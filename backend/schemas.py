"""
schemas.py
----------
Pydantic models for SmartScrape.

All request and response structures are defined here.
FastAPI uses these schemas for automatic validation and OpenAPI documentation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, HttpUrl, field_validator


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ExtractionOptions(BaseModel):
    """Which parts of the page the caller wants to extract."""

    page_info: bool = True
    headings: bool = False
    text: bool = False
    links: bool = False
    images: bool = False
    tables: bool = False
    lists: bool = False


class ScrapeRequest(BaseModel):
    """Incoming scrape request body."""

    url: str
    options: ExtractionOptions = ExtractionOptions()
    render_js: bool = False   # When True, use headless Chromium instead of requests

    @field_validator("url")
    @classmethod
    def url_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("URL must not be empty.")
        return v.strip()


# ---------------------------------------------------------------------------
# Extraction result schemas
# ---------------------------------------------------------------------------


class PageInfo(BaseModel):
    """Summary statistics about the scraped page."""

    title: str
    url: str
    status_code: int
    headings_count: int
    text_blocks_count: int
    links_count: int
    images_count: int
    tables_count: int
    lists_count: int


class Heading(BaseModel):
    tag: str   # e.g. "h1", "h2"
    text: str


class Link(BaseModel):
    text: str
    url: str


class Image(BaseModel):
    url: str
    alt: str


class TableData(BaseModel):
    headers: list[str]
    rows: list[list[str]]


class ListData(BaseModel):
    list_type: str   # "ordered" or "unordered"
    items: list[str]


class YoutubeData(BaseModel):
    """Structured metadata extracted from a YouTube video page."""

    video_id: str
    title: str
    author: str
    channel_id: str
    view_count: Optional[int] = None
    length_seconds: Optional[int] = None
    publish_date: Optional[str] = None
    category: Optional[str] = None
    is_live: bool = False
    keywords: list[str] = []
    description: str = ""
    thumbnail_url: Optional[str] = None
    video_url: str


# ---------------------------------------------------------------------------
# API response schema
# ---------------------------------------------------------------------------


class ScrapeResponse(BaseModel):
    """Full API response returned by POST /api/scrape."""

    success: bool
    url: str
    message: Optional[str] = None
    render_js_used: bool = False

    page_info: Optional[PageInfo] = None
    headings: Optional[list[Heading]] = None
    text: Optional[list[str]] = None
    links: Optional[list[Link]] = None
    images: Optional[list[Image]] = None
    tables: Optional[list[TableData]] = None
    lists: Optional[list[ListData]] = None
    youtube_data: Optional[YoutubeData] = None


# ---------------------------------------------------------------------------
# History schemas
# ---------------------------------------------------------------------------


class HistoryItem(BaseModel):
    """A single row from the scraping_jobs table."""

    id: int
    url: str
    timestamp: datetime
    status: str
    title: Optional[str] = None
    items_found: int

    class Config:
        from_attributes = True


class HistoryResponse(BaseModel):
    jobs: list[HistoryItem]
    total: int
