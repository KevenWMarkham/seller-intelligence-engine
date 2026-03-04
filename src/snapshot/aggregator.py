"""Layer 1 — Company data aggregator.

Sources: SEC EDGAR, Crunchbase, LinkedIn, website scraping.
"""

import logging

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Executive(BaseModel):
    name: str
    title: str
    linkedin_url: str | None = None


class FundingRound(BaseModel):
    round: str
    amount: str | None
    date: str | None
    investors: list[str] = []


class CompanyProfile(BaseModel):
    name: str
    domain: str
    ticker: str | None = None
    industry: str | None = None
    sub_industry: str | None = None
    revenue: str | None = None
    headcount: int | None = None
    hq_location: str | None = None
    founded: int | None = None
    stage: str | None = None
    business_model: str | None = None
    leadership: list[Executive] = []
    funding_rounds: list[FundingRound] | None = None
    description: str | None = None


async def aggregate_company(domain: str, ticker: str | None = None) -> CompanyProfile:
    """
    Pull company data from available sources and return a normalized CompanyProfile.

    Waterfall: Crunchbase → SEC EDGAR (if public) → website scraping → fallback stub.

    Args:
        domain: Company domain (e.g. "acme.com").
        ticker: Optional stock ticker for public companies.

    Returns:
        CompanyProfile populated from best available sources.
    """
    # TODO: Phase 6 — implement Crunchbase, SEC EDGAR, and website scraping
    logger.info("Aggregating company data for domain=%s ticker=%s", domain, ticker)
    return CompanyProfile(name=domain.split(".")[0].title(), domain=domain)


async def fetch_sec_filings(ticker: str) -> list[dict]:
    """
    Fetch recent 10-K, 10-Q, and 8-K filings from SEC EDGAR free API.

    Args:
        ticker: Stock ticker symbol.

    Returns:
        List of filing metadata dicts.
    """
    # TODO: Phase 6 — https://data.sec.gov/submissions/CIK{cik}.json
    logger.info("Fetching SEC filings for ticker=%s", ticker)
    return []


async def scrape_company_website(domain: str) -> dict:
    """
    Scrape About page, leadership, and press releases from company website.

    Args:
        domain: Company domain.

    Returns:
        Dict with scraped text content by section.
    """
    # TODO: Phase 6 — BeautifulSoup scraper
    logger.info("Scraping website for domain=%s", domain)
    return {}
