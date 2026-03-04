"""Layer 3 — Platform-aware contact resolver.

Sources: LinkedIn Sales Nav / Proxycurl, Clearbit / Apollo.io, Hunter.io.
Cache: Refresh contacts older than 90 days.
Priority: Ranked by platform vendor context.
"""

import logging
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.settings import settings
from src.models.contact import Contact

logger = logging.getLogger(__name__)

CACHE_TTL = timedelta(days=90)

# Priority functional areas per vendor
VENDOR_FA_PRIORITY = {
    "google": ["Engineering", "Data & Analytics", "Security", "Product"],
    "microsoft": ["Engineering", "IT Operations", "Finance", "Product"],
    "aws": ["Engineering", "Infrastructure", "Data & Analytics", "Security"],
    "oracle": ["Finance", "Operations", "HR", "IT"],
    "salesforce": ["Sales", "Marketing", "Customer Success", "Revenue Operations"],
    "ibm": ["Engineering", "IT Operations", "Data & Analytics", "Security"],
}


class ResolvedContact(BaseModel):
    name: str
    title: str
    functional_area: str | None = None
    role_type: str | None = None  # decision_maker | influencer | champion
    linkedin_url: str | None = None
    email: str | None = None
    phone: str | None = None
    tenure_years: float | None = None
    recent_activity: str | None = None
    platform_relevance_score: float = 0.0
    source: str | None = None


def _apply_fa_boost(
    base_score: float,
    functional_area: str | None,
    fa_priority: list[str],
) -> float:
    """Apply a functional-area priority boost to a base relevance score.

    Args:
        base_score: The contact's stored platform_relevance_score (0.0–1.0).
        functional_area: The contact's functional area string.
        fa_priority: Ordered list of preferred FAs for the current vendor.

    Returns:
        Boosted score, capped at 1.0.
    """
    if not functional_area:
        return min(base_score, 1.0)

    try:
        position = fa_priority.index(functional_area)
    except ValueError:
        return min(base_score, 1.0)

    if position <= 1:
        boost = 0.1
    elif position <= 3:
        boost = 0.05
    else:
        boost = 0.0

    return min(base_score + boost, 1.0)


def _orm_to_resolved(contact: Contact, score: float) -> ResolvedContact:
    """Convert a Contact ORM row to a ResolvedContact Pydantic model."""
    return ResolvedContact(
        name=contact.name,
        title=contact.title or "",
        functional_area=contact.functional_area,
        role_type=contact.role_type,
        linkedin_url=contact.linkedin_url,
        email=contact.email,
        phone=contact.phone,
        tenure_years=contact.tenure_years,
        recent_activity=contact.recent_activity,
        platform_relevance_score=score,
        source="database",
    )


async def resolve_contacts(
    company_name: str,
    domain: str,
    platform_vendor: str,
    company_id: int,
    session: AsyncSession,
    limit: int = 10,
) -> list[ResolvedContact]:
    """
    Resolve and prioritize functional-area contacts for a company.

    Primary path: load from DB, apply FA priority boost, sort, and return.
    External APIs (Proxycurl, Clearbit) are stubbed — called only when keys
    are present; gracefully returns [] otherwise.

    Contacts with an enriched_at timestamp older than 90 days are flagged as
    stale via a warning log but are still returned from the DB.

    Args:
        company_name: Target company name.
        domain: Company domain.
        platform_vendor: Seller's platform vendor for FA prioritization.
        company_id: DB primary key of the target company.
        session: SQLAlchemy async session.
        limit: Maximum contacts to return.

    Returns:
        List of ResolvedContact sorted by platform_relevance_score descending.
    """
    logger.info(
        "Resolving contacts for %s (company_id=%d, vendor=%s)",
        company_name,
        company_id,
        platform_vendor,
    )

    # ------------------------------------------------------------------
    # 1. Load contacts from DB
    # ------------------------------------------------------------------
    result = await session.execute(
        select(Contact).where(Contact.company_id == company_id)
    )
    db_contacts: list[Contact] = list(result.scalars().all())

    if not db_contacts:
        logger.info(
            "No contacts found in DB for company_id=%d (%s); trying external APIs.",
            company_id,
            company_name,
        )
        # External API waterfall (stubs — require paid keys)
        external = await _fetch_proxycurl(domain)
        if not external:
            external = await _fetch_clearbit(domain)
        return external[:limit]

    # ------------------------------------------------------------------
    # 2. FA priority list for the current vendor
    # ------------------------------------------------------------------
    vendor_key = platform_vendor.lower()
    fa_priority: list[str] = VENDOR_FA_PRIORITY.get(vendor_key, [])

    # ------------------------------------------------------------------
    # 3. 90-day cache check + score each contact
    # ------------------------------------------------------------------
    now = datetime.now(tz=timezone.utc)
    resolved: list[ResolvedContact] = []

    for contact in db_contacts:
        # Cache freshness check
        if contact.enriched_at is not None:
            enriched_at = contact.enriched_at
            # Make timezone-aware if stored as naive UTC
            if enriched_at.tzinfo is None:
                enriched_at = enriched_at.replace(tzinfo=timezone.utc)

            if now - enriched_at > CACHE_TTL:
                logger.warning(
                    "Contact %d (%s) enrichment is stale (enriched_at=%s). "
                    "External refresh needed but APIs not implemented.",
                    contact.id,
                    contact.name,
                    contact.enriched_at.isoformat(),
                )
        else:
            logger.debug(
                "Contact %d (%s) has never been enriched.",
                contact.id,
                contact.name,
            )

        # Score: use stored value as base (default 0.0), then apply FA boost
        base_score = contact.platform_relevance_score or 0.0
        final_score = _apply_fa_boost(base_score, contact.functional_area, fa_priority)

        resolved.append(_orm_to_resolved(contact, final_score))

    # ------------------------------------------------------------------
    # 4. Sort by platform_relevance_score descending, return up to limit
    # ------------------------------------------------------------------
    resolved.sort(key=lambda c: c.platform_relevance_score, reverse=True)
    return resolved[:limit]


async def _fetch_proxycurl(domain: str) -> list[ResolvedContact]:
    """Pull contacts from Proxycurl LinkedIn scraping API."""
    if not settings.proxycurl_key:
        return []
    # TODO: Phase 8 — Proxycurl company people endpoint
    return []


async def _fetch_clearbit(domain: str) -> list[ResolvedContact]:
    """Pull company contacts from Clearbit."""
    if not settings.clearbit_key:
        return []
    # TODO: Phase 8 — Clearbit Reveal + Enrichment API
    return []
