"""Layer 5 — Confidence score & readiness gate.

Assesses seller readiness 1-10 across 5 dimensions.
Configurable threshold (default 7) — task cannot move to "ready" until met.
"""

import logging
from pathlib import Path

import yaml
from pydantic import BaseModel

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "scoring.yaml"


class ReadinessScore(BaseModel):
    product_knowledge: int  # 1-10
    contact_knowledge: int  # 1-10
    objection_handling: int  # 1-10
    conversation_flow: int  # 1-10
    confidence: int  # 1-10
    overall: float  # weighted average
    is_ready: bool  # overall >= threshold
    areas_to_practice: list[str]
    threshold: int


def _load_threshold() -> int:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f).get("readiness_gate", 7)


def calculate_readiness(
    product_knowledge: int,
    contact_knowledge: int,
    objection_handling: int,
    conversation_flow: int,
    confidence: int,
) -> ReadinessScore:
    """
    Calculate overall readiness score from 5 dimension scores.

    Args:
        product_knowledge: Score 1-10 for platform/product knowledge.
        contact_knowledge: Score 1-10 for contact/company knowledge.
        objection_handling: Score 1-10 for objection handling quality.
        conversation_flow: Score 1-10 for call flow and structure.
        confidence: Score 1-10 for delivery confidence.

    Returns:
        ReadinessScore with overall score and readiness gate result.
    """
    threshold = _load_threshold()
    scores = [product_knowledge, contact_knowledge, objection_handling, conversation_flow, confidence]
    overall = sum(scores) / len(scores)

    areas_to_practice = []
    dimension_names = ["product_knowledge", "contact_knowledge", "objection_handling", "conversation_flow", "confidence"]
    for name, score in zip(dimension_names, scores):
        if score < threshold:
            areas_to_practice.append(name)

    return ReadinessScore(
        product_knowledge=product_knowledge,
        contact_knowledge=contact_knowledge,
        objection_handling=objection_handling,
        conversation_flow=conversation_flow,
        confidence=confidence,
        overall=round(overall, 1),
        is_ready=overall >= threshold,
        areas_to_practice=areas_to_practice,
        threshold=threshold,
    )
