"""Tests for Layer 4 — AI pipeline orchestration."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ai.pipeline import run_ai_pipeline, _extract_priorities, _adoption_depth
from src.ai.classifier import NewsClassification
from src.ai.brief_generator import ConversationBrief, PredictedObjection
from src.ai.scorer import PriorityScore
from src.models.company import Company
from src.models.contact import Contact
from src.models.news import NewsItem
from src.models.task import SellerTask


# ── Fixtures ──────────────────────────────────────────────────────────────

def make_company(id=1, name="Acme Corp", domain="acme.com", sales_motion="wedge", revenue="$500M"):
    c = MagicMock(spec=Company)
    c.id = id
    c.name = name
    c.domain = domain
    c.sales_motion = sales_motion
    c.revenue = revenue
    c.priorities_json = None
    return c


def make_contact(id=1, company_id=1):
    ct = MagicMock(spec=Contact)
    ct.id = id
    ct.company_id = company_id
    ct.name = "Michael Torres"
    ct.title = "VP Engineering"
    ct.functional_area = "Engineering"
    ct.role_type = "decision_maker"
    ct.platform_relevance_score = 0.9
    return ct


def make_news(id=1, relevance_score=None, headline="Acme launches digital initiative"):
    n = MagicMock(spec=NewsItem)
    n.id = id
    n.headline = headline
    n.body = "Acme Corp announced a $50M transformation program."
    n.relevance_score = relevance_score
    n.urgency = None
    n.signal_type = None
    n.opportunity_type = None
    n.companies_mentioned_json = None
    return n


MOCK_CLASSIFICATION = NewsClassification(
    relevance_score=0.9,
    urgency="high",
    signal_type="tech_initiative",
    opportunity_type="new_conversation",
    companies_mentioned=["Acme Corp"],
    summary="Acme Corp announced a major digital transformation.",
)

MOCK_BRIEF = ConversationBrief(
    opener="I saw that Acme Corp recently launched a digital transformation initiative.",
    why_it_matters="This impacts your engineering roadmap directly.",
    solution_connection="Google Cloud's Vertex AI maps well to this need.",
    isv_recommendation="Looker for analytics",
    suggested_ask="Can we set up a 30-minute call next week?",
    predicted_objections=[
        PredictedObjection(
            objection="We're committed to our current vendor",
            suggested_response="We just need one workload to prove value.",
        )
    ],
)

MOCK_SCORE = PriorityScore(
    score=82,
    reasoning="High urgency, decision maker engaged, strong motion match.",
    factor_scores={
        "company_priority_alignment": 0.9,
        "deal_value_potential": 0.8,
        "contact_seniority": 0.85,
        "sales_motion_opportunity": 0.9,
        "news_urgency": 0.95,
        "platform_adoption_depth": 0.5,
    },
)


# ── Helper functions ───────────────────────────────────────────────────────

def test_extract_priorities_with_json():
    company = make_company()
    company.priorities_json = json.dumps(["AI adoption", "Cost reduction"])
    result = _extract_priorities(company)
    assert result == ["AI adoption", "Cost reduction"]


def test_extract_priorities_fallback():
    company = make_company(name="Testco")
    company.priorities_json = None
    result = _extract_priorities(company)
    assert len(result) == 3
    assert "Testco" in result[0]


def test_adoption_depth_mapping():
    assert _adoption_depth("wedge") == "none"
    assert _adoption_depth("expand") == "moderate"
    assert _adoption_depth("displace") == "none"
    assert _adoption_depth(None) == "none"  # None falls back to "new" motion


# ── Pipeline tests ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pipeline_creates_task_for_relevant_news():
    """Pipeline creates one SellerTask when Qwen classifies news as relevant."""
    company = make_company()
    contact = make_contact()
    news = make_news()

    session = MagicMock()
    session.commit = AsyncMock()
    session.add = MagicMock()

    def make_scalars_result(items):
        result = MagicMock()
        result.scalars.return_value.all.return_value = items
        result.scalars.return_value.first.return_value = items[0] if items else None
        result.scalar_one_or_none.return_value = None
        result.fetchall.return_value = []
        return result

    execute_calls = [
        make_scalars_result([company]),   # select(Company)
        make_scalars_result([news]),      # select(NewsItem) unclassified
        make_scalars_result([]),          # existing task IDs for news_item (fallback)
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # existing task check
        make_scalars_result([contact]),   # select(Contact)
    ]
    session.execute = AsyncMock(side_effect=execute_calls)

    with (
        patch("src.ai.pipeline._load_active_vendor", return_value="google"),
        patch("src.ai.pipeline._load_platform_products", return_value=["BigQuery", "Vertex AI"]),
        patch("src.ai.pipeline.classifier.classify_news", new=AsyncMock(return_value=MOCK_CLASSIFICATION)),
        patch("src.ai.pipeline.brief_generator.generate_brief", new=AsyncMock(return_value=MOCK_BRIEF)),
        patch("src.ai.pipeline.scorer.score_task", new=AsyncMock(return_value=MOCK_SCORE)),
    ):
        count = await run_ai_pipeline(session)

    assert count == 1
    session.add.assert_called_once()
    added_task = session.add.call_args[0][0]
    assert isinstance(added_task, SellerTask)
    assert added_task.priority_score == 82
    brief_data = json.loads(added_task.conversation_brief_json)
    assert "opener" in brief_data
    assert len(brief_data["opener"]) > 0


@pytest.mark.asyncio
async def test_pipeline_skips_low_relevance_news():
    """Pipeline skips news classified below RELEVANCE_THRESHOLD."""
    company = make_company()
    news = make_news()

    low_relevance_classification = NewsClassification(
        relevance_score=0.1,
        urgency="low",
        signal_type="other",
        opportunity_type="relationship_deepener",
        companies_mentioned=[],
        summary="Not relevant.",
    )

    session = MagicMock()
    session.commit = AsyncMock()
    session.add = MagicMock()

    def make_scalars_result(items):
        result = MagicMock()
        result.scalars.return_value.all.return_value = items
        return result

    execute_calls = [
        make_scalars_result([company]),
        make_scalars_result([news]),
    ]
    session.execute = AsyncMock(side_effect=execute_calls)

    with (
        patch("src.ai.pipeline._load_active_vendor", return_value="google"),
        patch("src.ai.pipeline._load_platform_products", return_value=[]),
        patch("src.ai.pipeline.classifier.classify_news", new=AsyncMock(return_value=low_relevance_classification)),
        patch("src.ai.pipeline.brief_generator.generate_brief", new=AsyncMock()) as mock_brief,
        patch("src.ai.pipeline.scorer.score_task", new=AsyncMock()) as mock_score,
    ):
        count = await run_ai_pipeline(session)

    assert count == 0
    mock_brief.assert_not_called()
    mock_score.assert_not_called()


@pytest.mark.asyncio
async def test_pipeline_returns_zero_when_no_companies():
    """Pipeline exits early if no companies exist in DB."""
    session = MagicMock()
    session.commit = AsyncMock()

    empty_result = MagicMock()
    empty_result.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=empty_result)

    with (
        patch("src.ai.pipeline._load_active_vendor", return_value="google"),
        patch("src.ai.pipeline._load_platform_products", return_value=[]),
    ):
        count = await run_ai_pipeline(session)

    assert count == 0


@pytest.mark.asyncio
async def test_pipeline_returns_zero_when_no_unclassified_news():
    """Pipeline returns 0 when all news is already classified."""
    company = make_company()

    session = MagicMock()
    session.commit = AsyncMock()

    def make_scalars_result(items):
        result = MagicMock()
        result.scalars.return_value.all.return_value = items
        return result

    execute_calls = [
        make_scalars_result([company]),
        make_scalars_result([]),  # no unclassified news
    ]
    session.execute = AsyncMock(side_effect=execute_calls)

    with (
        patch("src.ai.pipeline._load_active_vendor", return_value="google"),
        patch("src.ai.pipeline._load_platform_products", return_value=[]),
    ):
        count = await run_ai_pipeline(session)

    assert count == 0


@pytest.mark.asyncio
async def test_pipeline_skips_duplicate_tasks():
    """Pipeline does not create a second task for the same news+company pair."""
    company = make_company()
    contact = make_contact()
    news = make_news()

    existing_task = MagicMock(spec=SellerTask)

    session = MagicMock()
    session.commit = AsyncMock()
    session.add = MagicMock()

    def make_scalars_result(items):
        result = MagicMock()
        result.scalars.return_value.all.return_value = items
        result.scalars.return_value.first.return_value = items[0] if items else None
        result.fetchall.return_value = []
        return result

    execute_calls = [
        make_scalars_result([company]),
        make_scalars_result([news]),
        make_scalars_result([]),          # existing task IDs
        MagicMock(scalar_one_or_none=MagicMock(return_value=existing_task)),  # task exists!
    ]
    session.execute = AsyncMock(side_effect=execute_calls)

    with (
        patch("src.ai.pipeline._load_active_vendor", return_value="google"),
        patch("src.ai.pipeline._load_platform_products", return_value=[]),
        patch("src.ai.pipeline.classifier.classify_news", new=AsyncMock(return_value=MOCK_CLASSIFICATION)),
        patch("src.ai.pipeline.brief_generator.generate_brief", new=AsyncMock()) as mock_brief,
    ):
        count = await run_ai_pipeline(session)

    assert count == 0
    mock_brief.assert_not_called()


@pytest.mark.asyncio
async def test_pipeline_continues_on_error():
    """Pipeline logs errors and continues processing remaining items."""
    company = make_company()
    news1 = make_news(id=1, headline="First news item")
    news2 = make_news(id=2, headline="Second news item")

    session = MagicMock()
    session.commit = AsyncMock()
    session.add = MagicMock()

    def make_scalars_result(items):
        result = MagicMock()
        result.scalars.return_value.all.return_value = items
        result.scalars.return_value.first.return_value = items[0] if items else None
        result.scalar_one_or_none.return_value = None
        result.fetchall.return_value = []
        return result

    call_count = 0

    async def classify_side_effect(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("Simulated Ollama error")
        return MOCK_CLASSIFICATION

    execute_calls = [
        make_scalars_result([company]),
        make_scalars_result([news1, news2]),
        make_scalars_result([]),
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        make_scalars_result([make_contact()]),
    ]
    session.execute = AsyncMock(side_effect=execute_calls)

    with (
        patch("src.ai.pipeline._load_active_vendor", return_value="google"),
        patch("src.ai.pipeline._load_platform_products", return_value=[]),
        patch("src.ai.pipeline.classifier.classify_news", new=AsyncMock(side_effect=classify_side_effect)),
        patch("src.ai.pipeline.brief_generator.generate_brief", new=AsyncMock(return_value=MOCK_BRIEF)),
        patch("src.ai.pipeline.scorer.score_task", new=AsyncMock(return_value=MOCK_SCORE)),
    ):
        count = await run_ai_pipeline(session)

    # Second news item should still produce a task despite first failing
    assert count == 1
