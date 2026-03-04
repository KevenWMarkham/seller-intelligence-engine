"""Layer 1 — Business priority extractor.

Sources: SEC EDGAR 10-K/8-K filing text, website-scraped description, Qwen synthesis.

Strategy (waterfall):
1. Attempt to fetch SEC EDGAR 10-K filing document text (public companies with ticker).
2. Combine EDGAR text + company_description + industry context into a raw_data blob.
3. Render prompts/build_snapshot.jinja2 and call Qwen via ollama_client.complete().
4. Parse key_strategic_priorities from the response and score alignment against
   the seller's platform_products list.
5. Degrade gracefully when Ollama is unavailable (return []) or EDGAR is unreachable.
"""

import logging
import re
from pathlib import Path
from typing import Any

import httpx
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from src.ai import ollama_client
from src.snapshot.aggregator import _EDGAR_SUBMISSIONS_URL, _EDGAR_TICKERS_URL, _HEADERS

logger = logging.getLogger(__name__)

_jinja = Environment(
    loader=FileSystemLoader(Path(__file__).parent.parent.parent / "prompts")
)

_MAX_EDGAR_TEXT = 4_000

_EDGAR_ARCHIVE_URL = (
    "https://www.sec.gov/Archives/edgar/data/{cik}/{accession_nodashes}/{primary_doc}"
)

_HTTP_TIMEOUT = 12.0


# ── Pydantic models ───────────────────────────────────────────────────────────


class CompanyPriority(BaseModel):
    priority: str
    source: str  # e.g. "Q3 2025 Earnings Call", "CEO LinkedIn", "10-K 2024"
    alignment: str  # HIGH | MEDIUM | LOW
    platform_products: list[str] = []
    talking_points: list[str] = []


# ── Main entry point ──────────────────────────────────────────────────────────


async def extract_priorities(
    company_name: str,
    domain: str,
    ticker: str | None,
    platform_vendor: str,
    platform_products: list[str],
    company_description: str | None = None,
) -> list[CompanyPriority]:
    """Extract top business priorities and map them to platform capabilities.

    Args:
        company_name: Target company name.
        domain: Company domain.
        ticker: Stock ticker (required for EDGAR access; None for private companies).
        platform_vendor: Seller's platform vendor string (e.g. "google").
        platform_products: Product name list from the vendor YAML config.
        company_description: Optional pre-fetched description text (e.g. from website).

    Returns:
        List of CompanyPriority ranked by alignment strength (HIGH first).
    """
    logger.info("Extracting priorities for %s (ticker=%s)", company_name, ticker)

    raw_data: dict[str, Any] = {
        "company_name": company_name,
        "domain": domain,
    }

    if company_description:
        raw_data["description"] = company_description

    edgar_source: str | None = None

    if ticker:
        edgar_text, filing_label = await _fetch_edgar_filing_text(ticker)
        if edgar_text:
            raw_data["sec_filing_excerpt"] = edgar_text
            edgar_source = filing_label
            logger.debug(
                "EDGAR text loaded for %s (%s, %d chars)",
                ticker,
                filing_label,
                len(edgar_text),
            )

    template = _jinja.get_template("build_snapshot.jinja2")
    prompt = template.render(
        company_name=company_name,
        domain=domain,
        ticker=ticker,
        industry=raw_data.get("industry"),
        platform_vendor=platform_vendor,
        raw_data=raw_data,
    )

    try:
        qwen_response = await ollama_client.complete(prompt)
    except Exception as exc:
        logger.warning(
            "Ollama unavailable while extracting priorities for %s: %s",
            company_name,
            exc,
        )
        return []

    raw_priorities: list[str] = qwen_response.get("key_strategic_priorities", [])

    if not raw_priorities:
        logger.debug("Qwen returned no key_strategic_priorities for %s", company_name)
        return []

    source_label = edgar_source if edgar_source else "Qwen synthesis from available data"

    priorities: list[CompanyPriority] = []
    for priority_text in raw_priorities:
        if not isinstance(priority_text, str) or not priority_text.strip():
            continue

        matched_products = _match_products(priority_text, platform_products)
        alignment = _score_alignment(matched_products)

        priorities.append(
            CompanyPriority(
                priority=priority_text.strip(),
                source=source_label,
                alignment=alignment,
                platform_products=matched_products,
                talking_points=[],
            )
        )

    _ALIGNMENT_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    priorities.sort(key=lambda p: _ALIGNMENT_ORDER.get(p.alignment, 2))

    logger.info(
        "Extracted %d priorities for %s (%d HIGH, %d MEDIUM)",
        len(priorities),
        company_name,
        sum(1 for p in priorities if p.alignment == "HIGH"),
        sum(1 for p in priorities if p.alignment == "MEDIUM"),
    )
    return priorities


