"""Layer 1 — Technographic profiler.

Sources (waterfall): BuiltWith → TheirStack → website technology detection → heuristics.

All API-based sources degrade gracefully when keys are absent.
The website detection layer always runs and provides baseline signals.
"""

import logging
import re
from pathlib import Path
from typing import Any

import httpx
import yaml
from pydantic import BaseModel

from src.core.settings import settings
from src.snapshot.aggregator import _extract_tech_mentions, scrape_company_website

logger = logging.getLogger(__name__)

_PLATFORMS_DIR = Path(__file__).parent.parent.parent / "config" / "platforms"
_HTTP_TIMEOUT = 8.0

# Map signal count to adoption depth label
_ADOPTION_DEPTH_THRESHOLDS = [
    (3, "deep"),
    (2, "moderate"),
    (1, "light"),
    (0, "evaluating"),
]


# ── Pydantic models ──────────────────────────────────────────────────────────


class Technology(BaseModel):
    name: str
    category: str
    confidence: float = 1.0
    source: str | None = None


class PlatformAdoption(BaseModel):
    vendor: str
    depth: str  # none | evaluating | light | moderate | deep
    products_detected: list[str] = []
    evidence: list[str] = []
    confidence_scores: dict[str, float] = {}


class HiringSignal(BaseModel):
    role: str
    tech_mentioned: list[str]
    job_url: str | None = None


class TechProfile(BaseModel):
    domain: str
    stack: list[Technology] = []
    platform_adoption: dict[str, PlatformAdoption] = {}
    confidence_scores: dict[str, float] = {}
    hiring_signals: list[HiringSignal] = []


# ── Main entry point ─────────────────────────────────────────────────────────


async def profile_tech_stack(domain: str) -> TechProfile:
    """Build a technology profile using available sources.

    Waterfall: BuiltWith (if key) → TheirStack (if key) → website detection.

    Args:
        domain: Company domain.

    Returns:
        TechProfile with detected stack and platform adoption depths.
    """
    logger.info("Profiling tech stack for domain=%s", domain)

    stack: list[Technology] = []
    tech_names: set[str] = set()

    # ── Layer 1: BuiltWith API (requires key) ───────────────────────────────
    if settings.builtwith_key:
        bw_techs = await _fetch_builtwith(domain)
        for tech in bw_techs:
            stack.append(tech)
            tech_names.add(tech.name.lower())

    # ── Layer 2: TheirStack API (requires key) ──────────────────────────────
    if settings.theirstack_key:
        ts_techs = await _fetch_theirstack(domain)
        for tech in ts_techs:
            if tech.name.lower() not in tech_names:
                stack.append(tech)
                tech_names.add(tech.name.lower())

    # ── Layer 3: Website technology detection (free, always runs) ───────────
    web_data = await scrape_company_website(domain)
    for tech_name in web_data.get("technologies_mentioned", []):
        if tech_name not in tech_names:
            stack.append(Technology(
                name=tech_name,
                category=_categorize_tech(tech_name),
                confidence=0.6,
                source="website_detection",
            ))
            tech_names.add(tech_name)

    # ── Layer 4: Infer platform adoption from detected technologies ──────────
    platform_adoption = _infer_platform_adoption(
        tech_names, web_data.get("raw_text", "")
    )

    # Build top-level confidence scores
    confidence_scores = {
        vendor: max(
            (t.confidence for t in stack if _tech_maps_to_vendor(t.name, vendor)),
            default=0.5,
        )
        for vendor in platform_adoption
    }

    return TechProfile(
        domain=domain,
        stack=stack,
        platform_adoption=platform_adoption,
        confidence_scores=confidence_scores,
    )


# ── BuiltWith integration ────────────────────────────────────────────────────


async def _fetch_builtwith(domain: str) -> list[Technology]:
    """Query BuiltWith free API for frontend technologies."""
    try:
        url = (
            f"https://api.builtwith.com/free1/api.json"
            f"?KEY={settings.builtwith_key}&LOOKUP={domain}"
        )
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        technologies = []
        for tech in data.get("Results", [{}])[0].get("Technologies", []):
            technologies.append(Technology(
                name=tech.get("Name", "unknown"),
                category=tech.get("Tag", "other"),
                confidence=0.95,
                source="builtwith",
            ))
        return technologies

    except Exception as exc:
        logger.debug("BuiltWith fetch failed for domain=%s: %s", domain, exc)
        return []


