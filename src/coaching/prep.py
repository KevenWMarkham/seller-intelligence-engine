"""Layer 5 — Pre-call prep package generator."""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from src.ai import ollama_client

logger = logging.getLogger(__name__)

_jinja = Environment(loader=FileSystemLoader(Path(__file__).parent.parent.parent / "prompts"))


class CallRoadmapStep(BaseModel):
    phase: str  # open | discover | value | ask
    objective: str
    key_questions: list[str]
    time_allocation: str  # e.g. "3 min"


class PrepPackage(BaseModel):
    contact_dossier: str  # Role, tenure, recent activity, communication style
    company_situation: str  # News triggers, financial health, competitive position
    isv_brief: str  # Recommended ISVs and outcomes
    call_roadmap: list[CallRoadmapStep]
    objection_predictions: list[dict]  # objection + suggested_response
    success_metrics: list[str]


async def generate_prep_package(
    seller_id: str,
    contact_name: str,
    contact_title: str,
    contact_recent_activity: str | None,
    company_name: str,
    news_trigger: str,
    sales_motion: str,
    platform_vendor: str,
    platform_products: list[str],
    company_priorities: list[str],
    isv_recommendations: list[dict],
) -> PrepPackage:
    """
    Generate a comprehensive pre-call preparation package for a seller task.

    Includes: contact dossier, company situation, ISV brief, call roadmap,
    predicted objections, and success metrics.

    Args:
        seller_id: Seller identifier for personalization via MEMORY.md.
        contact_name: Contact's full name.
        contact_title: Contact's job title.
        contact_recent_activity: Summary of recent LinkedIn/social activity.
        company_name: Target company name.
        news_trigger: The triggering news event.
        sales_motion: wedge | new | expand | displace
        platform_vendor: Seller's platform vendor.
        platform_products: Relevant platform products.
        company_priorities: Company business priorities.
        isv_recommendations: List of ISV match dicts.

    Returns:
        PrepPackage with all call preparation components.
    """
    template = _jinja.get_template("prep_package.jinja2")
    prompt = template.render(
        contact_name=contact_name,
        contact_title=contact_title,
        contact_recent_activity=contact_recent_activity or "No recent activity found",
        company_name=company_name,
        news_trigger=news_trigger,
        sales_motion=sales_motion,
        platform_vendor=platform_vendor,
        platform_products=platform_products,
        company_priorities=company_priorities,
        isv_recommendations=isv_recommendations,
    )

    raw = await ollama_client.complete(prompt)
    return PrepPackage.model_validate(raw)
