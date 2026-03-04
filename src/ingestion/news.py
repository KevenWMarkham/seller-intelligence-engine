"""Layer 2 — News & signal ingestion.

Sources: RSS/Atom feeds, NewsAPI, SEC EDGAR.
Deduplication: URL hash + MinHash for near-duplicates.
Schedule: Poll every 15 minutes (configurable via config/ingestion.yaml).
"""

import hashlib
import logging
from datetime import datetime
from pathlib import Path

import feedparser
import httpx
import yaml
from pydantic import BaseModel

from src.core.settings import settings

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "ingestion.yaml"


class RawNewsItem(BaseModel):
    url_hash: str
    headline: str
    body: str | None = None
    source: str | None = None
    url: str
    published_at: datetime | None = None


def _hash_url(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:32]


def _load_config() -> dict:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)


async def collect_rss_feeds() -> list[RawNewsItem]:
    """
    Collect articles from all configured RSS/Atom feeds.

    Returns deduplicated list of RawNewsItem.
    """
    config = _load_config()
    items: list[RawNewsItem] = []

    for feed_cfg in config.get("news", {}).get("sources", {}).get("rss", []):
        url = feed_cfg["url"]
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:
                item = RawNewsItem(
                    url_hash=_hash_url(entry.get("link", "")),
                    headline=entry.get("title", ""),
                    body=entry.get("summary", ""),
                    source=feed.feed.get("title", url),
                    url=entry.get("link", ""),
                    published_at=_parse_date(entry.get("published")),
                )
                items.append(item)
        except Exception as e:
            logger.warning("Failed to fetch RSS feed %s: %s", url, e)

    logger.info("Collected %d items from RSS feeds", len(items))
    return items


async def collect_newsapi(keywords: list[str]) -> list[RawNewsItem]:
    """
    Collect articles from NewsAPI for given keywords.

    Requires NEWSAPI_KEY environment variable.
    """
    if not settings.newsapi_key:
        logger.debug("NewsAPI key not configured, skipping")
        return []

    # TODO: Phase 3 — implement NewsAPI pagination and full collection
    return []


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        import email.utils
        return datetime(*email.utils.parsedate(date_str)[:6])
    except Exception:
        return None
