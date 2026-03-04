"""
Manual full pipeline trigger for testing and development.

Runs: news ingestion → classification → brief generation → priority scoring → task creation.

Usage: python scripts/run_pipeline.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.database import AsyncSessionLocal, init_db
from src.ingestion.news import collect_rss_feeds


async def run_pipeline():
    print("==> NEXUS Pipeline — Manual Run")

    await init_db()

    # Step 1: Collect news
    print("--> Step 1: Collecting news from RSS feeds...")
    items = await collect_rss_feeds()
    print(f"    Collected {len(items)} raw news items")

    if not items:
        print("    No news items collected. Check config/ingestion.yaml and network.")
        return

    # Step 2: Classify (requires Ollama running)
    print("--> Step 2: Classifying news items (requires Ollama)...")
    from src.ai.ollama_client import is_healthy
    if not await is_healthy():
        print("    WARNING: Ollama is not running. Skipping AI classification.")
        print("    Start Ollama with: ollama serve")
        return

    from src.ai.classifier import classify_news
    classified = []
    for item in items[:5]:  # Limit to 5 for manual runs
        try:
            classification = await classify_news(
                headline=item.headline,
                body=item.body or "",
                platform_vendor="google",
                watched_companies=[],
            )
            classified.append((item, classification))
            print(f"    Classified: {item.headline[:60]}... → relevance={classification.relevance_score:.2f} urgency={classification.urgency}")
        except Exception as e:
            print(f"    ERROR classifying item: {e}")

    print(f"\n==> Pipeline complete. Classified {len(classified)}/{len(items[:5])} items.")
    print("    Phase 4-6 implementation will complete the full pipeline.")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
