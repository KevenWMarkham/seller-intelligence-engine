"""Layer 6 — Multi-channel notifier.

Thresholds (from config/scoring.yaml):
- Priority >= 80: Immediate Slack DM
- Priority 50-79: Morning digest email
- Priority < 50: Dashboard only
"""

import logging
from pathlib import Path

import yaml

from src.core.settings import settings

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "scoring.yaml"


def _load_thresholds() -> dict:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f).get("thresholds", {})


async def notify_seller(
    seller_id: str,
    task_id: int,
    company_name: str,
    contact_name: str,
    priority_score: int,
    brief_summary: str,
) -> None:
    """
    Send task notification to the seller via the appropriate channel.

    Args:
        seller_id: Seller identifier (Slack user ID or email).
        task_id: Task identifier.
        company_name: Target company name.
        contact_name: Contact's name.
        priority_score: Task priority 1-100.
        brief_summary: One-sentence brief summary.
    """
    thresholds = _load_thresholds()
    slack_threshold = thresholds.get("slack_immediate", 80)
    email_threshold = thresholds.get("email_digest", 50)

    if priority_score >= slack_threshold:
        await _send_slack_dm(seller_id, task_id, company_name, contact_name, priority_score, brief_summary)
    elif priority_score >= email_threshold:
        logger.info("Task %d queued for morning digest email (priority=%d)", task_id, priority_score)
    else:
        logger.debug("Task %d below notification threshold, dashboard only", task_id)


async def _send_slack_dm(
    seller_id: str,
    task_id: int,
    company_name: str,
    contact_name: str,
    priority_score: int,
    brief_summary: str,
) -> None:
    """Send an immediate Slack DM for high-priority tasks."""
    if not settings.slack_bot_token:
        logger.debug("Slack bot token not configured, skipping Slack DM")
        return

    # TODO: Phase 12 — slack_sdk WebClient.chat_postMessage
    logger.info(
        "Sending Slack DM to seller=%s for task=%d company=%s priority=%d",
        seller_id, task_id, company_name, priority_score,
    )
