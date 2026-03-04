"""Tests for Layer 1.5 — ISV Matcher."""

import pytest
from src.isv.matcher import match_isvs_to_company, ISVMatch
from src.contacts.linker import link_contacts_to_news, SIGNAL_FA_ROUTING
from src.contacts.resolver import ResolvedContact


@pytest.mark.asyncio
async def test_match_isvs_returns_list():
    results = await match_isvs_to_company(
        company_name="Acme Corp",
        industry="Manufacturing",
        company_priorities=["Digital transformation"],
        tech_stack=["AWS", "SAP"],
        platform_vendor="google",
        sales_motion="wedge",
    )
    assert isinstance(results, list)


def test_link_contacts_to_news_sorts_by_relevance():
    contacts = [
        ResolvedContact(name="Alice", title="CTO", functional_area="Engineering", role_type="decision_maker"),
        ResolvedContact(name="Bob", title="Analyst", functional_area="Finance", role_type="champion"),
    ]
    matches = link_contacts_to_news(
        contacts=contacts,
        signal_type="tech_initiative",
        news_headline="Acme launches AI platform",
        platform_vendor="google",
        platform_products=["Vertex AI"],
    )
    assert len(matches) == 2
    # Engineering/decision_maker should rank higher for tech_initiative
    assert matches[0].contact.name == "Alice"
    assert matches[0].relevance_score > matches[1].relevance_score


def test_signal_fa_routing_covers_key_signals():
    for signal in ["earnings", "product_launch", "tech_initiative", "leadership_change"]:
        assert signal in SIGNAL_FA_ROUTING
        assert len(SIGNAL_FA_ROUTING[signal]) > 0
