from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    ticker: Mapped[str | None] = mapped_column(String(20))
    industry: Mapped[str | None] = mapped_column(String(100))
    sub_industry: Mapped[str | None] = mapped_column(String(100))
    revenue: Mapped[str | None] = mapped_column(String(50))
    headcount: Mapped[int | None] = mapped_column(Integer)
    hq_location: Mapped[str | None] = mapped_column(String(255))
    founded: Mapped[int | None] = mapped_column(Integer)
    stage: Mapped[str | None] = mapped_column(String(50))  # Public, Series C, Private
    business_model: Mapped[str | None] = mapped_column(String(100))  # B2B SaaS, Marketplace
    description: Mapped[str | None] = mapped_column(Text)

    # Tech / platform data (JSON stored as text — use JSON column for Postgres)
    tech_stack_json: Mapped[str | None] = mapped_column(Text)
    platform_adoption_json: Mapped[str | None] = mapped_column(Text)
    priorities_json: Mapped[str | None] = mapped_column(Text)
    competitive_json: Mapped[str | None] = mapped_column(Text)
    sales_motion: Mapped[str | None] = mapped_column(String(20))  # wedge, new, expand, displace

    # Metadata
    snapshot_refreshed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
