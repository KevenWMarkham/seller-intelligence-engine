from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, WebSocket
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_session
from src.tasks.manager import get_tasks_for_seller, transition_task

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class TaskStatusUpdate(BaseModel):
    status: str
    notes: str | None = None


@router.get("")
async def list_tasks(
    session: SessionDep,
    seller_id: str,
    status: str | None = None,
    min_priority: int = 0,
):
    """List tasks for a seller, filtered by status and minimum priority."""
    tasks = await get_tasks_for_seller(session, seller_id, status=status, min_priority=min_priority)
    return {"tasks": [t.__dict__ for t in tasks], "count": len(tasks)}


@router.get("/{task_id}")
async def get_task(task_id: int, session: SessionDep):
    """Get a single task by ID."""
    from src.models.task import SellerTask
    task = await session.get(SellerTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.__dict__


@router.patch("/{task_id}/status")
async def update_task_status(task_id: int, update: TaskStatusUpdate, session: SessionDep):
    """Update task status (follows allowed lifecycle transitions)."""
    try:
        task = await transition_task(session, task_id, update.status, update.notes)
        return {"task_id": task.id, "status": task.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.websocket("/stream")
async def task_stream(websocket: WebSocket, seller_id: str):
    """WebSocket endpoint for real-time task updates."""
    await websocket.accept()
    # TODO: Phase 5 — broadcast task events to connected sellers
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        pass
