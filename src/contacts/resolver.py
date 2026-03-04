"""Layer 3 — Platform-aware contact resolver.

Sources: LinkedIn Sales Nav / Proxycurl, Clearbit / Apollo.io, Hunter.io.
Cache: Refresh contacts older than 90 days.
Priority: Ranked by platform vendor context.
"""

import logging

from pydantic import BaseModel

from src.core.settings import settings

logger = logging.getLogger(__name__)

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


async def resolve_contacts(
    company_name: str,
    domain: str,
    platform_vendor: str,
    limit: int = 10,
) -> list[ResolvedContact]:
    """
    Resolve and prioritize functional-area contacts for a company.

    Waterfall: LinkedIn/Proxycurl → Clearbit/Apollo → Hunter.io.
    Contacts are ranked by platform_relevance_score based on vendor FA priorities.

    Args:
        company_name: Target company name.
        domain: Company domain.
        platform_vendor: Seller's platform vendor for FA prioritization.
        limit: Maximum contacts to return.

    Returns:
        List of ResolvedContact sorted by platform_relevance_score descending.
    """
    # TODO: Phase 8 — Proxycurl/LinkedIn integration with 90-day cache
    logger.info("Resolving contacts for %s (vendor=%s)", company_name, platform_vendor)
    return []


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
