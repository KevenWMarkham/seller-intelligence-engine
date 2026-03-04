"""Layer 1.5 — ISV industry and capability classifier.

Uses Qwen with JSON mode to classify ISV descriptions into standard
industry verticals and capability areas from the taxonomy defined here.

Graceful degradation: if Ollama is unavailable, returns the pre-populated
industries/capabilities from the ISVSolution DB row (set during catalog load).
"""

import json
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from src.ai import ollama_client

logger = logging.getLogger(__name__)

_jinja = Environment(loader=FileSystemLoader(Path(__file__).parent.parent.parent / "prompts"))

INDUSTRY_VERTICALS = [
    "Financial Services",
    "Healthcare & Life Sciences",
    "Retail & CPG",
    "Manufacturing",
    "Energy & Utilities",
    "Telecommunications",
    "Government & Public Sector",
    "Media & Entertainment",
]

CAPABILITY_AREAS = [
    "AI & Machine Learning",
    "Data & Analytics",
    "Security & Compliance",
    "Application Modernization",
    "Collaboration & Productivity",
    "Customer Experience",
    "Automation & Integration",
    "Infrastructure & Operations",
]


class ISVClassification(BaseModel):
    industries: list[str]       # Subset of INDUSTRY_VERTICALS
    capabilities: list[str]     # Subset of CAPABILITY_AREAS
    primary_buyer: str          # e.g. "CTO", "CISO", "CFO"
    use_case_summary: str


async def classify_isv(
    isv_name: str,
    description: str,
    marketplace: str,
    pre_classified_industries: list[str] | None = None,
    pre_classified_capabilities: list[str] | None = None,
) -> ISVClassification:
    """Classify an ISV solution into industry verticals and capability areas.

    If the ISV already has pre-classified industries/capabilities (from catalog),
    those are validated and returned with a Qwen-generated use_case_summary.
    Otherwise Qwen classifies from scratch.

    Args:
        isv_name: ISV solution name.
        description: Solution description text.
        marketplace: Source marketplace.
        pre_classified_industries: Industries from static catalog (if available).
        pre_classified_capabilities: Capabilities from static catalog (if available).

    Returns:
        ISVClassification with industries, capabilities, and primary buyer.
    """
    logger.info("Classifying ISV: %s", isv_name)

    # If we have catalog data, skip the expensive Qwen call and just validate
    if pre_classified_industries and pre_classified_capabilities:
        valid_industries = [i for i in pre_classified_industries if i in INDUSTRY_VERTICALS]
        valid_capabilities = [c for c in pre_classified_capabilities if c in CAPABILITY_AREAS]
        return ISVClassification(
            industries=valid_industries or pre_classified_industries[:3],
            capabilities=valid_capabilities or pre_classified_capabilities[:2],
            primary_buyer=_infer_buyer_from_capabilities(valid_capabilities or pre_classified_capabilities),
            use_case_summary=description[:300] if description else "",
        )

    # Qwen classification for ISVs without catalog data
    prompt = (
        f"You are an enterprise software analyst. Classify this ISV solution.\n\n"
        f"ISV Name: {isv_name}\n"
        f"Marketplace: {marketplace}\n"
        f"Description: {description[:600]}\n\n"
        f"Available industry verticals: {json.dumps(INDUSTRY_VERTICALS)}\n"
        f"Available capability areas: {json.dumps(CAPABILITY_AREAS)}\n\n"
        f"Return JSON:\n"
        f'{{"industries": ["<up to 3 matching verticals>"], '
        f'"capabilities": ["<up to 3 matching areas>"], '
        f'"primary_buyer": "<job title of primary economic buyer>", '
        f'"use_case_summary": "<2-3 sentence plain-English summary>"}}'
    )

    try:
        raw = await ollama_client.complete(prompt)
        industries = [i for i in raw.get("industries", []) if i in INDUSTRY_VERTICALS]
        capabilities = [c for c in raw.get("capabilities", []) if c in CAPABILITY_AREAS]
        return ISVClassification(
            industries=industries or ["Financial Services"],
            capabilities=capabilities or ["Data & Analytics"],
            primary_buyer=raw.get("primary_buyer", "CTO"),
            use_case_summary=raw.get("use_case_summary", description[:300] if description else ""),
        )
    except Exception as exc:
        logger.warning("Qwen ISV classification failed for %s: %s — using fallback", isv_name, exc)
        return ISVClassification(
            industries=[],
            capabilities=[],
            primary_buyer="CTO",
            use_case_summary=description[:200] if description else "",
        )


def _infer_buyer_from_capabilities(capabilities: list[str]) -> str:
    """Infer primary buyer title from capability areas."""
    if "Security & Compliance" in capabilities:
        return "CISO"
    if "AI & Machine Learning" in capabilities or "Data & Analytics" in capabilities:
        return "Chief Data Officer"
    if "Infrastructure & Operations" in capabilities:
        return "VP Infrastructure"
    if "Customer Experience" in capabilities:
        return "Chief Marketing Officer"
    if "Automation & Integration" in capabilities:
        return "Chief Operating Officer"
    return "CTO"
