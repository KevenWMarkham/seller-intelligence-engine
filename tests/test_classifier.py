"""Tests for Layer 4 — News Relevance Classifier."""

import pytest
from unittest.mock import AsyncMock, patch
from src.ai.classifier import classify_news, NewsClassification


@pytest.mark.asyncio
async def test_classify_news_returns_classification():
    mock_response = {
        "relevance_score": 0.9,
        "urgency": "high",
        "signal_type": "tech_initiative",
        "opportunity_type": "new_conversation",
        "companies_mentioned": ["Acme Corp"],
        "summary": "Acme Corp announced a digital transformation initiative relevant to Google Cloud.",
    }
    with patch("src.ai.classifier.ollama_client.complete", new=AsyncMock(return_value=mock_response)):
        result = await classify_news(
            headline="Acme Corp launches digital transformation program",
            body="Acme Corp announced a $50M digital transformation initiative.",
            platform_vendor="google",
            watched_companies=["Acme Corp"],
        )
    assert isinstance(result, NewsClassification)
    assert result.relevance_score == 0.9
    assert result.urgency == "high"
    assert "Acme Corp" in result.companies_mentioned


@pytest.mark.asyncio
async def test_classify_news_truncates_body():
    """Body longer than 2000 chars should be silently truncated before calling Ollama."""
    long_body = "x" * 5000
    mock_response = {
        "relevance_score": 0.1,
        "urgency": "low",
        "signal_type": "other",
        "opportunity_type": "relationship_deepener",
        "companies_mentioned": [],
        "summary": "No relevance.",
    }
    with patch("src.ai.classifier.ollama_client.complete", new=AsyncMock(return_value=mock_response)) as mock_call:
        await classify_news("Test headline", long_body, "google", [])
        called_prompt = mock_call.call_args[0][0]
        assert len(called_prompt) < len(long_body)
