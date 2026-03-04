"""Layer 5 — Roleplay simulator.

Seller chats with OpenClaw coach playing the prospect persona.
Persona is enriched with real company data for realistic pushback.
"""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from src.ai import ollama_client

logger = logging.getLogger(__name__)

_jinja = Environment(loader=FileSystemLoader(Path(__file__).parent.parent.parent / "prompts"))

MAX_TURNS = 20


class RoleplayMessage(BaseModel):
    role: str  # seller | prospect | coach
    content: str
    turn: int


class RoleplaySession(BaseModel):
    session_id: int
    seller_id: str
    company_name: str
    contact_name: str
    contact_title: str
    sales_motion: str
    messages: list[RoleplayMessage] = []
    is_complete: bool = False


async def generate_prospect_persona(
    contact_name: str,
    contact_title: str,
    company_name: str,
    company_priorities: list[str],
    tech_stack: list[str],
    sales_motion: str,
    platform_vendor: str,
) -> str:
    """
    Generate a realistic prospect persona for roleplay simulation.

    The persona is grounded in real company data — pushback reflects the
    company's actual tech dependencies, budget cycle, and strategic context.

    Returns:
        System prompt string defining the prospect persona.
    """
    template = _jinja.get_template("roleplay_persona.jinja2")
    return template.render(
        contact_name=contact_name,
        contact_title=contact_title,
        company_name=company_name,
        company_priorities=company_priorities,
        tech_stack=tech_stack,
        sales_motion=sales_motion,
        platform_vendor=platform_vendor,
    )


async def respond_as_prospect(
    persona_prompt: str,
    conversation_history: list[RoleplayMessage],
    seller_message: str,
) -> str:
    """
    Generate the prospect's response to a seller message.

    Args:
        persona_prompt: Prospect persona system prompt.
        conversation_history: Prior turns in the roleplay.
        seller_message: The seller's latest message.

    Returns:
        Prospect response as a string.
    """
    messages = [{"role": "system", "content": persona_prompt}]
    for msg in conversation_history:
        role = "assistant" if msg.role == "prospect" else "user"
        messages.append({"role": role, "content": msg.content})
    messages.append({"role": "user", "content": seller_message})

    # TODO: Phase 10 — use streaming for real-time display
    raw = await ollama_client.complete(
        prompt=seller_message,
        system=persona_prompt,
    )
    return raw.get("response", "")
