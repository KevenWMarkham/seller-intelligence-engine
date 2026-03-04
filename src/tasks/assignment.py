"""Layer 6 — Seller assignment engine.

Routing: CRM account ownership → named account lists → territory rules → round-robin fallback.
"""

import logging

logger = logging.getLogger(__name__)


async def assign_seller(
    company_name: str,
    domain: str,
    crm_opportunities: list[dict] | None = None,
) -> str | None:
    """
    Determine which seller should receive a task for a given company.

    Routing order:
    1. CRM account ownership (opportunity.seller_id)
    2. Named account list mapping
    3. Territory rules (by domain TLD, industry, region)
    4. Round-robin fallback

    Args:
        company_name: Target company name.
        domain: Company domain.
        crm_opportunities: Active CRM opportunities for this account.

    Returns:
        Seller ID string, or None if unassigned.
    """
    # 1. CRM ownership
    if crm_opportunities:
        for opp in crm_opportunities:
            if seller_id := opp.get("seller_id"):
                logger.info("Assigned %s to seller %s via CRM ownership", company_name, seller_id)
                return seller_id

    # 2-4. TODO: Phase 12 — named account lists, territory rules, round-robin
    logger.debug("No seller assignment found for %s", company_name)
    return None
