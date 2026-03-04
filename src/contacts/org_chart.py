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

# Ordered list of (keywords, functional_area) tuples.
# First match wins; keywords are tested case-insensitively against the full title.
_FA_TITLE_KEYWORDS: list[tuple[list[str], str]] = [
    (
        ["cto", "engineering", "developer", "software", "architect",
         "infrastructure", "devops", "sre", "platform"],
        "Engineering",
    ),
    (
        ["cfo", "finance", "financial", "controller", "treasurer", "accounting"],
        "Finance",
    ),
    (
        ["cmo", "marketing", "brand", "growth", "demand", "content"],
        "Marketing",
    ),
    (
        ["sales", "account executive", "revenue", "business development"],
        "Sales",
    ),
    (
        ["coo", "operations", "supply chain", "logistics", "procurement"],
        "Operations",
    ),
    (
        ["chro", "hr ", "human resources", "people", "talent", "recruiting"],
        "HR",
    ),
    (
        ["legal", "counsel", "compliance", "general counsel", "privacy"],
        "Legal",
    ),
    (
        ["cpo", "product manager", "product director", "product owner"],
        "Product",
    ),
    (
        ["data", "analytics", "bi ", "intelligence", "scientist",
         "ml ", "ai ", "machine learning"],
        "Data & Analytics",
    ),
    (
        ["ciso", "security", "infosec", "cyber", "information security"],
        "Security",
    ),
    (
        ["it director", "it manager", "systems admin", "network",
         "infrastructure manager"],
        "IT Operations",
    ),
    (
        ["customer success", "csm", "client success", "account manager"],
        "Customer Success",
    ),
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


def assign_functional_area(title: str) -> str:
    """
    Map a job title to a functional area using keyword heuristics.

    Iterates through _FA_TITLE_KEYWORDS in order; returns the functional area
    for the first keyword that appears (case-insensitive) in the title.
    Defaults to "Operations" when no keyword matches.

    Args:
        title: Contact job title.

    Returns:
        Functional area string from FUNCTIONAL_AREAS (or "Operations" fallback).
    """
    title_lower = title.lower()
    for keywords, fa in _FA_TITLE_KEYWORDS:
        for kw in keywords:
            if kw in title_lower:
                return fa
    return "Operations"


async def _infer_reporting_structure(
    company_name: str,
    contacts: list[ResolvedContact],
) -> dict[str, str | None]:
    """
    Ask Qwen to infer reporting relationships for a set of contacts.

    Returns a dict mapping contact name → manager name (or None).
    On any failure (Ollama unavailable, parse error, missing keys) the
    function logs a warning and returns an empty dict so callers can
    fall back to reports_to=None for all nodes.

    Args:
        company_name: Target company name used in the prompt.
        contacts: Contacts whose hierarchy should be inferred.

    Returns:
        Dict of {contact_name: reports_to_name_or_None}.
    """
    if not contacts:
        return {}

    contacts_list = "\n".join(
        f"- {c.name} ({c.title})" for c in contacts
    )

    prompt = (
        f"You are an org chart inference expert. "
        f"Given these executives at {company_name}, "
        f"infer who reports to whom based on typical corporate hierarchy.\n\n"
        f"Contacts:\n{contacts_list}\n\n"
        f'Return JSON:\n{{"reporting": [{{"name": "<contact name>", "reports_to": "<manager name or null>"}}]}}'
    )

    try:
        result = await ollama_client.complete(prompt)
        reporting_list = result.get("reporting", [])
        mapping: dict[str, str | None] = {}
        for entry in reporting_list:
            name = entry.get("name")
            reports_to = entry.get("reports_to")
            if name:
                # Treat the string "null" or empty string as None
                mapping[name] = reports_to if reports_to and reports_to != "null" else None
        return mapping
    except Exception as exc:
        logger.warning(
            "Qwen org-chart inference failed for %s — defaulting to no reporting links: %s",
            company_name,
            exc,
        )
        return {}


async def build_org_chart(
    company_name: str,
    contacts: list[ResolvedContact],
) -> OrgChart:
    """
    Build a functional org chart from a list of resolved contacts.

    Steps:
    1. Assign functional areas via title keywords (or honour existing FA on contact).
    2. Classify role type via title seniority heuristic (or honour existing role_type).
    3. Attempt Qwen-based reporting structure inference (graceful degradation on failure).
    4. Assemble OrgNode list and return OrgChart.

    Args:
        company_name: Target company name.
        contacts: List of resolved contacts.

    Returns:
        OrgChart with tagged nodes.  If Ollama is unavailable, nodes are still
        fully populated with FA and role_type — only reports_to will be None.
    """
    logger.info("Building org chart for %s (%d contacts)", company_name, len(contacts))

    if not contacts:
        return OrgChart(company=company_name, nodes=[])

    # Step 3: attempt Qwen inference for reporting structure
    reporting_map = await _infer_reporting_structure(company_name, contacts)

    # Steps 1, 2, 4: build nodes
    nodes: list[OrgNode] = []
    for contact in contacts:
        fa = contact.functional_area or assign_functional_area(contact.title)
        role = contact.role_type or classify_role_type(contact.title)
        reports_to = reporting_map.get(contact.name)
        nodes.append(
            OrgNode(
                contact_name=contact.name,
                title=contact.title,
                functional_area=fa,
                role_type=role,
                reports_to=reports_to,
            )
        )

    logger.info(
        "Org chart built for %s: %d nodes, reporting links resolved for %d",
        company_name,
        len(nodes),
        sum(1 for n in nodes if n.reports_to is not None),
    )
    return OrgChart(company=company_name, nodes=nodes)


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
