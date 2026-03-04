"""Layer 1.5 — ISV catalog loader / marketplace scraper.

Primary path: load from config/isvs/{vendor}.yaml (static curated catalog).
Future path: real marketplace scraping via BeautifulSoup (requires headless browser
and rate-limit handling — stubs provided for AWS, Azure, GCP, Salesforce).

The catalog loader is the reliable fallback that makes the full ISV pipeline
work without external API keys or web scraping infrastructure.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import yaml
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.isv import ISVSolution

logger = logging.getLogger(__name__)

_CATALOG_DIR = Path(__file__).parent.parent.parent / "config" / "isvs"

MARKETPLACE_URLS = {
    "aws": "https://aws.amazon.com/marketplace",
    "azure": "https://azuremarketplace.microsoft.com",
    "gcp": "https://console.cloud.google.com/marketplace",
    "salesforce": "https://appexchange.salesforce.com",
    "servicenow": "https://store.servicenow.com",
}

# Map vendor key to catalog filename
_VENDOR_CATALOG_MAP: dict[str, str] = {
    "google": "google",
    "gcp": "google",
    "aws": "aws",
    "amazon": "aws",
    "microsoft": "microsoft",
    "azure": "microsoft",
}


class MarketplaceListing(BaseModel):
    isv_name: str
    solution_name: str
    marketplace: str
    description: str | None = None
    industries: list[str] = []
    capabilities: list[str] = []
    business_outcomes: list[str] = []
    processes_improved: list[str] = []
    kpis_impacted: list[str] = []
    primary_buyer: str | None = None
    pricing_model: str | None = None
    listing_url: str | None = None
    co_sell_status: str | None = None
    integration_depth: str | None = None
    cert_level: str | None = None


def load_catalog(vendor: str) -> list[MarketplaceListing]:
    """Load ISV catalog from config/isvs/{vendor}.yaml.

    Args:
        vendor: Platform vendor key (google, aws, microsoft, etc.)

    Returns:
        List of MarketplaceListing from the curated catalog.
    """
    catalog_key = _VENDOR_CATALOG_MAP.get(vendor.lower(), vendor.lower())
    path = _CATALOG_DIR / f"{catalog_key}.yaml"

    if not path.exists():
        logger.debug("No ISV catalog found for vendor=%s at %s", vendor, path)
        return []

    try:
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        isv_list = data.get("isvs", [])
        listings = []
        for item in isv_list:
            listing = MarketplaceListing(
                isv_name=item.get("name", ""),
                solution_name=item.get("name", ""),
                marketplace=item.get("marketplace", catalog_key),
                description=item.get("description"),
                industries=item.get("industries", []),
                capabilities=item.get("capabilities", []),
                business_outcomes=item.get("business_outcomes", []),
                processes_improved=item.get("processes_improved", []),
                kpis_impacted=item.get("kpis_impacted", []),
                primary_buyer=item.get("primary_buyer"),
                pricing_model=item.get("pricing_model"),
                listing_url=item.get("listing_url"),
                co_sell_status=item.get("co_sell_status"),
                integration_depth=item.get("integration_depth"),
                cert_level=item.get("cert_level"),
            )
            listings.append(listing)
        logger.info("Loaded %d ISVs from catalog for vendor=%s", len(listings), vendor)
        return listings
    except Exception as exc:
        logger.warning("Failed to load ISV catalog for vendor=%s: %s", vendor, exc)
        return []


async def seed_isv_catalog(
    session: AsyncSession,
    platform_vendor: str,
) -> int:
    """Load ISV catalog into the isv_solutions DB table.

    Skips ISVs already present (by name + platform_vendor).
    Returns count of new rows inserted.

    Args:
        session: Async DB session.
        platform_vendor: Platform vendor to load catalog for.

    Returns:
        Number of new ISVSolution rows created.
    """
    listings = load_catalog(platform_vendor)
    if not listings:
        logger.info("No catalog listings for vendor=%s — nothing to seed", platform_vendor)
        return 0

    # Build set of existing ISV names for this vendor
    result = await session.execute(
        select(ISVSolution.name).where(ISVSolution.platform_vendor == platform_vendor)
    )
    existing_names = {row[0] for row in result.fetchall()}

    inserted = 0
    now = datetime.now(tz=timezone.utc)

    for listing in listings:
        if listing.isv_name in existing_names:
            logger.debug("ISV already in DB: %s / %s", listing.isv_name, platform_vendor)
            continue

        isv = ISVSolution(
            name=listing.isv_name,
            vendor=listing.isv_name,
            marketplace=listing.marketplace,
            description=listing.description,
            platform_vendor=platform_vendor,
            industries_json=json.dumps(listing.industries),
            capabilities_json=json.dumps(listing.capabilities),
            business_outcomes_json=json.dumps(listing.business_outcomes),
            pricing_model=listing.pricing_model,
            co_sell_status=listing.co_sell_status,
            integration_depth=listing.integration_depth,
            cert_level=listing.cert_level,
            scraped_at=now,
        )
        session.add(isv)
        inserted += 1

    await session.flush()
    logger.info("Seeded %d new ISVs for vendor=%s", inserted, platform_vendor)
    return inserted


async def scrape_marketplace(marketplace: str) -> list[MarketplaceListing]:
    """Scrape ISV listings from a marketplace.

    Falls back to static catalog when live scraping is unavailable.

    Args:
        marketplace: One of aws | azure | gcp | salesforce | servicenow.

    Returns:
        List of MarketplaceListing objects.
    """
    logger.info("Loading ISV listings for marketplace=%s", marketplace)
    # Attempt live scraping (future implementation)
    live_results = await _scrape_live(marketplace)
    if live_results:
        return live_results
    # Fallback: static catalog
    return load_catalog(marketplace)


async def scrape_all_marketplaces() -> list[MarketplaceListing]:
    """Run scraping across all supported marketplaces."""
    results: list[MarketplaceListing] = []
    for marketplace in MARKETPLACE_URLS:
        listings = await scrape_marketplace(marketplace)
        results.extend(listings)
    logger.info("Loaded %d total ISV listings", len(results))
    return results


async def _scrape_live(marketplace: str) -> list[MarketplaceListing]:
    """Live marketplace scraping stub.

    Returns [] until headless browser infrastructure is available.
    Requires: Playwright or Selenium + marketplace-specific scrapers.
    """
    # TODO: Sprint 12+ — implement per-marketplace BeautifulSoup/Playwright scrapers
    return []
