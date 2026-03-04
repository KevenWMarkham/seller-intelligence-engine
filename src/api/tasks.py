from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_session
from src.models.company import Company
from src.models.contact import Contact
from src.models.task import SellerTask
from src.tasks.manager import get_tasks_for_seller, transition_task

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class TaskStatusUpdate(BaseModel):
    status: str
    notes: str | None = None


def _task_to_dict(task: SellerTask, company: Company | None, contact: Contact | None) -> dict[str, Any]:
    """Serialize a task with embedded company + contact."""
    d = {c.key: getattr(task, c.key) for c in task.__mapper__.columns}
    d.pop("_sa_instance_state", None)
    if company:
        d["company"] = {
            "id": company.id,
            "name": company.name,
            "domain": company.domain,
            "industry": company.industry,
            "sales_motion": company.sales_motion,
            "revenue": company.revenue,
        }
    if contact:
        d["contact"] = {
            "id": contact.id,
            "name": contact.name,
            "title": contact.title,
            "functional_area": contact.functional_area,
            "role_type": contact.role_type,
            "linkedin_url": contact.linkedin_url,
            "recent_activity": contact.recent_activity,
            "platform_relevance_score": contact.platform_relevance_score,
        }
    return d


async def _enrich_tasks(session: AsyncSession, tasks: list[SellerTask]) -> list[dict[str, Any]]:
    """Load company and contact for each task and return enriched dicts."""
    if not tasks:
        return []

    company_ids = list({t.company_id for t in tasks if t.company_id})
    contact_ids = list({t.contact_id for t in tasks if t.contact_id})

    companies: dict[int, Company] = {}
    contacts: dict[int, Contact] = {}

    if company_ids:
        res = await session.execute(select(Company).where(Company.id.in_(company_ids)))
        companies = {c.id: c for c in res.scalars().all()}

    if contact_ids:
        res = await session.execute(select(Contact).where(Contact.id.in_(contact_ids)))
        contacts = {c.id: c for c in res.scalars().all()}

    return [
        _task_to_dict(t, companies.get(t.company_id), contacts.get(t.contact_id))
        for t in tasks
    ]


@router.get("")
async def list_tasks(
    session: SessionDep,
    seller_id: str,
    status: str | None = None,
    min_priority: int = 0,
):
    """List tasks for a seller with enriched company and contact data."""
    tasks = await get_tasks_for_seller(session, seller_id, status=status, min_priority=min_priority)
    enriched = await _enrich_tasks(session, tasks)
    return {"tasks": enriched, "count": len(enriched)}


@router.get("/{task_id}")
async def get_task(task_id: int, session: SessionDep):
    """Get a single task by ID with enriched company and contact data."""
    task = await session.get(SellerTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    enriched = await _enrich_tasks(session, [task])
    return enriched[0]


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
