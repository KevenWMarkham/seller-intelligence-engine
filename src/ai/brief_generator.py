"""Layer 4 — Platform-specific conversation brief generator."""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from src.ai import ollama_client

logger = logging.getLogger(__name__)

_jinja = Environment(loader=FileSystemLoader(Path(__file__).parent.parent.parent / "prompts"))


class PredictedObjection(BaseModel):
    objection: str
    suggested_response: str


class ConversationBrief(BaseModel):
    opener: str  # 2-3 sentence conversation starter referencing the news
    why_it_matters: str  # Why this matters to the contact's functional area
    solution_connection: str  # How your platform addresses their likely pain
    isv_recommendation: str  # Specific ISV solution that fits
    suggested_ask: str  # Specific next step
    predicted_objections: list[PredictedObjection]


async def generate_brief(
    company_name: str,
    contact_name: str,
    contact_title: str,
    functional_area: str,
    news_headline: str,
    news_summary: str,
    platform_vendor: str,
    sales_motion: str,
    company_priorities: list[str],
    platform_products: list[str],
) -> ConversationBrief:
    """
    Generate a platform-specific, conversation-ready brief for a seller task.

    Args:
        company_name: Target company name.
        contact_name: Contact's full name.
        contact_title: Contact's job title.
        functional_area: Contact's functional area (Engineering, Finance, etc.).
        news_headline: The triggering news headline.
        news_summary: Brief summary of the news event.
        platform_vendor: Active platform vendor (e.g. "google").
        sales_motion: wedge | new | expand | displace
        company_priorities: List of company business priorities.
        platform_products: Relevant platform products for this conversation.

    Returns:
        ConversationBrief with opener, objections, and ask.
    """
    template = _jinja.get_template("generate_brief.jinja2")
    prompt = template.render(
        company_name=company_name,
        contact_name=contact_name,
        contact_title=contact_title,
        functional_area=functional_area,
        news_headline=news_headline,
        news_summary=news_summary,
        platform_vendor=platform_vendor,
        sales_motion=sales_motion,
        company_priorities=company_priorities,
        platform_products=platform_products,
    )

    raw = await ollama_client.complete(prompt)
    return ConversationBrief.model_validate(raw)
