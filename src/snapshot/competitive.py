"""Layer 1 — Competitive landscape analyzer.

Loads battle cards from config/competitive/ and cross-references a
TechProfile's platform_adoption signals to determine which competitors
are active at a target account.

Battle card resolution order:
  1. {platform_vendor}_vs_{competitor}.yaml  (seller is the vendor)
  2. {competitor}_vs_{platform_vendor}.yaml  (inverted — still useful signals)

Degrades gracefully — always returns a CompetitiveSnapshot even when
no config files match or the TechProfile is unavailable.
"""

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

logger = logging.getLogger(__name__)

_COMPETITIVE_DIR = Path(__file__).parent.parent.parent / "config" / "competitive"

# Map adoption depth -> threat level
_DEPTH_TO_THREAT: dict[str, str] = {
    "deep": "high",
    "moderate": "high",
    "light": "medium",
    "evaluating": "low",
    "none": "low",
}

# Human-readable position labels per vendor (best-effort)
_VENDOR_POSITIONS: dict[str, str] = {
    "aws": "Primary Cloud Vendor",
    "azure": "Primary Cloud Vendor",
    "microsoft": "Primary Cloud Vendor",
    "google": "Primary Cloud Vendor",
    "gcp": "Primary Cloud Vendor",
    "salesforce": "Primary CRM Vendor",
    "oracle": "Primary Database / ERP Vendor",
    "ibm": "Enterprise Platform Vendor",
    "servicenow": "Primary ITSM Vendor",
}


# ── Pydantic models ──────────────────────────────────────────────────────────


class Competitor(BaseModel):
    name: str
    position: str
    threat_level: str  # high | medium | low
    differentiation: str
    your_win_theme: str


class CompetitiveMove(BaseModel):
    type: str  # acquisition | product_launch | partnership | pricing_change
    description: str
    date: str | None = None
    impact: str | None = None


class CompetitiveSnapshot(BaseModel):
    company: str
    market_position: str | None = None  # Leader | Challenger | Niche | Visionary
    competitors: list[Competitor] = []
    strengths: list[str] = []
    vulnerabilities: list[str] = []
    recent_moves: list[CompetitiveMove] = []


# ── Main entry point ─────────────────────────────────────────────────────────


async def build_competitive_snapshot(
    company_name: str,
    domain: str,
    industry: str | None,
    platform_vendor: str,
    tech_profile: Any | None = None,  # TechProfile | None — avoid circular import
) -> CompetitiveSnapshot:
    """Build a competitive landscape for a company.

    Loads battle cards from config/competitive/ and cross-references
    detected platform adoption from the TechProfile to identify which
    competitors are active at the target account.

    Args:
        company_name: Target company name.
        domain: Company domain.
        industry: Industry classification.
        platform_vendor: Seller's platform vendor (e.g. "google", "microsoft").
        tech_profile: Optional TechProfile with platform_adoption signals.

    Returns:
        CompetitiveSnapshot populated from matched battle cards.
    """
    logger.info(
        "Building competitive snapshot for company=%s vendor=%s",
        company_name,
        platform_vendor,
    )

    vendor_key = _normalise_vendor(platform_vendor)
    active_competitors = _detect_competitors(tech_profile, vendor_key)

    if not active_competitors:
        logger.debug(
            "No competitor signals detected for company=%s; returning minimal snapshot",
            company_name,
        )
        return CompetitiveSnapshot(company=company_name)

    all_strengths: list[str] = []
    all_vulnerabilities: list[str] = []
    competitors: list[Competitor] = []

    for competitor_key, adoption_depth in active_competitors.items():
        battle_card = _load_battle_card(vendor_key, competitor_key)
        if battle_card is None:
            logger.debug(
                "No battle card found for vendor=%s vs competitor=%s",
                vendor_key,
                competitor_key,
            )
            continue

        competitor_obj = _build_competitor(competitor_key, adoption_depth, battle_card)
        competitors.append(competitor_obj)

        card_data = battle_card.get("competitive_battlecard", {})
        for strength in card_data.get("our_strengths_vs_them", []):
            if strength not in all_strengths:
                all_strengths.append(strength)

        for signal in battle_card.get("displacement_signals", []):
            if signal not in all_vulnerabilities:
                all_vulnerabilities.append(signal)

    if not competitors:
        return CompetitiveSnapshot(company=company_name)

    return CompetitiveSnapshot(
        company=company_name,
        competitors=competitors,
        strengths=all_strengths,
        vulnerabilities=all_vulnerabilities,
    )


