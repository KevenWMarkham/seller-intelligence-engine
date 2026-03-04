"""Layer 1.5 — Platform affinity scorer.

Scores how deeply each ISV is integrated with each platform vendor.
"""

import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PlatformAffinity(BaseModel):
    vendor: str
    co_sell_status: str | None = None  # co_sell_ready | ip_co_sell | listing_only | none
    integration_depth: str | None = None  # transactable | listing | api_integration | none
    cert_level: str | None = None  # advanced | standard | none
    joint_case_studies: int = 0
    affinity_score: float = 0.0  # 0.0 – 1.0


async def score_affinity(
    isv_name: str,
    marketplace: str,
    platform_vendor: str,
    listing_metadata: dict,
) -> PlatformAffinity:
    """
    Score an ISV's integration depth with a platform vendor.

    Factors: co-sell status, marketplace listing type, joint case studies,
    certification level, integration points.

    Args:
        isv_name: ISV solution name.
        marketplace: Source marketplace.
        platform_vendor: Target platform vendor.
        listing_metadata: Raw metadata from marketplace scrape.

    Returns:
        PlatformAffinity with composite affinity score.
    """
    # TODO: Phase 9 — parse listing metadata, cross-reference co-sell databases
    logger.info("Scoring affinity for ISV=%s vendor=%s", isv_name, platform_vendor)
    return PlatformAffinity(vendor=platform_vendor)
