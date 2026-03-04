"""Layer 1 — Company data aggregator.

Sources (waterfall): SEC EDGAR → website scraping → stub fallback.
Crunchbase and Proxycurl are supported when API keys are configured.

All sources degrade gracefully — the aggregator always returns a
CompanyProfile even when all external sources are unavailable.
"""

import logging
import re
from typing import Any

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel

logger = logging.getLogger(__name__)

_EDGAR_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_EDGAR_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
_HTTP_TIMEOUT = 8.0
_HEADERS = {"User-Agent": "NEXUS/1.0 seller-intelligence@nexus.local"}


# ── Pydantic models ──────────────────────────────────────────────────────────


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
    sources_used: list[str] = []


# ── Main entry point ─────────────────────────────────────────────────────────


async def aggregate_company(
    domain: str,
    ticker: str | None = None,
    name: str | None = None,
) -> CompanyProfile:
    """Build a CompanyProfile using a waterfall of available data sources.

    Waterfall: SEC EDGAR (ticker) → website scraping → stub fallback.

    Args:
        domain: Company domain (e.g. "acme.com").
        ticker: Optional stock ticker for public companies.
        name: Optional company name hint.

    Returns:
        CompanyProfile populated from best available sources.
    """
    logger.info("Aggregating company: domain=%s ticker=%s", domain, ticker)

    profile = CompanyProfile(
        name=name or _name_from_domain(domain),
        domain=domain,
        ticker=ticker,
    )

    async with httpx.AsyncClient(
        headers=_HEADERS, timeout=_HTTP_TIMEOUT, follow_redirects=True
    ) as client:
        # ── Layer 1: SEC EDGAR (free, public companies) ──────────────────────
        if ticker:
            edgar_data = await _fetch_edgar_by_ticker(client, ticker)
            if edgar_data:
                _merge_edgar(profile, edgar_data)

        # ── Layer 2: Website scraping (free, all companies) ──────────────────
        web_data = await scrape_company_website(domain, client)
        if web_data:
            _merge_web(profile, web_data)

    return profile


# ── SEC EDGAR ────────────────────────────────────────────────────────────────


async def fetch_sec_filings(
    ticker: str,
    form_types: list[str] | None = None,
    count: int = 5,
) -> list[dict[str, Any]]:
    """Fetch recent SEC filings metadata from EDGAR free API.

    Args:
        ticker: Stock ticker symbol.
        form_types: Filing types to filter (default: 10-K, 10-Q, 8-K).
        count: Maximum number of filings to return.

    Returns:
        List of filing metadata dicts.
    """
    form_types = form_types or ["10-K", "10-Q", "8-K"]
    async with httpx.AsyncClient(headers=_HEADERS, timeout=_HTTP_TIMEOUT) as client:
        edgar_data = await _fetch_edgar_by_ticker(client, ticker)
        if not edgar_data:
            return []

        filings = edgar_data.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        dates = filings.get("filingDate", [])
        documents = filings.get("primaryDocument", [])

        results = []
        for i, form in enumerate(forms):
            if form in form_types:
                results.append({
                    "form_type": form,
                    "filing_date": dates[i] if i < len(dates) else None,
                    "primary_document": documents[i] if i < len(documents) else None,
                })
            if len(results) >= count:
                break

        return results


async def _fetch_edgar_by_ticker(
    client: httpx.AsyncClient, ticker: str
) -> dict[str, Any] | None:
    """Resolve ticker → CIK, then fetch EDGAR submissions JSON."""
    try:
        resp = await client.get(_EDGAR_TICKERS_URL)
        resp.raise_for_status()
        tickers_data = resp.json()

        cik = None
        for entry in tickers_data.values():
            if entry.get("ticker", "").upper() == ticker.upper():
                cik = str(entry["cik_str"]).zfill(10)
                break

        if not cik:
            logger.debug("Ticker %s not found in EDGAR", ticker)
            return None

        url = _EDGAR_SUBMISSIONS_URL.format(cik=cik)
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()

    except Exception as exc:
        logger.debug("EDGAR fetch failed for ticker=%s: %s", ticker, exc)
        return None


def _merge_edgar(profile: CompanyProfile, edgar: dict[str, Any]) -> None:
    """Merge EDGAR submission data into a CompanyProfile."""
    if not profile.name or profile.name == _name_from_domain(profile.domain):
        profile.name = edgar.get("name", profile.name)

    if not profile.hq_location:
        city = edgar.get("city", "")
        state = edgar.get("stateOfIncorporation", "")
        if city:
            profile.hq_location = f"{city}, {state}".strip(", ")

    if not profile.industry:
        sic_desc = edgar.get("sicDescription", "")
        if sic_desc:
            profile.industry = sic_desc

    profile.sources_used.append("sec_edgar")


# ── Website scraping ─────────────────────────────────────────────────────────


