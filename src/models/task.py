from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base


class SellerTask(Base):
    __tablename__ = "seller_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seller_id: Mapped[str] = mapped_column(String(255), index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"))
    contact_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("contacts.id"))
    news_item_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("news_items.id"))

    platform_vendor: Mapped[str] = mapped_column(String(50))
    sales_motion: Mapped[str | None] = mapped_column(String(20))  # wedge, new, expand, displace

    # Brief (JSON)
    conversation_brief_json: Mapped[str | None] = mapped_column(Text)
    isv_recommendations_json: Mapped[str | None] = mapped_column(Text)

    priority_score: Mapped[int | None] = mapped_column(Integer)
    priority_reasoning: Mapped[str | None] = mapped_column(Text)

    # Coaching
    coaching_status: Mapped[str] = mapped_column(String(50), default="not_started")
    readiness_score: Mapped[float | None] = mapped_column(Float)

    # Lifecycle
    status: Mapped[str] = mapped_column(String(50), default="created", index=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
