"""Layer 1.5 — Business capability mapper.

Translates ISV technical features into business-value language:
outcomes, processes improved, and KPIs impacted.

If the ISV already has catalog-sourced business outcomes, those are returned
directly without calling Qwen. Qwen extraction only runs for ISVs without
pre-populated outcome data.
"""

import logging

from pydantic import BaseModel

from src.ai import ollama_client

logger = logging.getLogger(__name__)


class CapabilityMapping(BaseModel):
    isv_name: str
    business_outcomes: list[str]
    processes_improved: list[str]
    kpis_impacted: list[str]
    example_customer_results: list[str] = []


async def map_capabilities(
    isv_name: str,
    description: str,
    capabilities: list[str],
    pre_mapped_outcomes: list[str] | None = None,
    pre_mapped_processes: list[str] | None = None,
    pre_mapped_kpis: list[str] | None = None,
) -> CapabilityMapping:
    """Map an ISV solution's technical features to business outcomes, processes, and KPIs.

    Uses catalog data if available (no Qwen call needed). Falls back to Qwen
    extraction when catalog data is absent.

    Args:
        isv_name: ISV solution name.
        description: Solution description.
        capabilities: Classified capability areas.
        pre_mapped_outcomes: Business outcomes from static catalog.
        pre_mapped_processes: Processes improved from static catalog.
        pre_mapped_kpis: KPIs impacted from static catalog.

    Returns:
        CapabilityMapping with business outcomes and KPIs.
    """
    logger.info("Mapping capabilities for ISV: %s", isv_name)

    # Catalog data takes precedence — avoid unnecessary Qwen call
    if pre_mapped_outcomes:
        return CapabilityMapping(
            isv_name=isv_name,
            business_outcomes=pre_mapped_outcomes,
            processes_improved=pre_mapped_processes or [],
            kpis_impacted=pre_mapped_kpis or [],
        )

    # Qwen extraction for ISVs without catalog outcome data
    cap_str = ", ".join(capabilities) if capabilities else "general enterprise software"
    prompt = (
        f"You are a B2B technology value consultant. Extract business value from this ISV.\n\n"
        f"ISV: {isv_name}\n"
        f"Capabilities: {cap_str}\n"
        f"Description: {description[:500]}\n\n"
        f"Return JSON:\n"
        f'{{"business_outcomes": ["<3 specific measurable outcomes with % improvement or time savings>"], '
        f'"processes_improved": ["<3 business processes this solution improves>"], '
        f'"kpis_impacted": ["<3 KPIs this solution moves>"]}}'
    )

    try:
        raw = await ollama_client.complete(prompt)
        return CapabilityMapping(
            isv_name=isv_name,
            business_outcomes=raw.get("business_outcomes", []),
            processes_improved=raw.get("processes_improved", []),
            kpis_impacted=raw.get("kpis_impacted", []),
        )
    except Exception as exc:
        logger.warning("Qwen capability mapping failed for %s: %s — returning empty mapping", isv_name, exc)
        return CapabilityMapping(
            isv_name=isv_name,
            business_outcomes=[],
            processes_improved=[],
            kpis_impacted=[],
        )
