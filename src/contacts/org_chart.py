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

    Acronyms (cto, cfo, etc.) are matched as whole words to avoid false
    positives — e.g. "director" contains the substring "cto".
    """
    title_lower = title.lower()
    words = set(title_lower.split())

    # Acronyms must match as complete words
    decision_exact = {"cto", "cfo", "cio", "cso", "coo", "ceo"}
    decision_substrings = ["chief", "president", "evp", "svp"]

    influencer_exact = {"vp"}
    influencer_substrings = ["vice president", "director", "head of"]

    if words & decision_exact or any(k in title_lower for k in decision_substrings):
        return "decision_maker"
    if words & influencer_exact or any(k in title_lower for k in influencer_substrings):
        return "influencer"
    return "champion"
