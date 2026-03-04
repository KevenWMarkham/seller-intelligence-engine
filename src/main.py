import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import coaching, companies, config, contacts, tasks
from src.core.settings import settings
from src.db.database import AsyncSessionLocal, init_db

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _scheduled_news_collection() -> None:
    """APScheduler job: collect news and persist to DB."""
    try:
        from src.ingestion.news import NewsCollector
        async with AsyncSessionLocal() as session:
            collector = NewsCollector()
            count = await collector.collect(session)
            logger.info("Scheduled news collection: %d new items", count)
    except Exception:
        logger.exception("Scheduled news collection failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    # Start news ingestion scheduler
    scheduler.add_job(
        _scheduled_news_collection,
        trigger="interval",
        minutes=15,
        id="news_collection",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("APScheduler started — news collection every 15 minutes")

    yield

    scheduler.shutdown(wait=False)
    logger.info("APScheduler stopped")


app = FastAPI(
    title="NEXUS Seller Intelligence Engine",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(contacts.router, prefix="/api/contacts", tags=["contacts"])
app.include_router(coaching.router, prefix="/api/coaching", tags=["coaching"])
app.include_router(config.router, prefix="/api/config", tags=["config"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
