"""
models.py
---------
SQLAlchemy ORM models for SmartScrape.

Only metadata is stored — raw HTML is NOT persisted.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class ScrapingJob(Base):
    """
    Represents one scraping request.

    Stores metadata about the job (URL, status, title, item count).
    Raw HTML and extracted content are NOT stored to keep the database small.
    """

    __tablename__ = "scraping_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String, nullable=False)   # "success" | "error"
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    items_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
