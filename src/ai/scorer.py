"""Layer 4 — Snapshot-driven priority scorer."""

import logging
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from src.ai import ollama_client

logger = logging.getLogger(__name__)

_jinja = Environment(loader=FileSystemLoader(Path(__file__).parent.parent.parent / "prompts"))
_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "scoring.yaml"


def _load_weights() -> dict[str, float]:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)["weights"]


class PriorityScore(BaseModel):
    score: int  # 1 – 100
    reasoning: str
    factor_scores: dict[str, float]  # factor_name → 0-1 score per factor


async def score_task(
    company_name: str,
    company_priorities: list[str],
    platform_adoption_depth: str,
    sales_motion: str,
    contact_role_type: str,
    contact_title: str,
    news_urgency: str,
    deal_value_estimate: str | None,
) -> PriorityScore:
    """
    Score a seller task 1-100 using 6 weighted factors.

    Factor weights are loaded from config/scoring.yaml.

    Returns:
        PriorityScore with final score and natural-language reasoning.
    """
    weights = _load_weights()

    template = _jinja.get_template("score_priority.jinja2")
    prompt = template.render(
        company_name=company_name,
        company_priorities=company_priorities,
        platform_adoption_depth=platform_adoption_depth,
        sales_motion=sales_motion,
        contact_role_type=contact_role_type,
        contact_title=contact_title,
        news_urgency=news_urgency,
        deal_value_estimate=deal_value_estimate or "unknown",
        weights=weights,
    )

    raw = await ollama_client.complete(prompt)
    return PriorityScore.model_validate(raw)
