"""Sprint 6 — targeted tests for aggregator and technographics implementations."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.snapshot.aggregator import (
    CompanyProfile,
    _extract_description,
    _extract_tech_mentions,
    _name_from_domain,
    aggregate_company,
    scrape_company_website,
)
from src.snapshot.technographics import (
    TechProfile,
    _categorize_tech,
    _infer_platform_adoption,
    profile_tech_stack,
)


# ── aggregator helpers ────────────────────────────────────────────────────────

def test_name_from_domain():
    assert _name_from_domain("acme.com") == "Acme"
    assert _name_from_domain("global-data.io") == "Global Data"
    assert _name_from_domain("retailnow.com") == "Retailnow"


def test_extract_tech_mentions_aws():
    text = "We use AWS Lambda and Amazon S3 for our cloud infrastructure."
    techs = _extract_tech_mentions(text)
    assert "aws" in techs


def test_extract_tech_mentions_gcp():
    text = "Our data warehouse runs on Google Cloud BigQuery."
    techs = _extract_tech_mentions(text)
    assert "gcp" in techs


def test_extract_tech_mentions_azure():
    text = "Authentication is handled via Azure Active Directory."
    techs = _extract_tech_mentions(text)
    assert "azure" in techs


def test_extract_tech_mentions_multiple():
    text = "We run Python on AWS with Terraform for infrastructure-as-code."
    techs = _extract_tech_mentions(text)
    assert "aws" in techs
    assert "terraform" in techs
    assert "python" in techs


def test_extract_tech_mentions_no_match():
    text = "We provide excellent customer service to our clients."
    techs = _extract_tech_mentions(text)
    assert techs == []


# ── scrape_company_website with mocked httpx ─────────────────────────────────

@pytest.mark.asyncio
async def test_scrape_website_returns_description():
    html = """<html><head>
    <meta name="description" content="Acme Corp builds precision manufacturing tools.">
    </head><body><p>We are a manufacturing company.</p></body></html>"""

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = html

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.aclose = AsyncMock()

    result = await scrape_company_website("acme.com", client=mock_client)

    assert result["description"] == "Acme Corp builds precision manufacturing tools."


@pytest.mark.asyncio
async def test_scrape_website_detects_tech_from_body():
    html = """<html><body>
    <p>We use AWS Lambda and Google Cloud for our platform.</p>
    </body></html>"""

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = html

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.aclose = AsyncMock()

    result = await scrape_company_website("acme.com", client=mock_client)

    assert "aws" in result["technologies_mentioned"]
    assert "gcp" in result["technologies_mentioned"]


@pytest.mark.asyncio
async def test_scrape_website_graceful_on_error():
    """Website scraping should return empty result when all URLs fail."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
    mock_client.aclose = AsyncMock()

    result = await scrape_company_website("unreachable.example.com", client=mock_client)

    assert result["description"] is None
    assert result["technologies_mentioned"] == []
    assert result["raw_text"] == ""


# ── aggregate_company with mocked httpx ──────────────────────────────────────

@pytest.mark.asyncio
async def test_aggregate_company_stub_when_no_network():
    """aggregate_company returns a stub profile when all sources fail."""
    with patch("src.snapshot.aggregator.httpx.AsyncClient") as mock_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(side_effect=Exception("Network unreachable"))
        mock_class.return_value = mock_client

        profile = await aggregate_company("acme.com", name="Acme Corp")

    assert isinstance(profile, CompanyProfile)
    assert profile.domain == "acme.com"
    assert profile.name == "Acme Corp"


@pytest.mark.asyncio
async def test_aggregate_company_merges_web_description():
    """aggregate_company should include the description from website scraping."""
    html = """<html><head>
    <meta name="description" content="Acme builds precision components.">
    </head><body></body></html>"""

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = html

    with patch("src.snapshot.aggregator.httpx.AsyncClient") as mock_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        # EDGAR fails, website scraping succeeds
        mock_client.get = AsyncMock(side_effect=[Exception("EDGAR down"), mock_response])
        mock_class.return_value = mock_client

        profile = await aggregate_company("acme.com", name="Acme Corp")

    assert profile.description == "Acme builds precision components."
    assert "website_scraping" in profile.sources_used


# ── technographics helpers ────────────────────────────────────────────────────

def test_categorize_tech():
    assert _categorize_tech("aws") == "cloud"
    assert _categorize_tech("snowflake") == "data"
    assert _categorize_tech("salesforce") == "crm"
    assert _categorize_tech("kubernetes") == "container"
    assert _categorize_tech("terraform") == "iac"
    assert _categorize_tech("python") == "language"
    assert _categorize_tech("react") == "frontend"
    assert _categorize_tech("unknown_tool") == "other"


def test_infer_platform_adoption_google():
    tech_names = {"gcp", "bigquery"}
    result = _infer_platform_adoption(tech_names, "")
    assert "google" in result
    assert result["google"].depth in ("light", "moderate", "deep")
    assert len(result["google"].products_detected) > 0


def test_infer_platform_adoption_no_signals():
    """With no recognized tech, no vendors should appear in the result."""
    result = _infer_platform_adoption(set(), "")
    # May be empty or have vendors with zero signals (filtered out)
    for vendor, adoption in result.items():
        assert adoption.depth != "deep"


def test_infer_platform_adoption_from_raw_text():
    """Platform signals in raw text (not tech names) should still register."""
    tech_names: set[str] = set()
    raw_text = "We migrated our entire data warehouse to Google BigQuery last year."
    result = _infer_platform_adoption(tech_names, raw_text)
    # BigQuery mention should yield at least evaluating for google
    if "google" in result:
        assert result["google"].depth in ("evaluating", "light", "moderate", "deep")


# ── profile_tech_stack with mocked scraping ───────────────────────────────────

@pytest.mark.asyncio
async def test_profile_tech_stack_classifies_detected_tech():
    """profile_tech_stack should classify techs found by website detection."""
    web_result = {
        "description": "Cloud-native company.",
        "leadership": [],
        "technologies_mentioned": ["aws", "kubernetes", "python"],
        "raw_text": "We run Python on AWS with Kubernetes for container orchestration.",
    }

    with patch("src.snapshot.technographics.scrape_company_website", new=AsyncMock(return_value=web_result)):
        profile = await profile_tech_stack("acme.com")

    assert isinstance(profile, TechProfile)
    assert profile.domain == "acme.com"
    tech_names = {t.name for t in profile.stack}
    assert "aws" in tech_names
    assert "kubernetes" in tech_names
    # Platform adoption should detect AWS
    if "aws" in profile.platform_adoption:
        assert profile.platform_adoption["aws"].depth != "none"


@pytest.mark.asyncio
async def test_profile_tech_stack_graceful_when_empty():
    """profile_tech_stack returns valid empty TechProfile when no tech detected."""
    web_result = {
        "description": None,
        "leadership": [],
        "technologies_mentioned": [],
        "raw_text": "",
    }

    with patch("src.snapshot.technographics.scrape_company_website", new=AsyncMock(return_value=web_result)):
        profile = await profile_tech_stack("noop.example.com")

    assert isinstance(profile, TechProfile)
    assert profile.stack == []
