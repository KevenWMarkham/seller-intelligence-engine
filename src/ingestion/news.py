"""Layer 2 — News & signal ingestion.

Sources: RSS/Atom feeds, NewsAPI, SEC EDGAR.
Deduplication: URL hash (exact) + MinHash (near-duplicate, Jaccard ≥ 0.85).
Schedule: Poll every 15 minutes (configurable via config/ingestion.yaml).

Usage::

    collector = NewsCollector()
    await collector.collect(session)   # collect + dedup + write to DB
"""

import hashlib
import json
import logging
import re
from datetime import datetime
from pathlib import Path

import feedparser
import httpx
import yaml
from datasketch import MinHash, MinHashLSH
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.config import _load_active_vendor, _load_vendor_catalog
from src.core.settings import settings
from src.models.news import NewsItem

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "ingestion.yaml"

# Jaccard similarity threshold for near-duplicate detection
_MINHASH_THRESHOLD = 0.85
_MINHASH_NUM_PERM = 128

# Signal type keyword patterns (rule-based)
_SIGNAL_PATTERNS: list[tuple[str, list[str]]] = [
    ("earnings", ["earnings", "revenue", "quarterly", "fiscal", "q1", "q2", "q3", "q4", "profit", "loss", "guidance"]),
    ("leadership_change", ["ceo", "cto", "cfo", "coo", "appointed", "resigned", "departure", "steps down", "joins as", "new chief", "executive change"]),
    ("m_and_a", ["acquisition", "merger", "acquires", "acquired", "takeover", "deal", "buyout", "acquired by"]),
    ("product_launch", ["launches", "launch", "announces", "unveiled", "introduces", "new product", "general availability", "ga release"]),
    ("partnership", ["partnership", "partner", "alliance", "collaboration", "integrates", "integration", "joint"]),
    ("tech_initiative", ["cloud migration", "digital transformation", "ai initiative", "platform modernization", "cloud adoption", "data strategy"]),
]


# ── Helpers ───────────────────────────────────────────────────────────────


def _load_config() -> dict:
    with open(_CONFIG_PATH) as f:
        raw = f.read()
    # Simple ${VAR} substitution from environment
    import os
    raw = re.sub(r"\$\{(\w+)\}", lambda m: os.environ.get(m.group(1), ""), raw)
    return yaml.safe_load(raw)


def _hash_url(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:32]


def _minhash_text(text: str) -> MinHash:
    """Generate a MinHash signature for a text string."""
    m = MinHash(num_perm=_MINHASH_NUM_PERM)
    for word in re.findall(r"\w+", text.lower()):
        m.update(word.encode("utf8"))
    return m


def _classify_signal_type(headline: str, body: str) -> str:
    """Rule-based signal type classification."""
    text = (headline + " " + (body or "")).lower()
    for signal_type, keywords in _SIGNAL_PATTERNS:
        if any(kw in text for kw in keywords):
            return signal_type
    return "tech_initiative"


def _score_platform_relevance(headline: str, body: str, signal_keywords: list[str]) -> float:
    """Score 0.0–1.0 based on vendor keyword frequency in article text."""
    if not signal_keywords:
        return 0.0
    text = (headline + " " + (body or "")).lower()
    hits = sum(1 for kw in signal_keywords if kw.lower() in text)
    # Normalise: 3+ hits = 1.0, scale linearly
    return min(hits / 3.0, 1.0)


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        import email.utils
        parsed = email.utils.parsedate(date_str)
        if parsed:
            return datetime(*parsed[:6])
    except Exception:
        pass
    return None


# ── Collectors ────────────────────────────────────────────────────────────


async def collect_rss_feeds(signal_keywords: list[str]) -> list[dict]:
    """Collect articles from configured RSS/Atom feeds."""
    config = _load_config()
    items: list[dict] = []

    for feed_cfg in config.get("news", {}).get("sources", {}).get("rss", []):
        url = feed_cfg["url"]
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:
                link = entry.get("link", "")
                headline = entry.get("title", "").strip()
                body = entry.get("summary", "") or entry.get("content", [{}])[0].get("value", "") if entry.get("content") else entry.get("summary", "")
                if not headline or not link:
                    continue
                items.append({
                    "url_hash": _hash_url(link),
                    "headline": headline,
                    "body": body,
                    "source": feed.feed.get("title", url),
                    "url": link,
                    "published_at": _parse_date(entry.get("published")),
                    "signal_type": _classify_signal_type(headline, body or ""),
                    "platform_relevance": _score_platform_relevance(headline, body or "", signal_keywords),
                })
        except Exception as e:
            logger.warning("Failed to fetch RSS feed %s: %s", url, e)

    logger.info("Collected %d raw items from RSS feeds", len(items))
    return items


