"""Tests for Layer 1 — Company Snapshot Engine."""

import pytest
from src.snapshot.aggregator import aggregate_company, CompanyProfile
from src.snapshot.technographics import profile_tech_stack, TechProfile
from src.contacts.org_chart import classify_role_type


@pytest.mark.asyncio
async def test_aggregate_company_returns_profile():
    profile = await aggregate_company("acme.com")
    assert isinstance(profile, CompanyProfile)
    assert profile.domain == "acme.com"
    assert profile.name == "Acme"


@pytest.mark.asyncio
async def test_profile_tech_stack_returns_tech_profile():
    profile = await profile_tech_stack("acme.com")
    assert isinstance(profile, TechProfile)
    assert profile.domain == "acme.com"


def test_classify_role_type_decision_maker():
    assert classify_role_type("Chief Technology Officer") == "decision_maker"
    assert classify_role_type("CTO") == "decision_maker"
    assert classify_role_type("CEO") == "decision_maker"


def test_classify_role_type_influencer():
    assert classify_role_type("VP Engineering") == "influencer"
    assert classify_role_type("Director of IT") == "influencer"


def test_classify_role_type_champion():
    assert classify_role_type("Senior Software Engineer") == "champion"
    assert classify_role_type("Data Analyst") == "champion"
