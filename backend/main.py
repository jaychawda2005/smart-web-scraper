"""
main.py
-------
FastAPI application entry point for SmartScrape.

Endpoints:
  POST   /api/scrape          - Scrape a URL and return extracted data
  GET    /api/history         - Retrieve recent scraping jobs
  DELETE /api/history/{id}    - Delete a specific scraping job record
  GET    /api/export/json     - Export a scraping result as JSON
  GET    /api/export/csv      - Export a scraping result as CSV
  GET    /api/export/excel    - Export a scraping result as Excel (.xlsx)

Run with:
  uvicorn main:app --reload --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from typing import Any, Optional

import pandas as pd
import requests
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from sqlalchemy.orm import Session

import models
import scraper as scraper_engine
from database import Base, engine, get_db
from schemas import (
    ExtractionOptions,
    HistoryItem,
    HistoryResponse,
    ScrapeRequest,
    ScrapeResponse,
)
from security import validate_url

# ---------------------------------------------------------------------------
# Database initialisation — create tables if they don't exist
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="SmartScrape API",
    description=(
        "Universal Web Data Extraction & Analytics Platform. "
        "Extracts structured information from publicly accessible web pages."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — allow the Vite/React dev server (PART 2) and common local ports
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite default
        "http://localhost:3000",   # Create-React-App default
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory cache of the last scrape result (used for export endpoints)
# This is a simple approach suitable for a single-user dev environment.
# For production, results would be stored in the database or a cache layer.
# ---------------------------------------------------------------------------
_last_result_cache: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Helper: count total items found across all extraction types
# ---------------------------------------------------------------------------

def _count_items(result: dict[str, Any]) -> int:
    """Count total extracted items across all categories."""
    total = 0
    for key in ("headings", "text", "links", "images", "tables", "lists"):
        val = result.get(key)
        if isinstance(val, list):
            total += len(val)
    return total


# ---------------------------------------------------------------------------
# POST /api/scrape
# ---------------------------------------------------------------------------

@app.post(
    "/api/scrape",
    response_model=ScrapeResponse,
    summary="Scrape a webpage",
    description=(
        "Fetch a publicly accessible webpage and extract structured data. "
        "Use the 'options' field to choose what to extract."
    ),
)
def scrape_endpoint(
    body: ScrapeRequest,
    db: Session = Depends(get_db),
) -> ScrapeResponse:
    url = body.url

    # --- URL validation / SSRF protection ---
    is_valid, error_msg = validate_url(url)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # --- Fetch and scrape ---
    try:
        result = scraper_engine.scrape_url(url, body.options, render_js=body.render_js)
    except RuntimeError as exc:
        # RuntimeError is raised by _fetch_with_browser for browser-specific failures
        _save_job(db, url, "error", None, 0)
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )
    except requests.exceptions.SSLError:
        _save_job(db, url, "error", None, 0)
        raise HTTPException(
            status_code=502,
            detail="SSL certificate verification failed for the target site.",
        )
    except requests.exceptions.ConnectionError:
        _save_job(db, url, "error", None, 0)
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to the website. Please check the URL and try again.",
        )
    except requests.exceptions.Timeout:
        _save_job(db, url, "error", None, 0)
        raise HTTPException(
            status_code=504,
            detail="The website took too long to respond.",
        )
    except requests.exceptions.TooManyRedirects:
        _save_job(db, url, "error", None, 0)
        raise HTTPException(
            status_code=502,
            detail="Too many redirects. The URL may be in a redirect loop.",
        )
    except requests.exceptions.HTTPError as exc:
        _save_job(db, url, "error", None, 0)
        raise HTTPException(
            status_code=502,
            detail=f"The website returned an HTTP error: {exc}",
        )
    except requests.exceptions.RequestException as exc:
        _save_job(db, url, "error", None, 0)
        raise HTTPException(
            status_code=502,
            detail=f"An error occurred while fetching the page: {exc}",
        )
    except Exception as exc:
        _save_job(db, url, "error", None, 0)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while parsing the page: {exc}",
        )

    items_found = _count_items(result)
    title = result.get("title") or ""

    # --- Persist job metadata ---
    job = _save_job(db, url, "success", title, items_found)

    # --- Cache the result for export endpoints ---
    _last_result_cache.clear()
    _last_result_cache["job_id"] = job.id
    _last_result_cache["url"] = url
    _last_result_cache["result"] = result

    # --- Build response ---
    return ScrapeResponse(
        success=True,
        url=url,
        page_info=result.get("page_info"),
        headings=result.get("headings"),
        text=result.get("text"),
        links=result.get("links"),
        images=result.get("images"),
        tables=result.get("tables"),
        lists=result.get("lists"),
        youtube_data=result.get("youtube_data"),
        render_js_used=result.get("render_js_used", False),
    )


# ---------------------------------------------------------------------------
# GET /api/history
# ---------------------------------------------------------------------------

@app.get(
    "/api/history",
    response_model=HistoryResponse,
    summary="Get scraping history",
    description="Return the most recent scraping jobs (default: last 50).",
)
def get_history(
    limit: int = Query(default=50, ge=1, le=200, description="Max records to return"),
    db: Session = Depends(get_db),
) -> HistoryResponse:
    jobs = (
        db.query(models.ScrapingJob)
        .order_by(models.ScrapingJob.id.desc())
        .limit(limit)
        .all()
    )
    total = db.query(models.ScrapingJob).count()
    return HistoryResponse(
        jobs=[HistoryItem.model_validate(j) for j in jobs],
        total=total,
    )


# ---------------------------------------------------------------------------
# DELETE /api/history/{id}
# ---------------------------------------------------------------------------

@app.delete(
    "/api/history/{job_id}",
    summary="Delete a history record",
    description="Remove a single scraping job record by its ID.",
)
def delete_history_item(
    job_id: int,
    db: Session = Depends(get_db),
) -> dict:
    job = db.query(models.ScrapingJob).filter(models.ScrapingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")
    db.delete(job)
    db.commit()
    return {"success": True, "message": f"Job {job_id} deleted."}


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

def _get_cached_result() -> dict[str, Any]:
    """Return the cached scrape result, raising 404 if nothing is cached."""
    if not _last_result_cache:
        raise HTTPException(
            status_code=404,
            detail=(
                "No scrape result available for export. "
                "Please call POST /api/scrape first."
            ),
        )
    return _last_result_cache


def _flatten_result(result: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Flatten the nested scrape result into a list of dicts suitable
    for CSV / Excel export.
    """
    rows: list[dict[str, Any]] = []

    if result.get("page_info"):
        pi = result["page_info"]
        rows.append({
            "category": "page_info",
            "field": "title",
            "value": pi.title,
        })
        rows.append({"category": "page_info", "field": "url", "value": pi.url})
        rows.append({"category": "page_info", "field": "status_code", "value": pi.status_code})
        rows.append({"category": "page_info", "field": "headings_count", "value": pi.headings_count})
        rows.append({"category": "page_info", "field": "text_blocks_count", "value": pi.text_blocks_count})
        rows.append({"category": "page_info", "field": "links_count", "value": pi.links_count})
        rows.append({"category": "page_info", "field": "images_count", "value": pi.images_count})
        rows.append({"category": "page_info", "field": "tables_count", "value": pi.tables_count})
        rows.append({"category": "page_info", "field": "lists_count", "value": pi.lists_count})

    if result.get("headings"):
        for h in result["headings"]:
            rows.append({"category": "heading", "field": h.tag, "value": h.text})

    if result.get("text"):
        for i, t in enumerate(result["text"]):
            rows.append({"category": "text", "field": f"block_{i+1}", "value": t})

    if result.get("links"):
        for lnk in result["links"]:
            rows.append({"category": "link", "field": lnk.text, "value": lnk.url})

    if result.get("images"):
        for img in result["images"]:
            rows.append({"category": "image", "field": img.alt or "[no alt]", "value": img.url})

    if result.get("tables"):
        for t_idx, tbl in enumerate(result["tables"]):
            rows.append({
                "category": "table",
                "field": f"table_{t_idx+1}_headers",
                "value": " | ".join(tbl.headers),
            })
            for r_idx, row in enumerate(tbl.rows):
                rows.append({
                    "category": "table",
                    "field": f"table_{t_idx+1}_row_{r_idx+1}",
                    "value": " | ".join(row),
                })

    if result.get("lists"):
        for l_idx, lst in enumerate(result["lists"]):
            for item in lst.items:
                rows.append({
                    "category": f"list_{lst.list_type}",
                    "field": f"list_{l_idx+1}",
                    "value": item,
                })

    return rows


