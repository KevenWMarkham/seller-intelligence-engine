"""Layer 2 — Social & executive signal monitor.

Sources: LinkedIn API / Proxycurl, X (Twitter) API v2.
Tracks FA lead activity — executive posts, company updates, platform mentions.
"""

import logging

from pydantic import BaseModel

from src.core.settings import settings

logger = logging.getLogger(__name__)


class SocialSignal(BaseModel):
    platform: str  # linkedin | twitter
    author_name: str
    author_title: str | None = None
    company: str | None = None
    content: str
    url: str | None = None
    signal_type: str | None = None  # platform_mention | leadership_update | thought_leadership
    published_at: str | None = None


async def monitor_linkedin_company(company_name: str, company_linkedin_id: str | None) -> list[SocialSignal]:
    """
    Monitor LinkedIn company page updates and executive posts.

    Args:
        company_name: Company name for reference.
        company_linkedin_id: LinkedIn company identifier.

    Returns:
        List of social signals from LinkedIn.
    """
    # TODO: Phase 8 — LinkedIn API / Proxycurl integration
    if not settings.linkedin_key:
        logger.debug("LinkedIn key not configured, skipping")
        return []
    return []


async def monitor_twitter_company(company_domain: str, tracked_handles: list[str]) -> list[SocialSignal]:
    """
    Monitor Twitter/X for company mentions and executive posts.

    Args:
        company_domain: Company domain for mention tracking.
        tracked_handles: List of executive Twitter handles to monitor.

    Returns:
        List of social signals from Twitter.
    """
    # TODO: Phase 8 — Twitter API v2 integration
    if not settings.twitter_bearer:
        logger.debug("Twitter bearer token not configured, skipping")
        return []
    return []
