"""Layer 3 — Org chart builder.

Uses Qwen to infer reporting structure from title patterns and LinkedIn connections.
Tags each contact: Decision Maker | Influencer | Champion.
"""

import logging

from pydantic import BaseModel

from src.ai import ollama_client
from src.contacts.resolver import ResolvedContact

logger = logging.getLogger(__name__)

FUNCTIONAL_AREAS = [
    "Engineering",
    "Finance",
    "Sales",
    "Marketing",
    "Operations",
    "HR",
    "Legal",
    "Product",
    "Data & Analytics",
    "Security",
    "IT Operations",
    "Customer Success",
]


class OrgNode(BaseModel):
    contact_name: str
    title: str
    functional_area: str
    role_type: str  # decision_maker | influencer | champion
    reports_to: str | None = None


class OrgChart(BaseModel):
    company: str
    nodes: list[OrgNode]


async def build_org_chart(
    company_name: str,
    contacts: list[ResolvedContact],
) -> OrgChart:
    """
    Build a functional org chart from a list of resolved contacts.

    Uses title pattern matching + Qwen inference to:
    1. Assign functional areas
    2. Classify role types (decision_maker / influencer / champion)
    3. Infer approximate reporting relationships

    Args:
        company_name: Target company name.
        contacts: List of resolved contacts.

    Returns:
        OrgChart with tagged nodes.
    """
    # TODO: Phase 8 — Qwen-based org inference
    logger.info("Building org chart for %s (%d contacts)", company_name, len(contacts))
    return OrgChart(company=company_name, nodes=[])


def classify_role_type(title: str) -> str:
    """
    Heuristic role type classification based on title seniority.

    Returns: decision_maker | influencer | champion
    """
    title_lower = title.lower()
    decision_keywords = ["chief", "cto", "cfo", "cio", "cso", "coo", "ceo", "president", "evp", "svp"]
    influencer_keywords = ["vp", "vice president", "director", "head of"]
    if any(k in title_lower for k in decision_keywords):
        return "decision_maker"
    if any(k in title_lower for k in influencer_keywords):
        return "influencer"
    return "champion"
