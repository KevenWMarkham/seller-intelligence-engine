"""Tests for Layer 5 — AI Sales Coach."""

import pytest
from src.coaching.readiness import calculate_readiness, ReadinessScore


def test_calculate_readiness_above_threshold():
    score = calculate_readiness(
        product_knowledge=8,
        contact_knowledge=8,
        objection_handling=9,
        conversation_flow=7,
        confidence=8,
    )
    assert isinstance(score, ReadinessScore)
    assert score.is_ready is True
    assert score.overall >= 7.0
    assert len(score.areas_to_practice) == 0


def test_calculate_readiness_below_threshold():
    score = calculate_readiness(
        product_knowledge=5,
        contact_knowledge=4,
        objection_handling=6,
        conversation_flow=5,
        confidence=4,
    )
    assert score.is_ready is False
    assert score.overall < 7.0
    assert len(score.areas_to_practice) > 0


def test_calculate_readiness_areas_flagged():
    score = calculate_readiness(
        product_knowledge=9,
        contact_knowledge=9,
        objection_handling=4,  # Below threshold
        conversation_flow=9,
        confidence=9,
    )
    assert "objection_handling" in score.areas_to_practice
    assert "product_knowledge" not in score.areas_to_practice


def test_readiness_overall_is_average():
    score = calculate_readiness(8, 6, 7, 9, 5)
    expected = (8 + 6 + 7 + 9 + 5) / 5
    assert abs(score.overall - expected) < 0.01
