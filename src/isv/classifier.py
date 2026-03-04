"""Layer 1.5 — ISV industry and capability classifier."""

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
    industries: list[str]  # Subset of INDUSTRY_VERTICALS
    capabilities: list[str]  # Subset of CAPABILITY_AREAS
    primary_buyer: str  # e.g. "CTO", "CISO", "CFO"
    use_case_summary: str


async def classify_isv(
    isv_name: str,
    description: str,
    marketplace: str,
) -> ISVClassification:
    """
    Classify an ISV solution into industry verticals and capability areas.

    Uses Qwen with few-shot taxonomy prompting.

    Args:
        isv_name: ISV solution name.
        description: Solution description text.
        marketplace: Source marketplace.

    Returns:
        ISVClassification with industries, capabilities, and primary buyer.
    """
    # TODO: Phase 9 — implement classification prompt
    logger.info("Classifying ISV: %s", isv_name)
    return ISVClassification(
        industries=[],
        capabilities=[],
        primary_buyer="CTO",
        use_case_summary=description[:200] if description else "",
    )
