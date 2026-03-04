"""Manual full pipeline trigger for testing and development.

Usage:
    python scripts/run_pipeline.py                    # run full pipeline
    python scripts/run_pipeline.py --layer news       # run news ingestion only
    python scripts/run_pipeline.py --layer ai         # run AI classification only
    python scripts/run_pipeline.py --layer snapshot   # run snapshot pipeline for all companies
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.database import AsyncSessionLocal, init_db


async def run_news_layer() -> int:
    """Collect and store news items. Returns count of new items."""
    from src.ingestion.news import NewsCollector
    async with AsyncSessionLocal() as session:
        collector = NewsCollector()
        count = await collector.collect(session)
    print(f"    Stored {count} new news items")
    return count


async def run_ai_layer() -> int:
    """Classify stored news items and create SellerTasks (requires Ollama)."""
    from src.ai.ollama_client import is_healthy
    if not await is_healthy():
        print("    WARNING: Ollama is not running. Skipping AI classification.")
        print("    Start Ollama with: ollama serve")
        return 0

    from src.ai.pipeline import run_ai_pipeline
    async with AsyncSessionLocal() as session:
        count = await run_ai_pipeline(session)
    print(f"    Created {count} new SellerTask(s)")
    return count


async def run_isv_layer() -> int:
    """Seed ISV catalog from config/isvs/ into the DB for all configured vendors."""
    from src.api.config import get_platform_context
    from src.isv.scraper import seed_isv_catalog

    platform = await get_platform_context()
    total = 0

    async with AsyncSessionLocal() as session:
        # Seed for active vendor
        count = await seed_isv_catalog(session, platform.vendor)
        await session.commit()
        total += count
        print(f"    Seeded {count} ISVs for vendor={platform.vendor}")

    return total


async def run_snapshot_layer() -> int:
    """Run full snapshot pipeline for all companies (requires Ollama for motion + priorities)."""
    from sqlalchemy import select

    from src.api.config import get_platform_context
    from src.models.company import Company
    from src.snapshot.competitive import build_competitive_snapshot
    from src.snapshot.motion_classifier import classify_motion
    from src.snapshot.priorities import extract_priorities
    from src.snapshot.technographics import (
        PlatformAdoption,
        Technology,
        TechProfile,
        profile_tech_stack,
    )

    platform = await get_platform_context()
    product_names = [p["name"] for p in platform.products]
    updated = 0

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Company))
        companies = result.scalars().all()

        for company in companies:
            print(f"    Processing: {company.name} ({company.domain})")
            db_updated = False

            # Tech profile
            tech_profile: TechProfile | None = None
            if company.platform_adoption_json:
                try:
                    import json
                    pa_data = json.loads(company.platform_adoption_json)
                    ts_data = json.loads(company.tech_stack_json or "[]")
                    tech_profile = TechProfile(
                        domain=company.domain,
                        stack=[Technology.model_validate(t) for t in ts_data],
                        platform_adoption={
                            v: PlatformAdoption.model_validate(a) for v, a in pa_data.items()
                        },
                    )
                except Exception:
                    pass

            if tech_profile is None:
                try:
                    tech_profile = await profile_tech_stack(company.domain)
                    import json
                    company.tech_stack_json = json.dumps(
                        [t.model_dump() for t in tech_profile.stack]
                    )
                    company.platform_adoption_json = json.dumps(
                        {v: a.model_dump() for v, a in tech_profile.platform_adoption.items()}
                    )
                    db_updated = True
                except Exception as exc:
                    print(f"      WARNING: Tech profiling failed: {exc}")

            # Sales motion
            if not company.sales_motion and tech_profile is not None:
                try:
                    motion = await classify_motion(
                        company_name=company.name,
                        platform_vendor=platform.vendor,
                        tech_profile=tech_profile,
                    )
                    company.sales_motion = motion.type
                    db_updated = True
                    print(f"      Motion: {motion.type} (confidence={motion.confidence:.2f})")
                except Exception as exc:
                    print(f"      WARNING: Motion classification failed: {exc}")

            # Competitive
            if not company.competitive_json:
                try:
                    comp = await build_competitive_snapshot(
                        company_name=company.name,
                        domain=company.domain,
                        industry=company.industry,
                        platform_vendor=platform.vendor,
                        tech_profile=tech_profile,
                    )
                    company.competitive_json = comp.model_dump_json()
                    db_updated = True
                    print(f"      Competitors: {len(comp.competitors)} found")
                except Exception as exc:
                    print(f"      WARNING: Competitive analysis failed: {exc}")

            # Priorities
            if not company.priorities_json:
                try:
                    priorities = await extract_priorities(
                        company_name=company.name,
                        domain=company.domain,
                        ticker=company.ticker,
                        platform_vendor=platform.vendor,
                        platform_products=product_names,
                        company_description=company.description,
                    )
                    import json
                    company.priorities_json = json.dumps([p.model_dump() for p in priorities])
                    db_updated = True
                    print(f"      Priorities: {len(priorities)} extracted")
                except Exception as exc:
                    print(f"      WARNING: Priority extraction failed: {exc}")

            if db_updated:
                from datetime import datetime, timezone
                company.snapshot_refreshed_at = datetime.now(timezone.utc)
                await session.commit()
                updated += 1

    return updated


async def run_pipeline(layer: str | None = None) -> None:
    print("==> NEXUS Pipeline — Manual Run")
    await init_db()

    if layer == "news" or layer is None:
        print("--> Collecting news...")
        count = await run_news_layer()
        if layer == "news":
            print(f"==> Done. {count} new items stored.")
            return

    if layer == "ai" or layer is None:
        print("--> Running AI classification...")
        count = await run_ai_layer()
        if layer == "ai":
            print(f"==> Done. {count} tasks created.")
            return

    if layer == "snapshot" or layer is None:
        print("--> Running snapshot pipeline...")
        count = await run_snapshot_layer()
        if layer == "snapshot":
            print(f"==> Done. {count} companies updated.")
            return

    if layer == "isvs" or layer is None:
        print("--> Seeding ISV catalog...")
        count = await run_isv_layer()
        if layer == "isvs":
            print(f"==> Done. {count} new ISVs seeded.")
            return

    print("==> Pipeline run complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NEXUS manual pipeline trigger")
    parser.add_argument(
        "--layer",
        choices=["news", "ai", "snapshot", "isvs"],
        help="Run a specific layer only",
    )
    args = parser.parse_args()
    asyncio.run(run_pipeline(layer=args.layer))
