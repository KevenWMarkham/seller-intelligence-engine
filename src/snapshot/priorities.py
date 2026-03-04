"""Layer 1 — Business priority extractor.

Sources: earnings call transcripts, annual reports, executive LinkedIn posts, hiring patterns.
"""

import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CompanyPriority(BaseModel):
    priority: str
    source: str  # e.g. "Q3 2025 Earnings Call", "CEO LinkedIn", "10-K 2024"
    alignment: str  # HIGH | MEDIUM | LOW
    platform_products: list[str] = []
    talking_points: list[str] = []


async def extract_priorities(
    company_name: str,
    domain: str,
    ticker: str | None,
    platform_vendor: str,
    platform_products: list[str],
) -> list[CompanyPriority]:
    """
    Extract top business priorities for a company and map them to platform capabilities.

    Sources (in order of signal strength):
    1. Earnings call transcripts (CEO/CFO commentary on strategic priorities)
    2. Annual report strategic priorities section
    3. Executive LinkedIn posts and conference talks
    4. Hiring patterns (active job postings by function)

    Args:
        company_name: Target company name.
        domain: Company domain.
        ticker: Stock ticker (required for earnings transcript access).
        platform_vendor: Seller's platform vendor.
        platform_products: Product list from vendor YAML config.

    Returns:
        List of CompanyPriority ranked by alignment strength.
    """
    # TODO: Phase 7 — SEC EDGAR transcript parsing + Qwen extraction
    logger.info("Extracting priorities for %s", company_name)
    return []
