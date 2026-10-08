import io

from bs4 import BeautifulSoup

import scraper
from schemas import ExtractionOptions, YoutubeData


def test_extract_text_excludes_script_and_deduplicates():
    html = """
    <html><head><script>var x = 1;</script></head>
    <body>
      <p>Hello world</p>
      <div>Hello world</div>
      <style>.x{}</style>
      <span>Visible text</span>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    blocks = scraper._extract_text(soup)

    assert "Hello world" in blocks
    assert "Visible text" in blocks
    assert all("var x = 1;" not in block for block in blocks)
    assert blocks.count("Hello world") == 1


def test_extract_links_images_lists():
    html = """
    <html><body>
      <a href="/a">A</a>
      <a href="#fragment">Skip</a>
      <a href="javascript:void(0)">Skip JS</a>
      <img src="/img.png" alt="image" />
      <ul><li>One</li><li>Two</li></ul>
      <ol><li>First</li></ol>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")

    links = scraper._extract_links(soup, "https://example.com/base")
    images = scraper._extract_images(soup, "https://example.com/base")
    lists = scraper._extract_lists(soup)

    assert len(links) == 1
    assert links[0].url == "https://example.com/a"
    assert len(images) == 1
    assert images[0].url == "https://example.com/img.png"
    assert [lst.list_type for lst in lists] == ["unordered", "ordered"]


def test_parse_single_table_manual_fallback(monkeypatch):
    monkeypatch.setattr(scraper.pd, "read_html", lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("bad")))
    table = BeautifulSoup(
        """
        <table>
          <thead><tr><th>H1</th><th>H2</th></tr></thead>
          <tbody><tr><td>r1c1</td><td>r1c2</td></tr></tbody>
        </table>
        """,
        "lxml",
    ).find("table")

    parsed = scraper._parse_single_table(table)
    assert parsed.headers == ["H1", "H2"]
    assert parsed.rows == [["r1c1", "r1c2"]]


def test_fetch_page_uses_utf8_fallback(monkeypatch):
    class FakeResponse:
        status_code = 200
        encoding = "x-invalid"

        def iter_content(self, chunk_size=8192):
            yield "Résumé".encode("utf-8")

    monkeypatch.setattr(scraper.requests, "get", lambda *args, **kwargs: FakeResponse())
    response, text = scraper._fetch_page("https://example.com")

    assert response.status_code == 200
    assert "Résumé" in text


def test_scrape_url_fast_path(monkeypatch):
    html = "<html><head><title>T</title></head><body><h1>H</h1><p>P</p></body></html>"

    class FakeResponse:
        status_code = 201

    monkeypatch.setattr(scraper, "_fetch_page", lambda url: (FakeResponse(), html))

    result = scraper.scrape_url("https://example.com", ExtractionOptions(page_info=True, headings=True, text=True))
    assert result["status_code"] == 201
    assert result["title"] == "T"
    assert result["page_info"].headings_count == 1
    assert result["headings"][0].text == "H"
    assert result["render_js_used"] is False


def test_scrape_url_browser_path(monkeypatch):
    html = "<html><head><title>Browser</title></head><body><a href='/x'>x</a></body></html>"
    monkeypatch.setattr(scraper, "_fetch_with_browser", lambda url: (202, html))

    result = scraper.scrape_url("https://example.com", ExtractionOptions(page_info=True, links=True), render_js=True)
    assert result["status_code"] == 202
    assert result["title"] == "Browser"
    assert result["links"][0].url == "https://example.com/x"
    assert result["render_js_used"] is True


def test_scrape_url_youtube_fast_path(monkeypatch):
    yt_data = YoutubeData(
        video_id="abc123",
        title="Video",
        author="Author",
        channel_id="channel",
        view_count=10,
        length_seconds=5,
        publish_date="2024-01-01",
        category="Education",
        is_live=False,
        keywords=["k1", "k2"],
        description="desc",
        thumbnail_url="https://img.example/thumb.jpg",
        video_url="https://www.youtube.com/watch?v=abc123",
    )
    monkeypatch.setattr(scraper, "_scrape_youtube", lambda url: (200, yt_data))

    result = scraper.scrape_url(
        "https://www.youtube.com/watch?v=abc123",
        ExtractionOptions(page_info=True, text=True),
        render_js=False,
    )

    assert result["youtube_data"].video_id == "abc123"
    assert result["title"] == "Video"
    assert result["page_info"].images_count == 1
    assert result["render_js_used"] is False


def test_extract_json_blob_invalid_returns_none():
    assert scraper._extract_json_blob("<html></html>", "ytInitialPlayerResponse") is None
