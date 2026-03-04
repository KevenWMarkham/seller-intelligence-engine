"""Layer 1.5 — ISV-company matcher.

Matches ISVs from the DB to a target company using multi-factor scoring:
  - Industry fit     (30%): company vertical matches ISV target industries
  - Capability fit   (40%): ISV capabilities match company priorities
  - Platform affinity(20%): co-sell status, integration depth, cert level
  - Motion alignment (10%): ISV-motion fit (expand ISVs for expand motion, etc.)

Returns top N ISVMatch objects sorted by fit_score descending.
"""

import json
import logging

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.isv.affinity import score_affinity_sync
from src.models.isv import ISVSolution

logger = logging.getLogger(__name__)

# Scoring weights — must sum to 1.0
_INDUSTRY_WEIGHT = 0.30
_CAPABILITY_WEIGHT = 0.40
_AFFINITY_WEIGHT = 0.20
_MOTION_WEIGHT = 0.10

# Capability keyword → ISV capability area mapping for priority matching
_PRIORITY_KEYWORDS: dict[str, list[str]] = {
    "ai": ["AI & Machine Learning"],
    "machine learning": ["AI & Machine Learning"],
    "ml ": ["AI & Machine Learning"],
    "data": ["Data & Analytics", "AI & Machine Learning"],
    "analytics": ["Data & Analytics"],
    "security": ["Security & Compliance"],
    "compliance": ["Security & Compliance"],
    "migration": ["Application Modernization", "Data & Analytics"],
    "moderniz": ["Application Modernization"],
    "cloud": ["Infrastructure & Operations", "Application Modernization"],
    "automation": ["Automation & Integration"],
    "integration": ["Automation & Integration"],
    "customer": ["Customer Experience"],
    "infrastructure": ["Infrastructure & Operations"],
    "observability": ["Infrastructure & Operations"],
    "monitoring": ["Infrastructure & Operations"],
}

# Motion → preferred integration depth
_MOTION_DEPTH_PREFERENCE: dict[str, list[str]] = {
    "wedge": ["transactable"],
    "new": ["transactable", "api_integration"],
    "expand": ["transactable", "api_integration"],
    "displace": ["transactable"],
}


class ISVMatch(BaseModel):
    isv_id: int
    isv_name: str
    fit_score: float            # 0.0 – 1.0 composite score
    motion_alignment: str       # wedge | new | expand | displace
    conversation_hook: str      # Short sentence for conversation opener
    matched_priorities: list[str] = []   # Company priorities that matched
    matched_capabilities: list[str] = [] # ISV capabilities that drove the match
    business_outcomes: list[str] = []    # Top 2 outcomes for this ISV
    co_sell_status: str | None = None


