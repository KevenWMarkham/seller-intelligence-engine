"""Layer 3 — Contact-news-platform linker.

Triple match: news event → specific FA contact → platform opportunity.
"""

import logging

from pydantic import BaseModel

from src.contacts.resolver import ResolvedContact

logger = logging.getLogger(__name__)

# Signal type → functional area routing rules
SIGNAL_FA_ROUTING: dict[str, list[str]] = {
    "tech_initiative": ["Engineering", "Data & Analytics", "IT Operations"],
    "earnings": ["Finance", "Sales", "Executive"],
    "product_launch": ["Product", "Marketing", "Engineering"],
    "leadership_change": ["Executive"],
    "m_and_a": ["Finance", "Legal", "Executive"],
    "partnership": ["Business Development", "Sales", "Product"],
    "security": ["Security", "IT Operations", "Engineering"],
}


class ContactNewsMatch(BaseModel):
    contact: ResolvedContact
    signal_type: str
    news_headline: str
    platform_products: list[str]
    relevance_score: float  # 0.0 – 1.0
    conversation_angle: str


def link_contacts_to_news(
    contacts: list[ResolvedContact],
    signal_type: str,
    news_headline: str,
    platform_vendor: str,
    platform_products: list[str],
) -> list[ContactNewsMatch]:
    """
    Match news signals to the most relevant FA contacts.

    Routing rules map signal types to functional areas. Contacts in matching
    FAs receive higher relevance scores.

    Args:
        contacts: Resolved contacts for a company.
        signal_type: News signal type (tech_initiative, earnings, etc.).
        news_headline: News headline for context.
        platform_vendor: Seller's platform vendor.
        platform_products: Relevant platform products.

    Returns:
        List of ContactNewsMatch sorted by relevance_score descending.
    """
    relevant_fas = SIGNAL_FA_ROUTING.get(signal_type, [])
    matches: list[ContactNewsMatch] = []

    for contact in contacts:
        fa_match = contact.functional_area in relevant_fas if contact.functional_area else False
        role_boost = {"decision_maker": 0.3, "influencer": 0.2, "champion": 0.1}.get(
            contact.role_type or "", 0.0
        )
        base_score = 0.7 if fa_match else 0.3
        relevance_score = min(1.0, base_score + role_boost + contact.platform_relevance_score * 0.1)

        matches.append(
            ContactNewsMatch(
                contact=contact,
                signal_type=signal_type,
                news_headline=news_headline,
                platform_products=platform_products,
                relevance_score=relevance_score,
                conversation_angle=_build_angle(contact, signal_type, platform_vendor),
            )
        )

    return sorted(matches, key=lambda m: m.relevance_score, reverse=True)


def _build_angle(contact: ResolvedContact, signal_type: str, platform_vendor: str) -> str:
    """Build a one-line conversation angle for a contact-signal pair."""
    # TODO: Phase 4 — replace with Qwen-generated angle
    return f"Discuss how {platform_vendor} can help with the {signal_type.replace('_', ' ')} initiative"
