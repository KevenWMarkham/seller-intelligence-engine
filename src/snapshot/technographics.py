"""Layer 1 — Technographic profiler.

Sources (waterfall): BuiltWith → TheirStack → Wappalyzer → job posting signals.
"""

import logging

from pydantic import BaseModel

from src.core.settings import settings

logger = logging.getLogger(__name__)


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


async def profile_tech_stack(domain: str) -> TechProfile:
    """
    Build a technology profile for a company using the waterfall of sources.

    Args:
        domain: Company domain.

    Returns:
        TechProfile with detected technologies and platform adoption depths.
    """
    # TODO: Phase 6 — waterfall: BuiltWith → TheirStack → Wappalyzer → LinkedIn jobs
    logger.info("Profiling tech stack for domain=%s", domain)
    return TechProfile(domain=domain)


async def _fetch_builtwith(domain: str) -> list[Technology]:
    """Query BuiltWith API for frontend technologies."""
    # TODO: Phase 6 — requires BUILTWITH_KEY
    if not settings.builtwith_key:
        logger.debug("BuiltWith API key not configured, skipping")
        return []
    return []


async def _fetch_theirstack(domain: str) -> list[Technology]:
    """Query TheirStack API for backend tech via job postings."""
    # TODO: Phase 6 — requires THEIRSTACK_KEY
    if not settings.theirstack_key:
        logger.debug("TheirStack API key not configured, skipping")
        return []
    return []


async def _analyze_job_postings(domain: str) -> list[HiringSignal]:
    """Scrape LinkedIn job postings for tech investment signals."""
    # TODO: Phase 6 — LinkedIn scraping or Proxycurl jobs API
    return []