async def match_isvs_to_company(
    company_name: str,
    industry: str | None,
    company_priorities: list[str],
    tech_stack: list[str],
    platform_vendor: str,
    sales_motion: str,
    session: AsyncSession,
    top_n: int = 5,
) -> list[ISVMatch]:
    """Match the top ISVs from the DB to a target company.

    Scoring factors:
    - Industry fit: company vertical matches ISV target industries
    - Capability fit: ISV capabilities address company priorities
    - Platform affinity: co-sell status, listing depth, certification
    - Motion alignment: ISV integration type suits the sales motion

    Args:
        company_name: Target company name.
        industry: Company industry vertical.
        company_priorities: List of company business priorities (strings).
        tech_stack: Detected technologies at the company.
        platform_vendor: Seller's platform vendor.
        sales_motion: wedge | new | expand | displace
        session: Async DB session.
        top_n: Number of top matches to return.

    Returns:
        List of ISVMatch ranked by fit_score descending.
    """
    logger.info(
        "Matching ISVs for company=%s industry=%s motion=%s vendor=%s",
        company_name, industry, sales_motion, platform_vendor,
    )

    # Load ISVs for this platform vendor
    result = await session.execute(
        select(ISVSolution).where(ISVSolution.platform_vendor == platform_vendor)
    )
    isv_solutions = list(result.scalars().all())

    if not isv_solutions:
        logger.warning(
            "No ISVs in DB for vendor=%s — seed catalog first via run_pipeline.py --layer isvs",
            platform_vendor,
        )
        return []

    priorities_lower = [p.lower() for p in company_priorities]
    preferred_depths = _MOTION_DEPTH_PREFERENCE.get(sales_motion.lower(), ["transactable"])

    matches: list[ISVMatch] = []

    for isv in isv_solutions:
        isv_industries = _load_json_list(isv.industries_json)
        isv_capabilities = _load_json_list(isv.capabilities_json)
        isv_outcomes = _load_json_list(isv.business_outcomes_json)

        # ── Industry score ─────────────────────────────────────────────────
        industry_score = 0.0
        if industry and isv_industries:
            if any(industry.lower() in ind.lower() or ind.lower() in industry.lower()
                   for ind in isv_industries):
                industry_score = 1.0
            else:
                industry_score = 0.2  # partial credit — ISV may still be relevant
        elif not isv_industries:
            industry_score = 0.4  # unknown industries: neutral

        # ── Capability score ───────────────────────────────────────────────
        matched_caps, matched_pris = _score_capability_fit(
            priorities_lower, isv_capabilities
        )
        capability_score = min(1.0, len(matched_caps) / max(1, len(isv_capabilities)))
        if not isv_capabilities:
            capability_score = 0.3

        # ── Affinity score ─────────────────────────────────────────────────
        affinity_score = isv.affinity_score or score_affinity_sync(
            isv.co_sell_status, isv.integration_depth, isv.cert_level
        )

        # ── Motion score ───────────────────────────────────────────────────
        motion_score = 1.0 if (isv.integration_depth in preferred_depths) else 0.4

        # ── Composite ──────────────────────────────────────────────────────
        fit_score = round(
            industry_score * _INDUSTRY_WEIGHT
            + capability_score * _CAPABILITY_WEIGHT
            + affinity_score * _AFFINITY_WEIGHT
            + motion_score * _MOTION_WEIGHT,
            3,
        )

        hook = _build_conversation_hook(isv.name, matched_pris, platform_vendor, sales_motion)

        matches.append(
            ISVMatch(
                isv_id=isv.id,
                isv_name=isv.name,
                fit_score=fit_score,
                motion_alignment=sales_motion,
                conversation_hook=hook,
                matched_priorities=matched_pris[:3],
                matched_capabilities=matched_caps[:3],
                business_outcomes=isv_outcomes[:2],
                co_sell_status=isv.co_sell_status,
            )
        )

    matches.sort(key=lambda m: m.fit_score, reverse=True)
    top = matches[:top_n]

    logger.info(
        "ISV matching for %s: %d ISVs scored, top %d selected (best fit=%.3f)",
        company_name,
        len(matches),
        len(top),
        top[0].fit_score if top else 0.0,
    )
    return top


# ── Helpers ───────────────────────────────────────────────────────────────────


def _load_json_list(json_str: str | None) -> list[str]:
    """Safe JSON list deserialization."""
    if not json_str:
        return []
    try:
        parsed = json.loads(json_str)
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _score_capability_fit(
    priorities_lower: list[str],
    isv_capabilities: list[str],
) -> tuple[list[str], list[str]]:
    """Return (matched_capabilities, matched_priority_phrases) for scoring.

    Checks each priority string against keyword→capability mappings.
    """
    matched_caps: list[str] = []
    matched_pris: list[str] = []

    for cap in isv_capabilities:
        for priority in priorities_lower:
            for keyword, cap_areas in _PRIORITY_KEYWORDS.items():
                if keyword in priority and cap in cap_areas:
                    if cap not in matched_caps:
                        matched_caps.append(cap)
                    # Find the original (non-lowercased) priority phrase
                    original_idx = priorities_lower.index(priority)
                    original = priority  # we only have lower, that's fine
                    if original not in matched_pris:
                        matched_pris.append(original)

    return matched_caps, matched_pris


def _build_conversation_hook(
    isv_name: str,
    matched_priorities: list[str],
    platform_vendor: str,
    sales_motion: str,
) -> str:
    """Build a short conversation hook for this ISV match."""
    if matched_priorities:
        pri_str = matched_priorities[0].replace("_", " ").split(" — ")[0]
        return (
            f"{isv_name} on {platform_vendor.title()} directly addresses "
            f"your {pri_str} initiative — let me show you what similar companies achieved."
        )
    motion_hooks = {
        "wedge": f"Start with {isv_name} as a low-risk entry point to demonstrate {platform_vendor.title()} value.",
        "expand": f"{isv_name} is the natural next workload to expand your {platform_vendor.title()} footprint.",
        "displace": f"{isv_name} on {platform_vendor.title()} delivers the same capabilities at significantly lower TCO.",
        "new": f"{isv_name} gives you a ready-made solution to accelerate your {platform_vendor.title()} adoption.",
    }
    return motion_hooks.get(
        sales_motion.lower(),
        f"{isv_name} is a highly rated {platform_vendor.title()} partner solution for your use case.",
    )