# ── TheirStack integration ───────────────────────────────────────────────────


async def _fetch_theirstack(domain: str) -> list[Technology]:
    """Query TheirStack API for backend technologies via job posting signals."""
    try:
        headers = {
            "Authorization": f"Bearer {settings.theirstack_key}",
            "Content-Type": "application/json",
        }
        payload = {"company_domain": domain, "include_technologies": True, "limit": 50}
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.post(
                "https://api.theirstack.com/v1/companies/search",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        technologies = []
        companies = data.get("data", [])
        if companies:
            for tech in companies[0].get("technologies", []):
                technologies.append(Technology(
                    name=tech.get("name", "unknown"),
                    category=tech.get("category", "other"),
                    confidence=0.9,
                    source="theirstack",
                ))
        return technologies

    except Exception as exc:
        logger.debug("TheirStack fetch failed for domain=%s: %s", domain, exc)
        return []


# ── Platform adoption inference ───────────────────────────────────────────────


def _infer_platform_adoption(
    tech_names: set[str],
    raw_text: str = "",
) -> dict[str, PlatformAdoption]:
    """Infer platform adoption depth from detected technologies + raw text.

    Cross-references detected technologies and text mentions against
    signal keywords from config/platforms/{vendor}.yaml.

    Args:
        tech_names: Set of normalized technology names detected.
        raw_text: Raw scraped text for additional keyword matching.

    Returns:
        Dict mapping vendor → PlatformAdoption (only vendors with signals).
    """
    vendor_signals: dict[str, list[str]] = {}

    for yaml_path in _PLATFORMS_DIR.glob("*.yaml"):
        vendor = yaml_path.stem
        try:
            with open(yaml_path) as f:
                catalog = yaml.safe_load(f) or {}
            keywords = catalog.get("signal_keywords", [])
            products = [p["name"] for p in catalog.get("products", [])]
            vendor_signals[vendor] = keywords + products
        except Exception:
            continue

    result: dict[str, PlatformAdoption] = {}

    for vendor, signals in vendor_signals.items():
        matched_techs: list[str] = []
        evidence: list[str] = []

        for signal in signals:
            signal_lower = signal.lower()

            # Check in detected tech names
            if any(signal_lower in t or t in signal_lower for t in tech_names):
                matched_techs.append(signal)
                evidence.append(f"Detected: {signal}")

            # Check in raw text (lower confidence)
            elif raw_text and re.search(re.escape(signal), raw_text, re.IGNORECASE):
                evidence.append(f"Mentioned: {signal}")

        total_signals = len(matched_techs) + len(evidence) // 2

        # Only include vendors with at least one signal
        if total_signals == 0 and not matched_techs:
            continue

        depth = "none"
        for threshold, label in _ADOPTION_DEPTH_THRESHOLDS:
            if total_signals > threshold:
                depth = label
                break

        result[vendor] = PlatformAdoption(
            vendor=vendor,
            depth=depth,
            products_detected=matched_techs[:5],
            evidence=evidence[:5],
        )

    return result


# ── Helpers ───────────────────────────────────────────────────────────────────


def _categorize_tech(tech_name: str) -> str:
    """Assign a broad category to a normalized technology name."""
    categories: dict[str, set[str]] = {
        "cloud": {"aws", "azure", "gcp", "oracle", "ibm"},
        "data": {"snowflake", "databricks", "bigquery"},
        "crm": {"salesforce"},
        "container": {"kubernetes", "docker"},
        "iac": {"terraform"},
        "language": {"python", "java", "javascript"},
        "frontend": {"react"},
    }
    for category, members in categories.items():
        if tech_name.lower() in members:
            return category
    return "other"


def _tech_maps_to_vendor(tech_name: str, vendor: str) -> bool:
    """Return True if a technology name is associated with a given vendor."""
    vendor_tech_map: dict[str, set[str]] = {
        "google": {"gcp", "bigquery", "vertex ai", "cloud run", "react"},
        "microsoft": {"azure", "azure ad"},
        "aws": {"aws"},
        "salesforce": {"salesforce"},
        "oracle": {"oracle"},
        "ibm": {"ibm"},
    }
    return tech_name.lower() in vendor_tech_map.get(vendor, set())
