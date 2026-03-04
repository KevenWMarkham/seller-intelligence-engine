from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_session
from src.models.contact import Contact

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/{company_id}")
async def get_contacts(company_id: int, session: SessionDep):
    """Get contacts for a company, sorted by platform relevance score."""
    result = await session.execute(
        select(Contact)
        .where(Contact.company_id == company_id)
        .order_by(Contact.platform_relevance_score.desc())
    )
    contacts = result.scalars().all()
    return {"company_id": company_id, "contacts": [c.__dict__ for c in contacts]}