# ---------------------------------------------------------------------------
# GET /api/export/json
# ---------------------------------------------------------------------------

@app.get(
    "/api/export/json",
    summary="Export last scrape result as JSON",
    description="Download the most recently scraped data as a JSON file.",
)
def export_json() -> Response:
    cache = _get_cached_result()
    result = cache["result"]
    url = cache["url"]

    # Serialise using Pydantic models where available
    export_data: dict[str, Any] = {"url": url}

    if result.get("page_info"):
        export_data["page_info"] = result["page_info"].model_dump()
    if result.get("youtube_data"):
        export_data["youtube_data"] = result["youtube_data"].model_dump()
    if result.get("headings"):
        export_data["headings"] = [h.model_dump() for h in result["headings"]]
    if result.get("text"):
        export_data["text"] = result["text"]
    if result.get("links"):
        export_data["links"] = [lnk.model_dump() for lnk in result["links"]]
    if result.get("images"):
        export_data["images"] = [img.model_dump() for img in result["images"]]
    if result.get("tables"):
        export_data["tables"] = [t.model_dump() for t in result["tables"]]
    if result.get("lists"):
        export_data["lists"] = [lst.model_dump() for lst in result["lists"]]

    json_bytes = json.dumps(export_data, indent=2, ensure_ascii=False).encode("utf-8")
    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="smartscrape_export.json"'},
    )


