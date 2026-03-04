from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base


class ISVSolution(Base):
    __tablename__ = "isv_solutions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor: Mapped[str] = mapped_column(String(255))
    marketplace: Mapped[str] = mapped_column(String(50))  # aws, azure, gcp, salesforce, servicenow
    description: Mapped[str | None] = mapped_column(Text)
    industries_json: Mapped[str | None] = mapped_column(Text)
    capabilities_json: Mapped[str | None] = mapped_column(Text)
    business_outcomes_json: Mapped[str | None] = mapped_column(Text)
    pricing_model: Mapped[str | None] = mapped_column(String(50))

    # Affinity scores
    platform_vendor: Mapped[str | None] = mapped_column(String(50))
    co_sell_status: Mapped[str | None] = mapped_column(String(50))
    integration_depth: Mapped[str | None] = mapped_column(String(50))  # transactable, listing
    cert_level: Mapped[str | None] = mapped_column(String(50))
    affinity_score: Mapped[float | None] = mapped_column(Float)

    scraped_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
