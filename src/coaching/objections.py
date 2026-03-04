"""Layer 5 — Objection library backed by ChromaDB.

Sellers can drill specific scenarios: industry × role × deal stage × sales motion.
New objections from roleplays and real calls are added automatically.
"""

import logging

import chromadb
from pydantic import BaseModel

logger = logging.getLogger(__name__)

_client: chromadb.Client | None = None
COLLECTION_NAME = "objections"


def _get_collection():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path="chroma_db")
    return _client.get_or_create_collection(COLLECTION_NAME)


class ObjectionEntry(BaseModel):
    id: str
    objection: str
    industry: str | None = None
    functional_area: str | None = None
    deal_stage: str | None = None
    sales_motion: str | None = None
    suggested_responses: list[str] = []
    source: str | None = None  # roleplay | real_call | manual


async def search_objections(
    query: str,
    industry: str | None = None,
    functional_area: str | None = None,
    sales_motion: str | None = None,
    top_k: int = 5,
) -> list[ObjectionEntry]:
    """
    Search the objection library for similar objections.

    Args:
        query: The objection text to search for.
        industry: Optional industry filter.
        functional_area: Optional functional area filter.
        sales_motion: Optional sales motion filter.
        top_k: Number of results to return.

    Returns:
        List of relevant ObjectionEntry matches.
    """
    # TODO: Phase 10 — ChromaDB similarity search with metadata filtering
    logger.info("Searching objections for: %s", query[:50])
    return []


async def add_objection(entry: ObjectionEntry) -> None:
    """Add a new objection to the library."""
    # TODO: Phase 10 — embed and store in ChromaDB
    logger.info("Adding objection: %s", entry.objection[:50])