# ---------------------------------------------------------------------------
# GET /api/export/csv
# ---------------------------------------------------------------------------

@app.get(
    "/api/export/csv",
    summary="Export last scrape result as CSV",
    description="Download the most recently scraped data as a CSV file.",
)
def export_csv() -> StreamingResponse:
    cache = _get_cached_result()
    rows = _flatten_result(cache["result"])

    df = pd.DataFrame(rows, columns=["category", "field", "value"])
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="smartscrape_export.csv"'},
    )


# ---------------------------------------------------------------------------
# GET /api/export/excel
# ---------------------------------------------------------------------------

@app.get(
    "/api/export/excel",
    summary="Export last scrape result as Excel",
    description="Download the most recently scraped data as an Excel (.xlsx) file.",
)
def export_excel() -> StreamingResponse:
    cache = _get_cached_result()
    rows = _flatten_result(cache["result"])

    df = pd.DataFrame(rows, columns=["category", "field", "value"])
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="SmartScrape")
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.read()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="smartscrape_export.xlsx"'},
    )


# ---------------------------------------------------------------------------
# Root health check
# ---------------------------------------------------------------------------

@app.get("/", summary="Health check")
def root() -> dict:
    return {
        "status": "ok",
        "service": "SmartScrape API",
        "version": "1.0.0",
        "docs": "/docs",
    }


# ---------------------------------------------------------------------------
# Internal helper: persist job record
# ---------------------------------------------------------------------------

def _save_job(
    db: Session,
    url: str,
    status: str,
    title: Optional[str],
    items_found: int,
) -> models.ScrapingJob:
    """Create and persist a ScrapingJob record. Returns the saved job."""
    job = models.ScrapingJob(
        url=url,
        timestamp=datetime.now(tz=timezone.utc),
        status=status,
        title=title,
        items_found=items_found,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job
