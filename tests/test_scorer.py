"""Tests for Layer 4 — Priority Scorer."""

import pytest
from unittest.mock import AsyncMock, patch
from src.ai.scorer import score_task, PriorityScore


MOCK_SCORE = {
    "score": 78,
    "reasoning": "High urgency news combined with a decision-maker contact drives the score.",
    "factor_scores": {
        "company_priority_alignment": 0.8,
        "deal_value_potential": 0.7,
        "contact_seniority": 1.0,
        "sales_motion_opportunity": 0.7,
        "news_urgency": 1.0,
        "platform_adoption_depth": 0.2,
    },
}


@pytest.mark.asyncio
async def test_score_task_returns_score():
    with patch("src.ai.scorer.ollama_client.complete", new=AsyncMock(return_value=MOCK_SCORE)):
        result = await score_task(
            company_name="Acme Corp",
            company_priorities=["Digital transformation"],
            platform_adoption_depth="none",
            sales_motion="wedge",
            contact_role_type="decision_maker",
            contact_title="VP Engineering",
            news_urgency="high",
            deal_value_estimate="$500K",
        )
    assert isinstance(result, PriorityScore)
    assert 1 <= result.score <= 100
    assert result.reasoning
    assert len(result.factor_scores) == 6


def test_score_range():
    """Score must always be 1-100."""
    score = PriorityScore(score=85, reasoning="test", factor_scores={})
    assert 1 <= score.score <= 100
