from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base


class NewsItem(Base):
    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    headline: Mapped[str] = mapped_column(String(512))
    body: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(1024))
    published_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Classification (populated by Layer 4)
    companies_mentioned_json: Mapped[str | None] = mapped_column(Text)
    platform_relevance: Mapped[float | None] = mapped_column(Float)
    signal_type: Mapped[str | None] = mapped_column(String(50))
    urgency: Mapped[str | None] = mapped_column(String(20))  # high, medium, low
    relevance_score: Mapped[float | None] = mapped_column(Float)
    opportunity_type: Mapped[str | None] = mapped_column(String(50))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