# ── Competitor detection ─────────────────────────────────────────────────────


def _detect_competitors(
    tech_profile: Any | None,
    vendor_key: str,
) -> dict[str, str]:
    """Return a mapping of competitor_key -> adoption_depth for active competitors."""
    if tech_profile is None:
        return {}

    platform_adoption: dict[str, Any] = {}
    try:
        platform_adoption = tech_profile.platform_adoption or {}
    except AttributeError:
        logger.debug("tech_profile has no platform_adoption attribute")
        return {}

    active: dict[str, str] = {}
    for detected_vendor, adoption in platform_adoption.items():
        detected_key = _normalise_vendor(detected_vendor)
        if detected_key == vendor_key:
            continue

        try:
            depth = (
                adoption.depth
                if hasattr(adoption, "depth")
                else adoption.get("depth", "none")
            )
        except Exception:
            depth = "none"

        if depth and depth != "none":
            active[detected_key] = depth

    return active


# ── Battle card loading ───────────────────────────────────────────────────────


def _load_battle_card(vendor_key: str, competitor_key: str) -> dict[str, Any] | None:
    """Load a battle card YAML for a vendor/competitor pair."""
    candidates = [
        _COMPETITIVE_DIR / f"{vendor_key}_vs_{competitor_key}.yaml",
        _COMPETITIVE_DIR / f"{competitor_key}_vs_{vendor_key}.yaml",
    ]

    for path in candidates:
        if path.exists():
            try:
                with open(path) as f:
                    data = yaml.safe_load(f) or {}
                logger.debug("Loaded battle card: %s", path.name)
                return data
            except Exception as exc:
                logger.warning("Failed to parse battle card %s: %s", path.name, exc)

    return None


# ── Competitor object builder ─────────────────────────────────────────────────


def _build_competitor(
    competitor_key: str,
    adoption_depth: str,
    battle_card: dict[str, Any],
) -> Competitor:
    """Construct a Competitor from a battle card and detected adoption depth."""
    win_themes: list[dict[str, str]] = battle_card.get("win_themes", [])

    if win_themes:
        first_theme = win_themes[0]
        your_win_theme: str = first_theme.get("theme", "")
        differentiation: str = first_theme.get("detail", "")
    else:
        your_win_theme = ""
        differentiation = ""

    return Competitor(
        name=_display_name(competitor_key),
        position=_VENDOR_POSITIONS.get(competitor_key, "Technology Vendor"),
        threat_level=_DEPTH_TO_THREAT.get(adoption_depth, "low"),
        differentiation=differentiation,
        your_win_theme=your_win_theme,
    )


# ── Utilities ─────────────────────────────────────────────────────────────────


def _normalise_vendor(vendor: str) -> str:
    """Normalise a vendor name to a lowercase slug for file lookup."""
    v = vendor.lower().strip().replace(" ", "_")
    aliases: dict[str, str] = {
        "azure": "microsoft",
        "microsoft_azure": "microsoft",
        "google_cloud": "google",
        "gcp": "google",
        "google_cloud_platform": "google",
        "amazon": "aws",
        "amazon_web_services": "aws",
    }
    return aliases.get(v, v)


def _display_name(vendor_key: str) -> str:
    """Convert a normalised vendor key to a human-readable display name."""
    display_map: dict[str, str] = {
        "aws": "AWS",
        "microsoft": "Microsoft",
        "azure": "Microsoft Azure",
        "google": "Google Cloud",
        "gcp": "Google Cloud",
        "salesforce": "Salesforce",
        "oracle": "Oracle",
        "ibm": "IBM",
        "servicenow": "ServiceNow",
    }
    if vendor_key in display_map:
        return display_map[vendor_key]
    return vendor_key.replace("_", " ").title()
