"""Layer 1 — Sales motion classifier.

Classifies into: WEDGE | NEW | EXPAND | DISPLACE
"""

import logging
from pathlib import Path
from typing import Literal

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from src.ai import ollama_client
from src.snapshot.technographics import TechProfile

logger = logging.getLogger(__name__)

_jinja = Environment(loader=FileSystemLoader(Path(__file__).parent.parent.parent / "prompts"))

SalesMotionType = Literal["wedge", "new", "expand", "displace"]


class SalesMotion(BaseModel):
    type: SalesMotionType
    confidence: float
    reasoning: str
    entry_points: list[str] = []
    competitor_to_displace: str | None = None


async def classify_motion(
    company_name: str,
    platform_vendor: str,
    tech_profile: TechProfile,
) -> SalesMotion:
    """
    Classify the sales motion for a company given the seller's platform vendor and tech profile.

    Motion types:
    - wedge: No platform adoption. Entry via narrow POC.
    - new: Greenfield. No vendor relationship.
    - expand: Active adoption in 1-2 areas. Adjacent workload play.
    - displace: Using competitor. TCO/risk case required.

    Args:
        company_name: Target company name.
        platform_vendor: Seller's platform vendor (e.g. "google").
        tech_profile: Detected technology profile from technographics.

    Returns:
        SalesMotion with type, confidence, and recommended entry points.
    """
    template = _jinja.get_template("classify_motion.jinja2")
    prompt = template.render(
        company_name=company_name,
        platform_vendor=platform_vendor,
        platform_adoption=tech_profile.platform_adoption,
        tech_stack=[t.name for t in tech_profile.stack],
    )

    raw = await ollama_client.complete(prompt)
    return SalesMotion.model_validate(raw)