async def collect_newsapi(keywords: list[str], signal_keywords: list[str]) -> list[dict]:
    """Collect articles from NewsAPI (graceful degradation if key absent)."""
    if not settings.newsapi_key:
        logger.debug("NEWSAPI_KEY not set — skipping NewsAPI collection")
        return []

    items: list[dict] = []
    query = " OR ".join(f'"{kw}"' for kw in keywords[:5])  # max 5 to avoid overly long query

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": query,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 25,
                    "apiKey": settings.newsapi_key,
                },
            )
            if response.status_code != 200:
                logger.warning("NewsAPI returned %d: %s", response.status_code, response.text[:200])
                return []

            for article in response.json().get("articles", []):
                url = article.get("url", "")
                headline = article.get("title", "").strip()
                body = article.get("description", "") or ""
                if not headline or not url or url == "[Removed]":
                    continue
                published_str = article.get("publishedAt", "")
                published_at = None
                if published_str:
                    try:
                        published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                    except Exception:
                        pass
                items.append({
                    "url_hash": _hash_url(url),
                    "headline": headline,
                    "body": body,
                    "source": article.get("source", {}).get("name", "NewsAPI"),
                    "url": url,
                    "published_at": published_at,
                    "signal_type": _classify_signal_type(headline, body),
                    "platform_relevance": _score_platform_relevance(headline, body, signal_keywords),
                })
    except Exception as e:
        logger.warning("NewsAPI collection failed: %s", e)

    logger.info("Collected %d items from NewsAPI", len(items))
    return items


async def collect_sec_edgar(tickers: list[str], signal_keywords: list[str]) -> list[dict]:
    """Collect SEC EDGAR RSS feeds for tracked company tickers."""
    if not tickers:
        return []

    items: list[dict] = []
    edgar_rss = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=8-K&dateb=&owner=include&count=20&search_text=&output=atom"

    try:
        feed = feedparser.parse(edgar_rss)
        for entry in feed.entries[:10]:
            headline = entry.get("title", "").strip()
            link = entry.get("link", "")
            if not headline or not link:
                continue
            body = entry.get("summary", "")
            items.append({
                "url_hash": _hash_url(link),
                "headline": f"SEC Filing: {headline}",
                "body": body,
                "source": "SEC EDGAR",
                "url": link,
                "published_at": _parse_date(entry.get("published")),
                "signal_type": "earnings",
                "platform_relevance": _score_platform_relevance(headline, body, signal_keywords),
            })
    except Exception as e:
        logger.warning("SEC EDGAR collection failed: %s", e)

    logger.info("Collected %d items from SEC EDGAR", len(items))
    return items


# ── Deduplication ─────────────────────────────────────────────────────────


def _dedup_by_minhash(items: list[dict]) -> list[dict]:
    """Remove near-duplicate articles using MinHash LSH.

    Articles with Jaccard similarity ≥ 0.85 are considered duplicates;
    only the first occurrence is kept.
    """
    lsh = MinHashLSH(threshold=_MINHASH_THRESHOLD, num_perm=_MINHASH_NUM_PERM)
    unique: list[dict] = []

    for i, item in enumerate(items):
        text = item["headline"] + " " + (item.get("body") or "")
        mh = _minhash_text(text)
        key = f"item_{i}"
        try:
            result = lsh.query(mh)
            if result:
                logger.debug("Near-duplicate dropped: %s", item["headline"][:60])
                continue
            lsh.insert(key, mh)
            unique.append(item)
        except Exception:
            unique.append(item)

    logger.info("MinHash dedup: %d → %d items", len(items), len(unique))
    return unique


# ── NewsCollector ─────────────────────────────────────────────────────────


class NewsCollector:
    """Orchestrates news collection, deduplication, and DB persistence."""

    async def collect(self, session: AsyncSession) -> int:
        """Run full collection cycle. Returns count of new items stored."""
        config = _load_config()

        # Get current platform signal keywords for relevance scoring
        try:
            vendor = _load_active_vendor()
            catalog = _load_vendor_catalog(vendor)
            signal_keywords: list[str] = catalog.get("signal_keywords", [])
        except Exception:
            signal_keywords = []

        newsapi_keywords = config.get("news", {}).get("sources", {}).get("newsapi", {}).get("keywords", [])
        sec_tickers = config.get("news", {}).get("sources", {}).get("sec_edgar", {}).get("tracked_tickers", [])

        # Collect from all sources
        rss_items = await collect_rss_feeds(signal_keywords)
        api_items = await collect_newsapi(newsapi_keywords, signal_keywords)
        edgar_items = await collect_sec_edgar(sec_tickers, signal_keywords)

        all_items = rss_items + api_items + edgar_items

        # Near-duplicate removal
        all_items = _dedup_by_minhash(all_items)

        # URL-hash deduplication against DB
        stored = 0
        for item_data in all_items:
            exists = await session.scalar(
                select(NewsItem).where(NewsItem.url_hash == item_data["url_hash"])
            )
            if exists:
                continue
            news_item = NewsItem(**item_data)
            session.add(news_item)
            stored += 1

        await session.commit()
        logger.info("News collection complete: %d new items stored", stored)
        return stored
