"""Ollama/Qwen wrapper — all AI calls go through this module."""

import json
import logging
from typing import Any

import httpx

from src.core.settings import settings

logger = logging.getLogger(__name__)

CHAT_URL = f"{settings.ollama_host}/api/chat"
HEALTH_URL = f"{settings.ollama_host}/api/tags"


async def _post(payload: dict) -> dict:
    """Send a single request to Ollama, return parsed JSON."""
    async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
        response = await client.post(CHAT_URL, json=payload)
        response.raise_for_status()
        return response.json()


async def complete(
    prompt: str,
    system: str | None = None,
    model: str | None = None,
    retries: int = 2,
) -> dict[str, Any]:
    """
    Send a prompt to Qwen via Ollama in JSON mode.

    Returns the parsed JSON object from the model response.
    Raises ValueError if the response cannot be parsed as JSON.
    """
    active_model = model or settings.ollama_model
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": active_model,
        "messages": messages,
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.2},
    }

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            result = await _post(payload)
            content = result["message"]["content"]
            return json.loads(content)
        except (httpx.HTTPError, KeyError) as e:
            last_error = e
            logger.warning("Ollama request failed (attempt %d/%d): %s", attempt + 1, retries + 1, e)
            if attempt < retries and active_model == settings.ollama_model:
                active_model = settings.ollama_fallback_model
                payload["model"] = active_model
        except json.JSONDecodeError as e:
            raise ValueError(f"Ollama returned non-JSON response: {e}") from e

    raise RuntimeError(f"Ollama request failed after {retries + 1} attempts: {last_error}")


async def is_healthy() -> bool:
    """Check if Ollama is running and has a model available."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(HEALTH_URL)
            return resp.status_code == 200
    except Exception:
        return False
