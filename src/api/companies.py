"""Company snapshot API.

GET /api/companies/{id}/snapshot — full profile with tech stack, motion, competitive, priorities
GET /api/companies/{id}/isvs    — ISV recommendations (Phase 9)
"""

import json
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.config import PlatformContext, get_platform_context
from src.db.database import get_session
from src.models.company import Company
from src.snapshot.competitive import build_competitive_snapshot
from src.snapshot.motion_classifier import classify_motion
from src.snapshot.priorities import extract_priorities
from src.snapshot.technographics import (
    PlatformAdoption,
    Technology,
    TechProfile,
    profile_tech_stack,
)

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


def _reconstruct_tech_profile(company: Company) -> TechProfile | None:
    """Reconstruct a TechProfile from stored DB JSON for use in downstream services."""
    try:
        platform_adoption_data = json.loads(company.platform_adoption_json or "{}")
        tech_stack_data = json.loads(company.tech_stack_json or "[]")

        platform_adoption = {
            vendor: PlatformAdoption.model_validate(adoption)
            for vendor, adoption in platform_adoption_data.items()
        }
        stack = [Technology.model_validate(t) for t in tech_stack_data]

        return TechProfile(
            domain=company.domain,
            stack=stack,
            platform_adoption=platform_adoption,
        )
    except Exception as exc:
        logger.warning(
            "Failed to reconstruct TechProfile for %s: %s", company.domain, exc
        )
        return None


@router.get("/{company_id}/snapshot")
async def get_company_snapshot(
    company_id: int,
    session: SessionDep,
    platform: PlatformContext = Depends(get_platform_context),
):
    """Get the full company snapshot.

    On first call (or when data is stale), runs the full snapshot pipeline:
    technographics → motion classification → competitive analysis → priority extraction.
    Results are cached to the DB so subsequent calls are fast.
    """
    company = await session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    product_names = [p["name"] for p in platform.products]
    db_updated = False

    # ── Step 1: Ensure tech profile exists ───────────────────────────────────
    tech_profile: TechProfile | None = None

    if company.platform_adoption_json:
        tech_profile = _reconstruct_tech_profile(company)
    elif not company.tech_stack_json:
        try:
            tech_profile = await profile_tech_stack(company.domain)
            company.tech_stack_json = json.dumps(
                [t.model_dump() for t in tech_profile.stack]
            )
            company.platform_adoption_json = json.dumps(
                {v: a.model_dump() for v, a in tech_profile.platform_adoption.items()}
            )
            db_updated = True
        except Exception as exc:
            logger.warning("Live tech profiling failed for %s: %s", company.domain, exc)
    else:
        tech_profile = _reconstruct_tech_profile(company)

    # ── Step 2: Sales motion classification ──────────────────────────────────
    if not company.sales_motion and tech_profile is not None:
        try:
            motion = await classify_motion(
                company_name=company.name,
                platform_vendor=platform.vendor,
                tech_profile=tech_profile,
            )
            company.sales_motion = motion.type
            db_updated = True
            logger.info("Classified sales motion for %s: %s", company.name, motion.type)
        except Exception as exc:
            logger.warning(
                "Motion classification failed for %s: %s", company.name, exc
            )

    # ── Step 3: Competitive analysis ─────────────────────────────────────────
    if not company.competitive_json:
        try:
            comp_snapshot = await build_competitive_snapshot(
                company_name=company.name,
                domain=company.domain,
                industry=company.industry,
                platform_vendor=platform.vendor,
                tech_profile=tech_profile,
            )
            company.competitive_json = comp_snapshot.model_dump_json()
            db_updated = True
            logger.info(
                "Built competitive snapshot for %s (%d competitors)",
                company.name,
                len(comp_snapshot.competitors),
            )
        except Exception as exc:
            logger.warning(
                "Competitive analysis failed for %s: %s", company.name, exc
            )

    # ── Step 4: Business priority extraction ─────────────────────────────────
    if not company.priorities_json:
        try:
            priorities = await extract_priorities(
                company_name=company.name,
                domain=company.domain,
                ticker=company.ticker,
                platform_vendor=platform.vendor,
                platform_products=product_names,
                company_description=company.description,
            )
            company.priorities_json = json.dumps([p.model_dump() for p in priorities])
            db_updated = True
            logger.info(
                "Extracted %d priorities for %s", len(priorities), company.name
            )
        except Exception as exc:
            logger.warning(
                "Priority extraction failed for %s: %s", company.name, exc
            )

    # ── Persist any updates ───────────────────────────────────────────────────
    if db_updated:
        from datetime import datetime, timezone

        company.snapshot_refreshed_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(company)

    # Pass tech_profile only when the DB still lacks tech data (first-call fallback)
    live_profile = tech_profile if not company.tech_stack_json else None
    return _company_to_snapshot(company, live_profile)


@router.get("/{company_id}/isvs")
async def get_company_isvs(
    company_id: int,
    session: SessionDep,
    platform: PlatformContext = Depends(get_platform_context),
):
    """Get ISV recommendations matched to this company.

    On first call, seeds the ISV catalog from config/isvs/{vendor}.yaml
    if no ISVs exist in the DB yet. Then runs the multi-factor matcher
    and returns ranked ISVMatch results with business outcomes.
    """
    import json as _json

    from src.isv.matcher import match_isvs_to_company
    from src.isv.scraper import seed_isv_catalog
    from src.models.isv import ISVSolution
    from sqlalchemy import select, func

    company = await session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Auto-seed catalog if DB has no ISVs for this vendor
    count_result = await session.execute(
        select(func.count()).select_from(ISVSolution).where(
            ISVSolution.platform_vendor == platform.vendor
        )
    )
    isv_count = count_result.scalar_one()
    if isv_count == 0:
        logger.info(
            "No ISVs in DB for vendor=%s — seeding catalog", platform.vendor
        )
        await seed_isv_catalog(session, platform.vendor)
        await session.commit()

    # Extract company priorities for capability matching
    company_priorities: list[str] = []
    if company.priorities_json:
        try:
            parsed = _json.loads(company.priorities_json)
            if isinstance(parsed, list):
                company_priorities = [
                    p.get("priority", "") if isinstance(p, dict) else str(p)
                    for p in parsed
                ]
        except (json.JSONDecodeError, TypeError):
            pass

    tech_stack: list[str] = []
    if company.tech_stack_json:
        try:
            ts = _json.loads(company.tech_stack_json)
            tech_stack = [t.get("name", "") for t in ts if isinstance(t, dict)]
        except (json.JSONDecodeError, TypeError):
            pass

    matches = await match_isvs_to_company(
        company_name=company.name,
        industry=company.industry,
        company_priorities=company_priorities,
        tech_stack=tech_stack,
        platform_vendor=platform.vendor,
        sales_motion=company.sales_motion or "new",
        session=session,
        top_n=5,
    )

    return {
        "company_id": company_id,
        "company_name": company.name,
        "vendor": platform.vendor,
        "isvs": [m.model_dump() for m in matches],
    }
