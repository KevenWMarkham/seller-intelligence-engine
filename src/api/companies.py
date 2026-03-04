from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_session

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/{company_id}/snapshot")
async def get_company_snapshot(company_id: int, session: SessionDep):
    """Get the full company snapshot including tech stack, priorities, and competitive analysis."""
    from src.models.company import Company
    company = await session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company.__dict__


@router.get("/{company_id}/isvs")
async def get_company_isvs(company_id: int, session: SessionDep):
    """Get ISV recommendations matched to this company."""
    from src.models.company import Company
    company = await session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    # TODO: Phase 9 — query ISV matches from DB
    return {"company_id": company_id, "isvs": []}
