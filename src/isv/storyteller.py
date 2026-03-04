"""Layer 1.5 — ISV solution storyteller.

Generates Qwen-written ISV narratives tailored to a specific company's context.
"""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from src.ai import ollama_client

logger = logging.getLogger(__name__)

_jinja = Environment(loader=FileSystemLoader(Path(__file__).parent.parent.parent / "prompts"))


class ISVStory(BaseModel):
    isv_name: str
    plain_english_description: str
    company_relevance: str  # How it maps to this company's specific priorities
    business_outcomes: str  # Outcomes from similar companies
    platform_integration_story: str  # How it runs on the seller's platform
    competitive_angle: str  # Why this ISV vs alternatives on competitor platforms


async def generate_isv_story(
    isv_name: str,
    isv_description: str,
    company_name: str,
    company_priorities: list[str],
    platform_vendor: str,
    business_outcomes: list[str],
) -> ISVStory:
    """
    Generate a tailored ISV solution narrative for a specific company.

    Args:
        isv_name: ISV solution name.
        isv_description: ISV solution description.
        company_name: Target company name.
        company_priorities: Company's business priorities.
        platform_vendor: Seller's platform vendor.
        business_outcomes: Known outcomes from ISV capability mapping.

    Returns:
        ISVStory with business-value narrative components.
    """
    template = _jinja.get_template("match_isv.jinja2")
    prompt = template.render(
        isv_name=isv_name,
        isv_description=isv_description,
        company_name=company_name,
        company_priorities=company_priorities,
        platform_vendor=platform_vendor,
        business_outcomes=business_outcomes,
    )

    raw = await ollama_client.complete(prompt)
    return ISVStory.model_validate(raw)
