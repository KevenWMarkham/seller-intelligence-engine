"""Layer 4 — News relevance classifier."""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from src.ai import ollama_client

logger = logging.getLogger(__name__)

_jinja = Environment(loader=FileSystemLoader(Path(__file__).parent.parent.parent / "prompts"))


class NewsClassification(BaseModel):
    relevance_score: float  # 0.0 – 1.0
    urgency: str  # high | medium | low
    signal_type: str  # earnings | product_launch | leadership_change | m_and_a | partnership | tech_initiative
    opportunity_type: str  # upsell | risk_mitigation | new_conversation | relationship_deepener
    companies_mentioned: list[str]
    summary: str


async def classify_news(
    headline: str,
    body: str,
    platform_vendor: str,
    watched_companies: list[str],
) -> NewsClassification:
    """
    Classify a news item for relevance, urgency, and opportunity type.

    Args:
        headline: News headline.
        body: News body text (truncated to ~2000 chars before passing).
        platform_vendor: Active platform vendor context (e.g. "google").
        watched_companies: List of company names in the seller's account list.

    Returns:
        NewsClassification with relevance score and type metadata.
    """
    template = _jinja.get_template("classify_news.jinja2")
    prompt = template.render(
        headline=headline,
        body=body[:2000],
        platform_vendor=platform_vendor,
        watched_companies=watched_companies,
    )

    raw = await ollama_client.complete(prompt)
    return NewsClassification.model_validate(raw)