async def scrape_company_website(
    domain: str,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """Scrape the company website for description, leadership, and tech mentions.

    Tries /about, /, www.{domain}/about, www.{domain} in order.
    Gracefully handles timeouts and connection errors.

    Args:
        domain: Company domain.
        client: Optional shared httpx client.

    Returns:
        Dict with: description, leadership, technologies_mentioned, raw_text.
    """
    should_close = client is None
    if client is None:
        client = httpx.AsyncClient(
            headers=_HEADERS, timeout=_HTTP_TIMEOUT, follow_redirects=True
        )

    result: dict[str, Any] = {
        "description": None,
        "leadership": [],
        "technologies_mentioned": [],
        "raw_text": "",
    }

    pages_to_try = [
        f"https://{domain}/about",
        f"https://{domain}",
        f"https://www.{domain}/about",
        f"https://www.{domain}",
    ]

    combined_text = ""
    for url in pages_to_try:
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "lxml")
                text = _extract_visible_text(soup)
                combined_text += " " + text
                if not result["description"]:
                    result["description"] = _extract_description(soup)
                break  # stop at first successful page
        except Exception:
            continue

    if should_close:
        await client.aclose()

    result["raw_text"] = combined_text.strip()
    result["technologies_mentioned"] = _extract_tech_mentions(combined_text)
    result["leadership"] = _extract_executives(combined_text)
    return result


def _extract_visible_text(soup: BeautifulSoup) -> str:
    """Strip boilerplate tags and return normalized visible text."""
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    return " ".join(soup.get_text().split())


def _extract_description(soup: BeautifulSoup) -> str | None:
    """Extract meta description, og:description, or first substantial paragraph."""
    for attr in [("name", "description"), ("property", "og:description")]:
        meta = soup.find("meta", attrs={attr[0]: attr[1]})
        if meta and meta.get("content"):
            return str(meta["content"])[:500]

    for p in soup.find_all("p"):
        text = p.get_text().strip()
        if len(text) > 80:
            return text[:500]

    return None


_TECH_PATTERNS: list[tuple[str, str]] = [
    (r"\bAWS\b|Amazon Web Services|Amazon S3\b|EC2\b|\bLambda\b", "aws"),
    (r"\bAzure\b|Microsoft Azure|Azure AD|Azure DevOps", "azure"),
    (r"\bGCP\b|Google Cloud|BigQuery\b|Vertex AI|Cloud Run\b", "gcp"),
    (r"\bSalesforce\b|Salesforce CRM|Force\.com", "salesforce"),
    (r"\bOracle\b|Oracle Cloud|Oracle DB", "oracle"),
    (r"\bIBM\b|IBM Cloud|IBM Watson", "ibm"),
    (r"\bKubernetes\b|\bk8s\b", "kubernetes"),
    (r"\bDocker\b", "docker"),
    (r"\bTerraform\b", "terraform"),
    (r"\bSnowflake\b", "snowflake"),
    (r"\bDatabricks\b", "databricks"),
    (r"\bPython\b", "python"),
    (r"\bJava\b(?!Script)", "java"),
    (r"\bReact\b|\bNext\.js\b", "react"),
    (r"\bJavaScript\b|\bNode\.js\b", "javascript"),
]


def _extract_tech_mentions(text: str) -> list[str]:
    """Return sorted list of detected technology names from free-form text."""
    found: set[str] = set()
    for pattern, tech in _TECH_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            found.add(tech)
    return sorted(found)


_EXEC_TITLE_RE = re.compile(
    r"\b(CEO|CTO|CFO|COO|CMO|CIO|CISO|VP|Vice President|President|Chief)\b",
    re.IGNORECASE,
)
_NAME_RE = re.compile(r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b")


def _extract_executives(text: str) -> list[dict[str, str]]:
    """Heuristically extract executive names and titles from scraped text."""
    executives = []
    sentences = re.split(r"[.!?\n]", text)
    for sentence in sentences[:60]:
        if _EXEC_TITLE_RE.search(sentence):
            names = _NAME_RE.findall(sentence)
            title_match = _EXEC_TITLE_RE.search(sentence)
            if names and title_match:
                executives.append({
                    "name": names[0],
                    "title": title_match.group(0),
                })

    seen: set[str] = set()
    unique = []
    for e in executives:
        if e["name"] not in seen:
            seen.add(e["name"])
            unique.append(e)
    return unique[:5]


def _merge_web(profile: CompanyProfile, web: dict[str, Any]) -> None:
    """Merge website-scraped data into a CompanyProfile."""
    if not profile.description and web.get("description"):
        profile.description = web["description"]

    for exec_dict in web.get("leadership", []):
        profile.leadership.append(
            Executive(name=exec_dict["name"], title=exec_dict["title"])
        )

    if web.get("raw_text") or web.get("description"):
        profile.sources_used.append("website_scraping")


# ── Utilities ─────────────────────────────────────────────────────────────────


def _name_from_domain(domain: str) -> str:
    """Derive a human-readable company name from a domain."""
    base = domain.split(".")[0]
    return base.replace("-", " ").replace("_", " ").title()
