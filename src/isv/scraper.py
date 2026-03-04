"""Layer 1.5 — Marketplace scraper.

Scrapes: AWS Marketplace, Azure Marketplace/AppSource, Google Cloud Marketplace,
Salesforce AppExchange, ServiceNow Store.

Runs on a weekly schedule via APScheduler.
"""

import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)

MARKETPLACE_URLS = {
    "aws": "https://aws.amazon.com/marketplace",
    "azure": "https://azuremarketplace.microsoft.com",
    "gcp": "https://console.cloud.google.com/marketplace",
    "salesforce": "https://appexchange.salesforce.com",
    "servicenow": "https://store.servicenow.com",
}


class MarketplaceListing(BaseModel):
    isv_name: str
    solution_name: str
    marketplace: str
    description: str | None = None
    industries: list[str] = []
    capabilities: list[str] = []
    pricing_model: str | None = None
    listing_url: str | None = None
    co_sell_status: str | None = None


async def scrape_marketplace(marketplace: str) -> list[MarketplaceListing]:
    """
    Scrape ISV listings from a marketplace.

    Args:
        marketplace: One of aws | azure | gcp | salesforce | servicenow.

    Returns:
        List of MarketplaceListing objects.
    """
    # TODO: Phase 9 — BeautifulSoup scraping + pagination
    logger.info("Scraping %s marketplace", marketplace)
    return []


async def scrape_all_marketplaces() -> list[MarketplaceListing]:
    """Run scraping across all supported marketplaces."""
    results: list[MarketplaceListing] = []
    for marketplace in MARKETPLACE_URLS:
        listings = await scrape_marketplace(marketplace)
        results.extend(listings)
    logger.info("Scraped %d total ISV listings", len(results))
    return results
