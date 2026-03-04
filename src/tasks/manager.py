"""Layer 6 — Task lifecycle manager.

Task states: created → prepped → coached → ready → in_progress → completed | snoozed | escalated
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.task import SellerTask

logger = logging.getLogger(__name__)

VALID_TRANSITIONS: dict[str, list[str]] = {
    "created": ["prepped"],
    "prepped": ["coached", "ready"],
    "coached": ["ready"],
    "ready": ["in_progress"],
    "in_progress": ["completed", "snoozed", "escalated"],
    "snoozed": ["in_progress", "created"],
    "escalated": ["in_progress"],
    "completed": [],
}


async def transition_task(
    session: AsyncSession,
    task_id: int,
    new_status: str,
    notes: str | None = None,
) -> SellerTask:
    """
    Transition a task to a new status, validating the transition is allowed.

    Args:
        session: Async DB session.
        task_id: Task ID.
        new_status: Target status.
        notes: Optional notes to attach to the transition.

    Returns:
        Updated SellerTask.

    Raises:
        ValueError: If the transition is not allowed from the current status.
    """
    task = await session.get(SellerTask, task_id)
    if task is None:
        raise ValueError(f"Task {task_id} not found")

    allowed = VALID_TRANSITIONS.get(task.status, [])
    if new_status not in allowed:
        raise ValueError(f"Cannot transition task from '{task.status}' to '{new_status}'")

    task.status = new_status
    if notes:
        task.notes = (task.notes or "") + f"\n{notes}"
    return task


async def get_tasks_for_seller(
    session: AsyncSession,
    seller_id: str,
    status: str | None = None,
    min_priority: int = 0,
) -> list[SellerTask]:
    """
    Retrieve tasks for a seller, optionally filtered by status and minimum priority.

    Args:
        session: Async DB session.
        seller_id: Seller identifier.
        status: Optional status filter.
        min_priority: Minimum priority score (0 = no filter).

    Returns:
        List of SellerTask sorted by priority_score descending.
    """
    from sqlalchemy import select

    query = select(SellerTask).where(SellerTask.seller_id == seller_id)
    if status:
        query = query.where(SellerTask.status == status)
    if min_priority > 0:
        query = query.where(SellerTask.priority_score >= min_priority)
    query = query.order_by(SellerTask.priority_score.desc())

    result = await session.execute(query)
    return list(result.scalars().all())
