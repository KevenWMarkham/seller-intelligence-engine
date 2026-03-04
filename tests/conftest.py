"""Shared pytest fixtures for NEXUS test suite."""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.db.database import Base, get_session
from src.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    """In-memory SQLite session for unit tests."""
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    """Test HTTP client with DB session overridden."""
    app.dependency_overrides[get_session] = lambda: db_session
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def mock_ollama_response(monkeypatch):
    """Mock Ollama client to avoid real AI calls in unit tests."""
    async def mock_complete(prompt, system=None, model=None, retries=2):
        return {"response": "mocked", "score": 75, "reasoning": "mocked reasoning"}

    import src.ai.ollama_client as client_module
    monkeypatch.setattr(client_module, "complete", mock_complete)
    return mock_complete
