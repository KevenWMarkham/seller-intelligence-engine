from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_session

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class RoleplayStartRequest(BaseModel):
    seller_id: str
    task_id: int


@router.get("/{seller_id}")
async def get_coaching_history(seller_id: str, session: SessionDep):
    """Get coaching history and scores for a seller."""
    from sqlalchemy import select
    from src.models.coaching import CoachingSession, RoleplayScorecard

    sessions_result = await session.execute(
        select(CoachingSession).where(CoachingSession.seller_id == seller_id).limit(20)
    )
    sessions = sessions_result.scalars().all()
    return {"seller_id": seller_id, "sessions": [s.__dict__ for s in sessions]}


@router.post("/roleplay/start")
async def start_roleplay(request: RoleplayStartRequest, session: SessionDep):
    """Start a new roleplay coaching session for a task."""
    from src.models.task import SellerTask
    task = await session.get(SellerTask, request.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # TODO: Phase 10 — create CoachingSession, generate prospect persona
    return {
        "session_id": None,
        "status": "started",
        "message": "Roleplay session creation coming in Phase 10",
    }
