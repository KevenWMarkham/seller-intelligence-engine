"""Contacts API.

GET /api/contacts/{company_id} — FA-ranked contacts with org chart.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.config import PlatformContext, get_platform_context
from src.contacts.org_chart import build_org_chart
from src.contacts.resolver import resolve_contacts
from src.db.database import get_session
from src.models.company import Company

router = APIRouter()
logger = logging.getLogger(__name__)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/{company_id}")
async def get_contacts(
    company_id: int,
    session: SessionDep,
    platform: PlatformContext = Depends(get_platform_context),
):
    """Get FA-ranked contacts for a company with org chart inference."""
    company = await session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    resolved = await resolve_contacts(
        company_name=company.name,
        domain=company.domain,
        platform_vendor=platform.vendor,
        company_id=company_id,
        session=session,
    )

    org_chart = await build_org_chart(company.name, resolved)

    return {
        "company_id": company_id,
        "company_name": company.name,
        "vendor": platform.vendor,
        "contacts": [c.model_dump() for c in resolved],
        "org_chart": org_chart.model_dump(),
    }
