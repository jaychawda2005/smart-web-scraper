"""
scraper.py
----------
Universal web scraping engine for SmartScrape.

This module fetches a publicly accessible webpage and extracts structured
information from its HTML using BeautifulSoup.

Two fetch paths are available:
  FAST PATH (default):
    Uses the `requests` library to fetch raw HTML directly.  Fast (0.5-2s),
    lightweight, no browser involved.  Works perfectly for normal static sites.
    Does NOT execute JavaScript.

  BROWSER PATH (render_js=True):
    Launches headless Chromium via Playwright, navigates to the page, waits
    for the JavaScript to finish rendering, then hands the fully-rendered HTML
    to the same BeautifulSoup extraction pipeline.  Slower (3-10s) but works
    on single-page apps and other JS-heavy sites.
    The same SSRF validation is re-applied before any navigation.

LIMITATIONS:
  - The fast path does NOT execute JavaScript.
  - Some sites block headless browsers with bot-detection (e.g. Cloudflare).
  - Authentication, CAPTCHA, and paywalls are NOT supported by either path.
  - Content limits are applied to avoid downloading excessively large pages.
"""

from __future__ import annotations

import io
from typing import Any
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

from schemas import (
    ExtractionOptions,
    Heading,
    Image,
    Link,
    ListData,
    PageInfo,
    TableData,
    YoutubeData,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REQUEST_TIMEOUT = 15          # seconds
MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5 MB

USER_AGENT = (
    "SmartScrape/1.0 (educational project; "
    "respects robots.txt; not for commercial use)"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Browser-like headers used for YouTube (plain UA gets bot-detection page)
YOUTUBE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Tags whose content should be excluded from text extraction
EXCLUDED_TEXT_TAGS = {"script", "style", "noscript", "head", "meta", "link"}


# ---------------------------------------------------------------------------
# YouTube detection & extraction
# ---------------------------------------------------------------------------

import json
import re

YOUTUBE_DOMAINS = {"youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"}


def _is_youtube_video(url: str) -> bool:
    """Return True if the URL is a YouTube watch/shorts/embed URL."""
    parsed = urlparse(url)
    if parsed.netloc not in YOUTUBE_DOMAINS:
        return False
    # Standard watch, shorts, and youtu.be share links
    if parsed.path.startswith(("/watch", "/shorts", "/embed")):
        return True
    if parsed.netloc == "youtu.be":
        return bool(parsed.path.strip("/"))
    return False


def _extract_json_blob(html: str, var_name: str) -> dict | None:
    """
    Extract a JavaScript variable assignment like::

        var ytInitialPlayerResponse = { ... };

    Using the stdlib JSON decoder to correctly handle nested braces.
    """
    marker = f"var {var_name} = "
    idx = html.find(marker)
    if idx == -1:
        return None
    start = html.index("{", idx)
    try:
        decoder = json.JSONDecoder()
        obj, _ = decoder.raw_decode(html[start:])
        return obj
    except (json.JSONDecodeError, ValueError):
        return None


def _get_video_id(url: str) -> str:
    """Extract the YouTube video ID from various URL formats."""
    parsed = urlparse(url)
    if parsed.netloc == "youtu.be":
        return parsed.path.strip("/")
    # /shorts/<id>  or  /embed/<id>
    for prefix in ("/shorts/", "/embed/"):
        if parsed.path.startswith(prefix):
            return parsed.path[len(prefix):].split("/")[0]
    # ?v=<id>
    from urllib.parse import parse_qs
    qs = parse_qs(parsed.query)
    return qs.get("v", [""])[0]


def _scrape_youtube(url: str) -> tuple[int, YoutubeData | None]:
    """
    Fetch a YouTube video page and extract structured metadata from the
    embedded ytInitialPlayerResponse JSON blob.

    Returns (status_code, YoutubeData | None).
    """
    response = requests.get(
        url,
        headers=YOUTUBE_HEADERS,
        timeout=REQUEST_TIMEOUT,
        allow_redirects=True,
        stream=True,
    )

    content_chunks: list[bytes] = []
    bytes_read = 0
    for chunk in response.iter_content(chunk_size=8192):
        content_chunks.append(chunk)
        bytes_read += len(chunk)
        if bytes_read > MAX_RESPONSE_BYTES:
            break
    html = b"".join(content_chunks).decode("utf-8", errors="replace")

    pr = _extract_json_blob(html, "ytInitialPlayerResponse")
    if not pr:
        return response.status_code, None

    vd = pr.get("videoDetails", {})
    mf = pr.get("microformat", {}).get("playerMicroformatRenderer", {})

    # Thumbnail — prefer highest resolution
    thumbs = vd.get("thumbnail", {}).get("thumbnails", [])
    thumbnail_url = thumbs[-1]["url"] if thumbs else None

    # View count may be a string ("1800684005")
    raw_views = vd.get("viewCount")
    try:
        view_count: int | None = int(raw_views) if raw_views else None
    except (ValueError, TypeError):
        view_count = None

    raw_length = vd.get("lengthSeconds")
    try:
        length_seconds: int | None = int(raw_length) if raw_length else None
    except (ValueError, TypeError):
        length_seconds = None

    video_id = vd.get("videoId") or _get_video_id(url)

    return response.status_code, YoutubeData(
        video_id=video_id,
        title=vd.get("title", ""),
        author=vd.get("author", ""),
        channel_id=vd.get("channelId", ""),
        view_count=view_count,
        length_seconds=length_seconds,
        publish_date=mf.get("publishDate") or mf.get("uploadDate"),
        category=mf.get("category"),
        is_live=bool(vd.get("isLiveContent", False)),
        keywords=vd.get("keywords", [])[:30],
        description=vd.get("shortDescription", ""),
        thumbnail_url=thumbnail_url,
        video_url=f"https://www.youtube.com/watch?v={video_id}",
    )


# ---------------------------------------------------------------------------
# HTTP fetching
# ---------------------------------------------------------------------------


def _fetch_page(url: str) -> tuple[requests.Response, str]:
    """
    Fetch a webpage and return the Response object plus its text content.

    Raises requests exceptions on failure — the caller handles them.
    """
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
        allow_redirects=True,
        stream=True,   # Use streaming to enforce size limit
    )

    # Read up to MAX_RESPONSE_BYTES
    content_chunks: list[bytes] = []
    bytes_read = 0
    for chunk in response.iter_content(chunk_size=8192):
        content_chunks.append(chunk)
        bytes_read += len(chunk)
        if bytes_read > MAX_RESPONSE_BYTES:
            break

    content_bytes = b"".join(content_chunks)

    # Detect encoding
    encoding = response.encoding or "utf-8"
    try:
        text = content_bytes.decode(encoding, errors="replace")
    except (LookupError, UnicodeDecodeError):
        text = content_bytes.decode("utf-8", errors="replace")

    return response, text


# ---------------------------------------------------------------------------
# Browser-based fetch (Playwright / headless Chromium)
# ---------------------------------------------------------------------------


def _fetch_with_browser(url: str) -> tuple[int, str]:
    """
    Fetch a webpage using a headless Chromium browser (Playwright).

    The browser navigates to the URL, waits for the network to be mostly idle
    and a short additional settle delay, then returns the fully-rendered HTML
    and the final HTTP status code.

    Security note: SSRF validation must be performed by the caller BEFORE
    calling this function — the browser will follow redirects blindly.

    Parameters
    ----------
    url : str
        A validated, publicly accessible URL.

    Returns
    -------
    tuple[int, str]
        (http_status_code, rendered_html)

    Raises
    ------
    RuntimeError
        On navigation timeout, browser crash, or any Playwright error.
        The message is user-friendly (no raw stack traces).
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    BROWSER_NAVIGATION_TIMEOUT_MS = 20_000   # 20 s for page load
    BROWSER_SETTLE_MS             =  2_000   # 2 s extra after networkidle
    MAX_BROWSER_CONTENT_BYTES     = 5 * 1024 * 1024  # 5 MB cap on HTML size

    browser = None
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-extensions",
                ],
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
                java_script_enabled=True,
                ignore_https_errors=True,
            )
            page = context.new_page()

            # Block binary resources to speed up rendering and reduce memory use
            def _block_heavy(route, request):
                if request.resource_type in ("image", "media", "font"):
                    route.abort()
                else:
                    route.continue_()

            page.route("**/*", _block_heavy)

            status_code = 200
            try:
                response = page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=BROWSER_NAVIGATION_TIMEOUT_MS,
                )
                if response:
                    status_code = response.status
            except PWTimeout:
                # Page may still have useful content — try to get what we have
                pass

            # Extra settle time for late-rendering JS
            page.wait_for_timeout(BROWSER_SETTLE_MS)

            html = page.content()  # Fully rendered HTML

            # Enforce size cap
            if len(html.encode("utf-8", errors="replace")) > MAX_BROWSER_CONTENT_BYTES:
                html = html[: MAX_BROWSER_CONTENT_BYTES * 4]  # rough char limit

            context.close()
            browser.close()
            browser = None

            return status_code, html

    except PWTimeout as exc:
        raise RuntimeError(
            "The page could not be rendered — it took too long to load. "
            "It may be too complex, behind a paywall, or using aggressive bot-detection."
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            "The headless browser encountered an error while loading the page. "
            "The site may be blocking automated access or the page is unavailable."
        ) from exc
    finally:
        # Guarantee no orphaned browser process leaks
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Individual extractors
# ---------------------------------------------------------------------------


def _extract_page_info(
    soup: BeautifulSoup,
    url: str,
    status_code: int,
) -> PageInfo:
    """Compute summary statistics about the page."""
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    return PageInfo(
        title=title,
        url=url,
        status_code=status_code,
        headings_count=len(soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])),
        text_blocks_count=len([
            p for p in soup.find_all("p") if p.get_text(strip=True)
        ]),
        links_count=len(soup.find_all("a", href=True)),
        images_count=len(soup.find_all("img")),
        tables_count=len(soup.find_all("table")),
        lists_count=len(soup.find_all(["ul", "ol"])),
    )


def _extract_headings(soup: BeautifulSoup) -> list[Heading]:
    """Extract all heading tags (h1–h6) with their text."""
    headings: list[Heading] = []
    for tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
        for tag in soup.find_all(tag_name):
            text = tag.get_text(strip=True)
            if text:
                headings.append(Heading(tag=tag_name, text=text))
    return headings


def _extract_text(soup: BeautifulSoup) -> list[str]:
    """
    Extract clean, visible text blocks from the page.

    Removes script, style, noscript, and other non-visible tags first,
    then collects text from block-level elements (p, div, li, td, etc.).
    Returns a deduplicated list of non-empty strings.
    """
    from bs4 import NavigableString

    # Work on a copy so we don't mutate the shared soup
    soup_copy = BeautifulSoup(str(soup), "lxml")

    # Remove unwanted tags entirely
    for tag in soup_copy.find_all(list(EXCLUDED_TEXT_TAGS)):
        tag.decompose()

    seen: set[str] = set()
    blocks: list[str] = []

    # Gather text from meaningful block-level / inline elements
    block_tags = [
        "p", "div", "span", "li", "td", "th", "caption",
        "blockquote", "pre", "code", "article", "section",
        "header", "footer", "main", "aside", "figcaption",
        "h1", "h2", "h3", "h4", "h5", "h6",
        "dt", "dd", "label", "strong", "em", "b", "i",
    ]

    for element in soup_copy.find_all(block_tags):
        # Get all direct NavigableString children only (avoid double-counting)
        for child in element.children:
            if not isinstance(child, NavigableString):
                continue
            text = str(child).strip()
            text = " ".join(text.split())
            if text and text not in seen:
                seen.add(text)
                blocks.append(text)

    # If no block-level text was found, fall back to all visible strings
    if not blocks:
        for string in soup_copy.strings:
            text = string.strip()
            text = " ".join(text.split())
            if text and text not in seen:
                seen.add(text)
                blocks.append(text)

    return blocks


def _extract_links(soup: BeautifulSoup, base_url: str) -> list[Link]:
    """Extract all anchor tags, resolving relative URLs to absolute."""
    links: list[Link] = []
    for tag in soup.find_all("a", href=True):
        href = tag.get("href", "").strip()
        if not href or href.startswith(("#", "javascript:")):
            continue
        absolute_url = urljoin(base_url, href)
        text = tag.get_text(strip=True) or "[no text]"
        links.append(Link(text=text, url=absolute_url))
    return links


def _extract_images(soup: BeautifulSoup, base_url: str) -> list[Image]:
    """Extract all img tags, resolving relative src URLs to absolute."""
    images: list[Image] = []
    for tag in soup.find_all("img"):
        src = tag.get("src", "").strip()
        if not src:
            continue
        absolute_src = urljoin(base_url, src)
        alt = tag.get("alt", "").strip()
        images.append(Image(url=absolute_src, alt=alt))
    return images


def _parse_single_table(table_tag: Tag) -> TableData:
    """
    Parse a single <table> element into headers and rows.

    Uses Pandas for robust handling of irregular tables.
    Falls back to manual parsing if Pandas fails.
    """
    try:
        # Pandas can read HTML tables directly from a string
        html_str = str(table_tag)
        df_list = pd.read_html(io.StringIO(html_str))
        if df_list:
            df = df_list[0]
            # Convert all values to strings, replace NaN with empty string
            df = df.fillna("").astype(str)
            headers = [str(col) for col in df.columns.tolist()]
            rows = df.values.tolist()
            return TableData(headers=headers, rows=rows)
    except Exception:
        pass  # Fall through to manual parsing

    # Manual fallback
    headers: list[str] = []
    rows: list[list[str]] = []

    thead = table_tag.find("thead")
    if thead:
        header_row = thead.find("tr")
        if header_row:
            headers = [
                th.get_text(strip=True)
                for th in header_row.find_all(["th", "td"])
            ]

    tbody = table_tag.find("tbody") or table_tag
    for tr in tbody.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if cells:
            rows.append(cells)

    return TableData(headers=headers, rows=rows)


def _extract_tables(soup: BeautifulSoup) -> list[TableData]:
    """Extract all tables from the page."""
    tables: list[TableData] = []
    for table_tag in soup.find_all("table"):
        try:
            tables.append(_parse_single_table(table_tag))
        except Exception:
            # Skip unparseable tables rather than crashing
            continue
    return tables


def _extract_lists(soup: BeautifulSoup) -> list[ListData]:
    """Extract ordered (ol) and unordered (ul) lists."""
    result: list[ListData] = []
    for list_tag in soup.find_all(["ul", "ol"]):
        list_type = "ordered" if list_tag.name == "ol" else "unordered"
        items = [
            li.get_text(strip=True)
            for li in list_tag.find_all("li", recursive=False)
            if li.get_text(strip=True)
        ]
        if items:
            result.append(ListData(list_type=list_type, items=items))
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def scrape_url(
    url: str,
    options: ExtractionOptions,
    render_js: bool = False,
) -> dict[str, Any]:
    """
    Fetch a public webpage and extract structured data based on the options.

    Parameters
    ----------
    url : str
        The validated, publicly accessible URL to scrape.
    options : ExtractionOptions
        Which parts of the page to extract.
    render_js : bool, optional
        When True, use headless Chromium (Playwright) to fetch the page so that
        JavaScript-rendered content is included.  Default is False (fast path).

    Returns
    -------
    dict with keys: status_code, title, page_info, headings, text,
                    links, images, tables, lists, youtube_data, render_js_used

    Raises
    ------
    RuntimeError
        When render_js=True and the browser fails to load the page.
    requests.exceptions.*
        When render_js=False and the requests fetch fails.
    """
    is_yt = _is_youtube_video(url)

    result: dict[str, Any] = {
        "status_code": 200,
        "title": None,
        "page_info": None,
        "headings": None,
        "text": None,
        "links": None,
        "images": None,
        "tables": None,
        "lists": None,
        "youtube_data": None,
        "render_js_used": render_js,
    }

    # ── YouTube fast path (never uses browser — has its own JSON extractor) ──
    if is_yt and not render_js:
        status_code, yt_data = _scrape_youtube(url)
        result["status_code"] = status_code
        result["youtube_data"] = yt_data

        if yt_data:
            result["title"] = yt_data.title
            if options.page_info:
                result["page_info"] = PageInfo(
                    title=yt_data.title,
                    url=url,
                    status_code=status_code,
                    headings_count=0,
                    text_blocks_count=1 if yt_data.description else 0,
                    links_count=0,
                    images_count=1 if yt_data.thumbnail_url else 0,
                    tables_count=0,
                    lists_count=len(yt_data.keywords),
                )
        return result

    # ── Choose fetch method ───────────────────────────────────────────────────
    if render_js:
        # Browser path — _fetch_with_browser raises RuntimeError on failure
        status_code, html_text = _fetch_with_browser(url)
    else:
        # Fast path — returns (Response, str)
        response, html_text = _fetch_page(url)
        status_code = response.status_code

    # ── Parse with BeautifulSoup (same pipeline for both paths) ──────────────
    soup = BeautifulSoup(html_text, "lxml")

    result["status_code"] = status_code

    # Always determine the title (needed for history storage)
    title_tag = soup.find("title")
    result["title"] = title_tag.get_text(strip=True) if title_tag else ""

    if options.page_info:
        result["page_info"] = _extract_page_info(soup, url, status_code)

    if options.headings:
        result["headings"] = _extract_headings(soup)

    if options.text:
        result["text"] = _extract_text(soup)

    if options.links:
        result["links"] = _extract_links(soup, url)

    if options.images:
        result["images"] = _extract_images(soup, url)

    if options.tables:
        result["tables"] = _extract_tables(soup)

    if options.lists:
        result["lists"] = _extract_lists(soup)

    return result
