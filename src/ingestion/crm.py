"""Layer 2 — CRM pipeline sync.

Supports: Salesforce, HubSpot.
Pulls: Active opportunities, account tiers, deal stages, seller assignments.
"""

import logging

from pydantic import BaseModel

from src.core.settings import settings

logger = logging.getLogger(__name__)


class CRMOpportunity(BaseModel):
    crm_id: str
    account_name: str
    account_domain: str | None = None
    seller_id: str
    stage: str
    amount: float | None = None
    close_date: str | None = None
    last_activity_date: str | None = None


async def sync_opportunities() -> list[CRMOpportunity]:
    """
    Sync active opportunities from the configured CRM provider.

    Returns:
        List of CRMOpportunity objects for enrichment.
    """
    provider = settings.sf_instance_url and "salesforce" or (settings.hubspot_api_key and "hubspot")
    if not provider:
        logger.debug("No CRM credentials configured, skipping sync")
        return []

    if provider == "salesforce":
        return await _sync_salesforce()
    return await _sync_hubspot()


async def _sync_salesforce() -> list[CRMOpportunity]:
    """Pull opportunities from Salesforce via REST API."""
    # TODO: Phase 3 — OAuth2 + SOQL query
    logger.info("Syncing Salesforce opportunities")
    return []


async def _sync_hubspot() -> list[CRMOpportunity]:
    """Pull deals from HubSpot via API."""
    # TODO: Phase 3 — HubSpot Deals API
    logger.info("Syncing HubSpot deals")
    return []
