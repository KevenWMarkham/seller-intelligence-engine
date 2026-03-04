"""Layer 1.5 — Platform affinity scorer.

Scores how deeply each ISV is integrated with a platform vendor using
rule-based scoring from marketplace listing metadata.

Affinity score components:
  co_sell_status  → 0.4 weight (co_sell_ready=1.0, ip_co_sell=0.75, listing_only=0.25, none=0.0)
  integration_depth → 0.35 weight (transactable=1.0, api_integration=0.65, listing=0.3, none=0.0)
  cert_level      → 0.25 weight (advanced=1.0, standard=0.5, none=0.0)
"""

import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Score tables for each dimension
_CO_SELL_SCORES: dict[str, float] = {
    "co_sell_ready": 1.0,
    "ip_co_sell": 0.75,
    "listing_only": 0.25,
    "none": 0.0,
}

_INTEGRATION_SCORES: dict[str, float] = {
    "transactable": 1.0,
    "api_integration": 0.65,
    "listing": 0.3,
    "none": 0.0,
}

_CERT_SCORES: dict[str, float] = {
    "advanced": 1.0,
    "standard": 0.5,
    "none": 0.0,
}

# Weights must sum to 1.0
_CO_SELL_WEIGHT = 0.40
_INTEGRATION_WEIGHT = 0.35
_CERT_WEIGHT = 0.25


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
    """Score an ISV's integration depth with a platform vendor.

    Computes a weighted composite score from co-sell status, listing depth,
    and certification level. Does not require Qwen — fully deterministic.

    Args:
        isv_name: ISV solution name.
        marketplace: Source marketplace (aws | azure | gcp | salesforce).
        platform_vendor: Target platform vendor key.
        listing_metadata: Dict with co_sell_status, integration_depth, cert_level.

    Returns:
        PlatformAffinity with composite affinity_score.
    """
    co_sell = listing_metadata.get("co_sell_status") or "none"
    integration = listing_metadata.get("integration_depth") or "none"
    cert = listing_metadata.get("cert_level") or "none"

    co_sell_score = _CO_SELL_SCORES.get(co_sell, 0.0)
    integration_score = _INTEGRATION_SCORES.get(integration, 0.0)
    cert_score = _CERT_SCORES.get(cert, 0.0)

    affinity = (
        co_sell_score * _CO_SELL_WEIGHT
        + integration_score * _INTEGRATION_WEIGHT
        + cert_score * _CERT_WEIGHT
    )

    logger.debug(
        "Affinity for ISV=%s vendor=%s: co_sell=%.2f integration=%.2f cert=%.2f → %.3f",
        isv_name,
        platform_vendor,
        co_sell_score,
        integration_score,
        cert_score,
        affinity,
    )

    return PlatformAffinity(
        vendor=platform_vendor,
        co_sell_status=co_sell if co_sell != "none" else None,
        integration_depth=integration if integration != "none" else None,
        cert_level=cert if cert != "none" else None,
        affinity_score=round(affinity, 3),
    )


def score_affinity_sync(
    co_sell_status: str | None,
    integration_depth: str | None,
    cert_level: str | None,
) -> float:
    """Synchronous affinity scoring from ISVSolution ORM fields.

    Used by matcher.py which already has the ORM data loaded and
    doesn't need an async call.

    Returns:
        Affinity score float 0.0–1.0.
    """
    co_sell = co_sell_status or "none"
    integration = integration_depth or "none"
    cert = cert_level or "none"

    return round(
        _CO_SELL_SCORES.get(co_sell, 0.0) * _CO_SELL_WEIGHT
        + _INTEGRATION_SCORES.get(integration, 0.0) * _INTEGRATION_WEIGHT
        + _CERT_SCORES.get(cert, 0.0) * _CERT_WEIGHT,
        3,
    )
