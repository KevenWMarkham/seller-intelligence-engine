"""Tests for Phase 3 — News & Signal Ingestion."""

import hashlib
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ingestion.news import (
    NewsCollector,
    _classify_signal_type,
    _dedup_by_minhash,
    _hash_url,
    _minhash_text,
    _score_platform_relevance,
)


# ── URL hashing ───────────────────────────────────────────────────────────


def test_hash_url_is_deterministic():
    url = "https://example.com/article/123"
    assert _hash_url(url) == _hash_url(url)


def test_hash_url_different_urls():
    assert _hash_url("https://a.com") != _hash_url("https://b.com")


def test_hash_url_length():
    assert len(_hash_url("https://example.com")) == 32


# ── Signal type classification ────────────────────────────────────────────


def test_classify_earnings():
    assert _classify_signal_type("Company reports Q3 earnings beat", "") == "earnings"


def test_classify_leadership_change():
    assert _classify_signal_type("CEO resigns from company", "") == "leadership_change"


def test_classify_m_and_a():
    assert _classify_signal_type("Corp acquires startup for $1B", "") == "m_and_a"


def test_classify_product_launch():
    assert _classify_signal_type("Company launches new AI platform", "") == "product_launch"


def test_classify_partnership():
    assert _classify_signal_type("Two firms announce strategic partnership", "") == "partnership"


def test_classify_default():
    assert _classify_signal_type("General tech industry news", "") == "tech_initiative"


# ── Platform relevance scoring ────────────────────────────────────────────


def test_score_relevance_high():
    keywords = ["google cloud", "bigquery", "vertex ai"]
    score = _score_platform_relevance("Google Cloud announces new BigQuery features", "", keywords)
    assert score > 0.5


def test_score_relevance_zero():
    keywords = ["google cloud", "gcp"]
    score = _score_platform_relevance("Local bakery wins award", "", keywords)
    assert score == 0.0


def test_score_relevance_capped_at_one():
    keywords = ["aws", "amazon", "cloud", "ec2", "s3"]
    score = _score_platform_relevance("AWS Amazon EC2 S3 cloud services", "", keywords)
    assert score <= 1.0


# ── MinHash deduplication ─────────────────────────────────────────────────


def test_dedup_removes_near_duplicates():
    items = [
        {"url_hash": "aaa", "headline": "Google Cloud announces BigQuery updates for 2026", "body": ""},
        {"url_hash": "bbb", "headline": "Google Cloud announces BigQuery updates for 2026", "body": ""},  # exact dup
        {"url_hash": "ccc", "headline": "Tesla reports record Q3 earnings", "body": ""},
    ]
    result = _dedup_by_minhash(items)
    assert len(result) == 2  # duplicate removed


def test_dedup_preserves_unique():
    items = [
        {"url_hash": "aaa", "headline": "Google Cloud AI platform launch", "body": ""},
        {"url_hash": "bbb", "headline": "AWS announces new EC2 instance types", "body": ""},
        {"url_hash": "ccc", "headline": "Microsoft Azure expands regions", "body": ""},
    ]
    result = _dedup_by_minhash(items)
    assert len(result) == 3


# ── NewsCollector DB integration ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_collector_stores_new_items():
    """NewsCollector.collect() stores items that don't exist in DB."""
    mock_session = MagicMock()
    mock_session.scalar = AsyncMock(return_value=None)  # simulate no existing items
    mock_session.commit = AsyncMock()

    fake_item = {
        "url_hash": "abc123",
        "headline": "Test headline",
        "body": "Test body",
        "source": "TestFeed",
        "url": "https://example.com/test",
        "published_at": None,
        "signal_type": "tech_initiative",
        "platform_relevance": 0.5,
    }

    with patch("src.ingestion.news.collect_rss_feeds", new_callable=AsyncMock) as mock_rss, \
         patch("src.ingestion.news.collect_newsapi", new_callable=AsyncMock) as mock_api, \
         patch("src.ingestion.news.collect_sec_edgar", new_callable=AsyncMock) as mock_edgar:

        mock_rss.return_value = [fake_item]
        mock_api.return_value = []
        mock_edgar.return_value = []

        collector = NewsCollector()
        count = await collector.collect(mock_session)

    assert count == 1
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_collector_skips_existing_items():
    """NewsCollector.collect() skips items already in DB."""
    mock_session = MagicMock()
    mock_session.scalar = AsyncMock(return_value=MagicMock())  # simulate existing item
    mock_session.commit = AsyncMock()

    fake_item = {
        "url_hash": "existing_hash",
        "headline": "Existing headline",
        "body": "",
        "source": "Feed",
        "url": "https://example.com/existing",
        "published_at": None,
        "signal_type": "earnings",
        "platform_relevance": 0.0,
    }

    with patch("src.ingestion.news.collect_rss_feeds", new_callable=AsyncMock) as mock_rss, \
         patch("src.ingestion.news.collect_newsapi", new_callable=AsyncMock) as mock_api, \
         patch("src.ingestion.news.collect_sec_edgar", new_callable=AsyncMock) as mock_edgar:

        mock_rss.return_value = [fake_item]
        mock_api.return_value = []
        mock_edgar.return_value = []

        collector = NewsCollector()
        count = await collector.collect(mock_session)

    assert count == 0
    mock_session.add.assert_not_called()
