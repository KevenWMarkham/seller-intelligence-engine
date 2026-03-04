from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import coaching, companies, config, contacts, tasks
from src.core.settings import settings
from src.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


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