# ── EDGAR filing text fetch ───────────────────────────────────────────────────


async def _fetch_edgar_filing_text(ticker: str) -> tuple[str, str]:
    """Fetch the text of the most recent 10-K (fallback: 10-Q) from EDGAR.

    Returns:
        Tuple of (filing_text_excerpt, source_label). Both empty strings on failure.
    """
    try:
        async with httpx.AsyncClient(
            headers=_HEADERS, timeout=_HTTP_TIMEOUT, follow_redirects=True
        ) as client:
            resp = await client.get(_EDGAR_TICKERS_URL)
            resp.raise_for_status()
            tickers_data = resp.json()

            cik: str | None = None
            for entry in tickers_data.values():
                if entry.get("ticker", "").upper() == ticker.upper():
                    cik = str(entry["cik_str"]).zfill(10)
                    break

            if not cik:
                logger.debug("EDGAR: ticker %s not found", ticker)
                return "", ""

            url = _EDGAR_SUBMISSIONS_URL.format(cik=cik)
            resp = await client.get(url)
            resp.raise_for_status()
            edgar_data = resp.json()

            filings = edgar_data.get("filings", {}).get("recent", {})
            forms = filings.get("form", [])
            dates = filings.get("filingDate", [])
            accession_numbers = filings.get("accessionNumber", [])
            primary_docs = filings.get("primaryDocument", [])

            target_form: str | None = None
            target_date: str | None = None
            target_accession: str | None = None
            target_primary_doc: str | None = None

            for priority_form in ("10-K", "10-Q"):
                for i, form in enumerate(forms):
                    if form == priority_form:
                        target_form = form
                        target_date = dates[i] if i < len(dates) else None
                        target_accession = (
                            accession_numbers[i] if i < len(accession_numbers) else None
                        )
                        target_primary_doc = (
                            primary_docs[i] if i < len(primary_docs) else None
                        )
                        break
                if target_form:
                    break

            if not (target_accession and target_primary_doc):
                logger.debug("EDGAR: no 10-K/10-Q filing found for ticker %s", ticker)
                return "", ""

            accession_nodashes = target_accession.replace("-", "")
            doc_url = _EDGAR_ARCHIVE_URL.format(
                cik=cik.lstrip("0"),
                accession_nodashes=accession_nodashes,
                primary_doc=target_primary_doc,
            )

            doc_resp = await client.get(doc_url)
            doc_resp.raise_for_status()

            raw_text = _strip_html_to_text(doc_resp.text)
            excerpt = _extract_strategic_excerpt(raw_text)

            year = target_date[:4] if target_date else "recent"
            source_label = f"SEC EDGAR {target_form} {year}"

            return excerpt, source_label

    except Exception as exc:
        logger.debug("EDGAR filing text fetch failed for ticker=%s: %s", ticker, exc)
        return "", ""


def _strip_html_to_text(html: str) -> str:
    """Strip HTML tags and return normalized plain text."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_strategic_excerpt(text: str, max_chars: int = _MAX_EDGAR_TEXT) -> str:
    """Extract the most strategically relevant portion of a filing document."""
    strategy_pattern = (
        r"(?i)(business\s+strategy|strategic\s+priorities|growth\s+strategy"
        r"|our\s+strategy|key\s+priorities|strategic\s+objectives"
        r"|strategic\s+initiatives|management.{0,20}discussion)"
    )

    match = re.search(strategy_pattern, text)
    if match:
        best_start = max(0, match.start() - 50)
        excerpt = text[best_start : best_start + max_chars]
    else:
        excerpt = text[:max_chars]

    return excerpt.strip()


# ── Alignment scoring ─────────────────────────────────────────────────────────


def _match_products(priority_text: str, platform_products: list[str]) -> list[str]:
    """Return platform products whose names appear as keywords in priority_text."""
    priority_lower = priority_text.lower()
    matched: list[str] = []

    for product in platform_products:
        product_lower = product.lower()

        if product_lower in priority_lower:
            matched.append(product)
            continue

        words = [w for w in re.split(r"\W+", product_lower) if len(w) >= 4]
        if any(word in priority_lower for word in words):
            matched.append(product)

    return matched


def _score_alignment(matched_products: list[str]) -> str:
    """Derive alignment tier from the number of matched platform products."""
    if matched_products:
        return "HIGH"
    return "MEDIUM"
