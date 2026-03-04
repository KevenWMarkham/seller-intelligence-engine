from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base


class CoachingSession(Base):
    __tablename__ = "coaching_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seller_id: Mapped[str] = mapped_column(String(255), index=True)
    task_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("seller_tasks.id"))
    mode: Mapped[str] = mapped_column(String(50))  # prep, roleplay, debrief, objection_drill
    messages_json: Mapped[str | None] = mapped_column(Text)
    feedback: Mapped[str | None] = mapped_column(Text)
    action_items_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)


class RoleplayScorecard(Base):
    __tablename__ = "roleplay_scorecards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("coaching_sessions.id"))
    seller_id: Mapped[str] = mapped_column(String(255), index=True)
    product_knowledge: Mapped[int | None] = mapped_column(Integer)
    contact_knowledge: Mapped[int | None] = mapped_column(Integer)
    objection_handling: Mapped[int | None] = mapped_column(Integer)
    conversation_flow: Mapped[int | None] = mapped_column(Integer)
    confidence: Mapped[int | None] = mapped_column(Integer)
    overall: Mapped[float | None] = mapped_column(Float)
    feedback: Mapped[str | None] = mapped_column(Text)
    areas_to_practice_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
