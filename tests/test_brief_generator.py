"""Tests for Layer 4 — Conversation Brief Generator."""

import pytest
from unittest.mock import AsyncMock, patch
from src.ai.brief_generator import generate_brief, ConversationBrief


MOCK_BRIEF = {
    "opener": "I saw Acme Corp just announced a $50M digital transformation initiative.",
    "why_it_matters": "As VP Engineering, this initiative will land on your team.",
    "solution_connection": "Google Cloud's Vertex AI platform can accelerate your ML roadmap.",
    "isv_recommendation": "Consider Databricks on GCP for your data unification needs.",
    "suggested_ask": "Can we set up a 30-minute call next week to explore the data platform angle?",
    "predicted_objections": [
        {
            "objection": "We don't have budget right now",
            "suggested_response": "Understood. Given the transformation program, when would the budget cycle open up? I'd like to make sure you have the right information for your planning process.",
        }
    ],
}


@pytest.mark.asyncio
async def test_generate_brief_returns_brief():
    with patch("src.ai.brief_generator.ollama_client.complete", new=AsyncMock(return_value=MOCK_BRIEF)):
        result = await generate_brief(
            company_name="Acme Corp",
            contact_name="Michael Torres",
            contact_title="VP Engineering",
            functional_area="Engineering",
            news_headline="Acme Corp launches digital transformation",
            news_summary="$50M initiative announced",
            platform_vendor="google",
            sales_motion="wedge",
            company_priorities=["Digital transformation", "Cost reduction"],
            platform_products=["Vertex AI", "BigQuery"],
        )
    assert isinstance(result, ConversationBrief)
    assert result.opener
    assert len(result.predicted_objections) >= 1
    assert result.suggested_ask
