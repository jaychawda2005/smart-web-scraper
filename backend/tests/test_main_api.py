import io
from datetime import datetime, timezone

import requests
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main
import models
from database import Base
from schemas import Heading, Image, ListData, PageInfo, TableData


TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)
Base.metadata.create_all(bind=TEST_ENGINE)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


main.app.dependency_overrides[main.get_db] = _override_get_db
client = TestClient(main.app)


def _sample_result(url: str = "https://example.com"):
    return {
        "title": "Example Domain",
        "page_info": PageInfo(
            title="Example Domain",
            url=url,
            status_code=200,
            headings_count=1,
            text_blocks_count=1,
            links_count=1,
            images_count=1,
            tables_count=1,
            lists_count=1,
        ),
        "headings": [Heading(tag="h1", text="Example Domain")],
        "text": ["This domain is for use in illustrative examples."],
        "links": [],
        "images": [Image(url=f"{url}/image.png", alt="hero")],
        "tables": [TableData(headers=["A"], rows=[["B"]])],
        "lists": [ListData(list_type="unordered", items=["item-1"])],
        "youtube_data": None,
        "render_js_used": False,
    }


def _clear_db():
    db = TestingSessionLocal()
    try:
        db.query(models.ScrapingJob).delete()
        db.commit()
    finally:
        db.close()


def setup_function(_):
    _clear_db()
    main._last_result_cache.clear()


def test_root_health():
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "SmartScrape API"


def test_scrape_success_and_history(monkeypatch):
    monkeypatch.setattr(main, "validate_url", lambda url: (True, ""))
    monkeypatch.setattr(main.scraper_engine, "scrape_url", lambda url, options, render_js=False: _sample_result(url))

    response = client.post("/api/scrape", json={"url": "https://example.com"})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["page_info"]["title"] == "Example Domain"

    history = client.get("/api/history")
    assert history.status_code == 200
    history_body = history.json()
    assert history_body["total"] == 1
    assert history_body["jobs"][0]["status"] == "success"
    assert main._last_result_cache["url"] == "https://example.com"


def test_scrape_validation_failure_returns_400(monkeypatch):
    monkeypatch.setattr(main, "validate_url", lambda url: (False, "blocked"))

    response = client.post("/api/scrape", json={"url": "https://blocked.example"})
    assert response.status_code == 400
    assert response.json()["detail"] == "blocked"

    history = client.get("/api/history")
    assert history.json()["total"] == 0


def test_scrape_error_mappings(monkeypatch):
    cases = [
        (RuntimeError("browser failed"), 502),
        (requests.exceptions.ConnectionError(), 502),
        (requests.exceptions.Timeout(), 504),
        (requests.exceptions.TooManyRedirects(), 502),
        (requests.exceptions.RequestException("network"), 502),
        (Exception("parse"), 500),
    ]

    monkeypatch.setattr(main, "validate_url", lambda url: (True, ""))

    for exc, status_code in cases:
        def _raiser(url, options, render_js=False, e=exc):
            raise e

        monkeypatch.setattr(main.scraper_engine, "scrape_url", _raiser)
        response = client.post("/api/scrape", json={"url": "https://example.com"})
        assert response.status_code == status_code


def test_history_limit_validation_422():
    response = client.get("/api/history", params={"limit": 0})
    assert response.status_code == 422


def test_delete_history_success_and_not_found(monkeypatch):
    monkeypatch.setattr(main, "validate_url", lambda url: (True, ""))
    monkeypatch.setattr(main.scraper_engine, "scrape_url", lambda url, options, render_js=False: _sample_result(url))
    created = client.post("/api/scrape", json={"url": "https://example.com"})
    assert created.status_code == 200

    job_id = client.get("/api/history", params={"limit": 1}).json()["jobs"][0]["id"]
    deleted = client.delete(f"/api/history/{job_id}")
    assert deleted.status_code == 200
    assert deleted.json()["success"] is True

    missing = client.delete(f"/api/history/{job_id}")
    assert missing.status_code == 404


def test_export_endpoints_require_cache():
    assert client.get("/api/export/json").status_code == 404
    assert client.get("/api/export/csv").status_code == 404
    assert client.get("/api/export/excel").status_code == 404


def test_export_json_csv_excel_success():
    main._last_result_cache.update(
        {
            "job_id": 1,
            "url": "https://example.com",
            "result": _sample_result("https://example.com"),
        }
    )

    json_resp = client.get("/api/export/json")
    assert json_resp.status_code == 200
    assert json_resp.headers["content-type"].startswith("application/json")
    assert json_resp.json()["url"] == "https://example.com"

    csv_resp = client.get("/api/export/csv")
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert "category,field,value" in csv_resp.text

    excel_resp = client.get("/api/export/excel")
    assert excel_resp.status_code == 200
    assert excel_resp.content[:2] == b"PK"


def test_count_items_and_flatten_result_helpers():
    result = _sample_result()
    assert main._count_items(result) == 5

    rows = main._flatten_result(result)
    categories = {row["category"] for row in rows}
    assert "page_info" in categories
    assert "heading" in categories
    assert "list_unordered" in categories
