"""Layer 4 — AI pipeline: news → classify → brief → score → SellerTask.

Processes unclassified NewsItems from the DB, generates conversation briefs,
scores each task, and creates SellerTask records for the seller dashboard.
"""

import json
import logging
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai import brief_generator, classifier, scorer
from src.contacts.linker import link_contacts_to_news
from src.contacts.resolver import resolve_contacts
from src.models.company import Company
from src.models.contact import Contact
from src.models.news import NewsItem
from src.models.task import SellerTask

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "platform.yaml"
_PLATFORMS_DIR = Path(__file__).parent.parent.parent / "config" / "platforms"

RELEVANCE_THRESHOLD = 0.3
DEFAULT_SELLER_ID = "seller-1"


def _load_active_vendor() -> str:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f).get("active_vendor", "google")


def _load_platform_products(vendor: str) -> list[str]:
    path = _PLATFORMS_DIR / f"{vendor}.yaml"
    if not path.exists():
        return []
    with open(path) as f:
        catalog = yaml.safe_load(f) or {}
    return [p["name"] for p in catalog.get("products", [])][:5]


async def run_ai_pipeline(session: AsyncSession) -> int:
    """Process unclassified news items and create prioritised SellerTasks.

    Steps per news item:
        1. Classify relevance/urgency/signal via Qwen
        2. Update NewsItem fields in DB
        3. Skip if relevance < threshold
        4. Match news to watched companies
        5. Generate conversation brief per matched company
        6. Score the task (1-100)
        7. Upsert SellerTask

    Returns:
        Number of new SellerTask records created.
    """
    vendor = _load_active_vendor()
    platform_products = _load_platform_products(vendor)

    # Load all watched companies
    companies_result = await session.execute(select(Company))
    all_companies = list(companies_result.scalars().all())
    watched_names = [c.name for c in all_companies]
    company_by_name: dict[str, Company] = {c.name.lower(): c for c in all_companies}

    if not all_companies:
        logger.warning("No companies in DB. Run seed_data.py first.")
        return 0

    # Fetch unclassified news items (relevance_score not yet set)
    news_result = await session.execute(
        select(NewsItem).where(NewsItem.relevance_score.is_(None))
    )
    unclassified = list(news_result.scalars().all())

    if not unclassified:
        logger.info("No unclassified news items found.")
        return 0

    logger.info(f"Classifying {len(unclassified)} news items for vendor={vendor}...")
    tasks_created = 0

    for news_item in unclassified:
        try:
            # ── Step 1: Classify ──────────────────────────────────────────
            classification = await classifier.classify_news(
                headline=news_item.headline,
                body=news_item.body or "",
                platform_vendor=vendor,
                watched_companies=watched_names,
            )

            # ── Step 2: Update NewsItem ───────────────────────────────────
            news_item.relevance_score = classification.relevance_score
            news_item.urgency = classification.urgency
            news_item.signal_type = classification.signal_type
            news_item.opportunity_type = classification.opportunity_type
            news_item.companies_mentioned_json = json.dumps(
                classification.companies_mentioned
            )

            # ── Step 3: Filter low-relevance ─────────────────────────────
            if classification.relevance_score < RELEVANCE_THRESHOLD:
                logger.debug(
                    f"Skipping low-relevance ({classification.relevance_score:.2f}): "
                    f"{news_item.headline[:60]}"
                )
                continue

            # ── Step 4: Match companies ───────────────────────────────────
            matched: list[Company] = []
            for name in classification.companies_mentioned:
                company = company_by_name.get(name.lower())
                if company:
                    matched.append(company)

            # Fallback: apply to companies that don't yet have a task for this news
            if not matched:
                existing_ids_result = await session.execute(
                    select(SellerTask.company_id).where(
                        SellerTask.news_item_id == news_item.id
                    )
                )
                tasked_ids = {r[0] for r in existing_ids_result.fetchall()}
                matched = [c for c in all_companies if c.id not in tasked_ids][:1]

            # ── Steps 5-7: Brief + Score + Task per company ───────────────
            for company in matched:
                # Skip if task already exists for this news+company pair
                existing_result = await session.execute(
                    select(SellerTask).where(
                        SellerTask.news_item_id == news_item.id,
                        SellerTask.company_id == company.id,
                    )
                )
                if existing_result.scalar_one_or_none():
                    continue

                # Resolve best contact via signal-aware linker
                resolved_contacts = await resolve_contacts(
                    company_name=company.name,
                    domain=company.domain,
                    platform_vendor=vendor,
                    company_id=company.id,
                    session=session,
                )
                contact = None  # ResolvedContact used for brief/score params
                contact_id: int | None = None
                if resolved_contacts:
                    matches = link_contacts_to_news(
                        contacts=resolved_contacts,
                        signal_type=classification.signal_type or "tech_initiative",
                        news_headline=news_item.headline,
                        platform_vendor=vendor,
                        platform_products=platform_products,
                    )
                    if matches:
                        contact = matches[0].contact
                    if contact:
                        id_result = await session.execute(
                            select(Contact.id).where(
                                Contact.company_id == company.id,
                                Contact.name == contact.name,
                            )
                        )
                        contact_id = id_result.scalar_one_or_none()

                priorities: list[str] = _extract_priorities(company)
                platform_adoption = _adoption_depth(company.sales_motion)

                # Generate brief
                brief = await brief_generator.generate_brief(
                    company_name=company.name,
                    contact_name=contact.name if contact else "Decision Maker",
                    contact_title=contact.title if contact else "Executive",
                    functional_area=contact.functional_area if contact else "Operations",
                    news_headline=news_item.headline,
                    news_summary=classification.summary,
                    platform_vendor=vendor,
                    sales_motion=company.sales_motion or "new",
                    company_priorities=priorities,
                    platform_products=platform_products,
                )

                # Score the task
                score = await scorer.score_task(
                    company_name=company.name,
                    company_priorities=priorities,
                    platform_adoption_depth=platform_adoption,
                    sales_motion=company.sales_motion or "new",
                    contact_role_type=contact.role_type if contact else "influencer",
                    contact_title=contact.title if contact else "Executive",
                    news_urgency=classification.urgency,
                    deal_value_estimate=company.revenue,
                )

                # Create SellerTask
                task = SellerTask(
                    seller_id=DEFAULT_SELLER_ID,
                    company_id=company.id,
                    contact_id=contact_id,
                    news_item_id=news_item.id,
                    platform_vendor=vendor,
                    sales_motion=company.sales_motion or "new",
                    conversation_brief_json=json.dumps(brief.model_dump()),
                    priority_score=score.score,
                    priority_reasoning=score.reasoning,
                    status="created",
                )
                session.add(task)
                tasks_created += 1
                logger.info(
                    f"  Created task: {company.name} | score={score.score} | "
                    f"{news_item.headline[:50]}"
                )

        except Exception as exc:
            logger.error(f"Error processing news_item.id={news_item.id}: {exc}")
            continue

    await session.commit()
    logger.info(f"AI pipeline complete. {tasks_created} tasks created.")
    return tasks_created


def _extract_priorities(company: Company) -> list[str]:
    """Return company business priorities, falling back to generic defaults."""
    if company.priorities_json:
        try:
            parsed = json.loads(company.priorities_json)
            if isinstance(parsed, list) and parsed:
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    return [
        f"Digital transformation at {company.name}",
        "Operational efficiency and cost reduction",
        "AI/ML capability expansion",
    ]


def _adoption_depth(sales_motion: str | None) -> str:
    """Map sales motion to a platform adoption depth descriptor."""
    return {
        "wedge": "none",
        "new": "none",
        "expand": "moderate",
        "displace": "none",
    }.get(sales_motion or "new", "unknown")
