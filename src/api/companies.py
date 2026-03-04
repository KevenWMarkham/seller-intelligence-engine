"""Company snapshot API.

GET /api/companies/{id}/snapshot — full profile with tech stack
GET /api/companies/{id}/isvs    — ISV recommendations (Phase 9)
"""

import json
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_session
from src.models.company import Company
from src.snapshot.technographics import TechProfile, profile_tech_stack

router = APIRouter()
logger = logging.getLogger(__name__)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _company_to_snapshot(
    company: Company, tech_profile: TechProfile | None = None
) -> dict[str, Any]:
    """Build snapshot response dict from a Company row + optional live TechProfile."""
    snapshot: dict[str, Any] = {
        "id": company.id,
        "name": company.name,
        "domain": company.domain,
        "ticker": company.ticker,
        "industry": company.industry,
        "sub_industry": company.sub_industry,
        "revenue": company.revenue,
        "headcount": company.headcount,
        "hq_location": company.hq_location,
        "founded": company.founded,
        "stage": company.stage,
        "business_model": company.business_model,
        "description": company.description,
        "sales_motion": company.sales_motion,
        "snapshot_refreshed_at": (
            company.snapshot_refreshed_at.isoformat()
            if company.snapshot_refreshed_at
            else None
        ),
        "tech_stack": None,
        "platform_adoption": None,
        "priorities": None,
        "competitive": None,
    }

    # Deserialize JSON fields stored in DB
    for field, key in [
        ("tech_stack_json", "tech_stack"),
        ("platform_adoption_json", "platform_adoption"),
        ("priorities_json", "priorities"),
        ("competitive_json", "competitive"),
    ]:
        raw = getattr(company, field, None)
        if raw:
            try:
                snapshot[key] = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                pass

    # Overlay live tech profile if DB doesn't have one yet
    if tech_profile:
        if not snapshot["tech_stack"]:
            snapshot["tech_stack"] = [t.model_dump() for t in tech_profile.stack]
        if not snapshot["platform_adoption"]:
            snapshot["platform_adoption"] = {
                v: a.model_dump() for v, a in tech_profile.platform_adoption.items()
            }

    return snapshot


@router.get("/{company_id}/snapshot")
async def get_company_snapshot(company_id: int, session: SessionDep):
    """Get the full company snapshot including tech stack and platform adoption.

    Returns the cached DB snapshot. When no tech stack is present, runs a
    live technographic profile on-the-fly using website detection.
    """
    company = await session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    tech_profile: TechProfile | None = None
    if not company.tech_stack_json:
        try:
            tech_profile = await profile_tech_stack(company.domain)
        except Exception as exc:
            logger.warning("Live tech profiling failed for %s: %s", company.domain, exc)

    return _company_to_snapshot(company, tech_profile)


@router.get("/{company_id}/isvs")
async def get_company_isvs(company_id: int, session: SessionDep):
    """Get ISV recommendations matched to this company (Sprint 9)."""
    company = await session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"company_id": company_id, "isvs": []}
