"""Layer 1.5 — ISV-company matcher.

Matches ISVs to target companies based on industry fit, capability gaps,
platform alignment, and sales motion.
"""

import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ISVMatch(BaseModel):
    isv_id: int
    isv_name: str
    fit_score: float  # 0.0 – 1.0
    motion_alignment: str  # wedge | new | expand | displace
    conversation_hook: str
    matched_priorities: list[str] = []
    matched_capabilities: list[str] = []


async def match_isvs_to_company(
    company_name: str,
    industry: str | None,
    company_priorities: list[str],
    tech_stack: list[str],
    platform_vendor: str,
    sales_motion: str,
    top_n: int = 5,
) -> list[ISVMatch]:
    """
    Match the top ISVs to a target company.

    Matching factors:
    - Industry fit (company vertical × ISV vertical)
    - Capability gap (company priorities vs current stack)
    - Platform alignment (ISV runs on seller's platform)
    - Sales motion fit (wedge → entry ISVs, expand → adjacent ISVs)

    Args:
        company_name: Target company name.
        industry: Company industry vertical.
        company_priorities: List of company business priorities.
        tech_stack: Detected technologies at the company.
        platform_vendor: Seller's platform vendor.
        sales_motion: wedge | new | expand | displace
        top_n: Number of top matches to return.

    Returns:
        List of ISVMatch ranked by fit_score descending.
    """
    # TODO: Phase 9 — query ISV DB, score matches, rank by fit
    logger.info("Matching ISVs for company=%s motion=%s", company_name, sales_motion)
    return []
