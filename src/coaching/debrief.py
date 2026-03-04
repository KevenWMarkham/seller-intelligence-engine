"""Layer 5 — Post-call debrief analyzer.

Seller debriefs via chat after the call.
Coach analyzes: what went well vs gaps, new objections, next steps.
Updates objection library + seller MEMORY.md.
"""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from src.ai import ollama_client

logger = logging.getLogger(__name__)

_jinja = Environment(loader=FileSystemLoader(Path(__file__).parent.parent.parent / "prompts"))


class DebriefAnalysis(BaseModel):
    what_went_well: list[str]
    gaps_identified: list[str]
    new_objections_discovered: list[str]
    next_steps: list[str]
    follow_up_tasks: list[str]
    coaching_notes: str


async def analyze_debrief(
    seller_id: str,
    company_name: str,
    contact_name: str,
    contact_title: str,
    sales_motion: str,
    debrief_conversation: list[dict],
) -> DebriefAnalysis:
    """
    Analyze a post-call debrief conversation and extract coaching insights.

    Side effects (TODO Phase 10):
    - Adds new objections to the ChromaDB objection library.
    - Updates seller MEMORY.md with coaching notes.
    - Generates follow-up task suggestions.

    Args:
        seller_id: Seller identifier.
        company_name: Target company name.
        contact_name: Contact's name.
        contact_title: Contact's title.
        sales_motion: wedge | new | expand | displace
        debrief_conversation: List of {role, content} message dicts.

    Returns:
        DebriefAnalysis with coaching insights and action items.
    """
    template = _jinja.get_template("debrief_analysis.jinja2")
    prompt = template.render(
        company_name=company_name,
        contact_name=contact_name,
        contact_title=contact_title,
        sales_motion=sales_motion,
        conversation=debrief_conversation,
    )

    raw = await ollama_client.complete(prompt)
    return DebriefAnalysis.model_validate(raw)
