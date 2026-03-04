"""Manual full pipeline trigger for testing and development.

Usage:
    python scripts/run_pipeline.py                # run full pipeline
    python scripts/run_pipeline.py --layer news   # run news ingestion only
    python scripts/run_pipeline.py --layer ai     # run AI classification only
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

    print("==> Pipeline run complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NEXUS manual pipeline trigger")
    parser.add_argument("--layer", choices=["news", "ai"], help="Run a specific layer only")
    args = parser.parse_args()
    asyncio.run(run_pipeline(layer=args.layer))
