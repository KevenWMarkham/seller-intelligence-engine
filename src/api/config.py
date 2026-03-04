"""Platform vendor context API.

GET  /api/config/platform           — current vendor + product catalog
PUT  /api/config/platform           — update active vendor
GET  /api/config/platform/{vendor}/products — full catalog for a vendor

Exposes get_platform_context() as a FastAPI dependency injected into
downstream routers that need vendor-aware behavior.
"""

from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter()

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "platform.yaml"
_PLATFORMS_DIR = Path(__file__).parent.parent.parent / "config" / "platforms"
_COMPETITIVE_DIR = Path(__file__).parent.parent.parent / "config" / "competitive"

SUPPORTED_VENDORS = ["google", "microsoft", "aws", "oracle", "salesforce", "ibm"]


# ── Pydantic schemas ──────────────────────────────────────────────────────


class PlatformUpdate(BaseModel):
    vendor: str


class PlatformContext(BaseModel):
    """Injected into request state for downstream use."""

    vendor: str
    display_name: str
    products: list[dict[str, Any]]
    workload_map: dict[str, list[str]]
    signal_keywords: list[str]


# ── Helpers ───────────────────────────────────────────────────────────────


def _load_active_vendor() -> str:
    with open(_CONFIG_PATH) as f:
        config = yaml.safe_load(f)
    return config.get("active_vendor", "google")


def _load_vendor_catalog(vendor: str) -> dict[str, Any]:
    vendor_file = _PLATFORMS_DIR / f"{vendor}.yaml"
    if not vendor_file.exists():
        raise HTTPException(status_code=404, detail=f"Product catalog not found for {vendor}")
    with open(vendor_file) as f:
        return yaml.safe_load(f)


def map_workload(vendor: str, workload: str) -> list[str]:
    """Return product IDs mapped to a workload for a given vendor.

    Args:
        vendor: Vendor identifier (e.g. "google").
        workload: Workload key (e.g. "ai_ml", "data_analytics").

    Returns:
        List of product IDs, or empty list if workload not found.
    """
    try:
        catalog = _load_vendor_catalog(vendor)
        return catalog.get("workload_map", {}).get(workload, [])
    except HTTPException:
        return []


# ── FastAPI dependency ────────────────────────────────────────────────────


async def get_platform_context() -> PlatformContext:
    """FastAPI dependency — inject active platform context into any route.

    Usage::

        @router.get("/something")
        async def my_route(platform: PlatformContext = Depends(get_platform_context)):
            vendor = platform.vendor
            keywords = platform.signal_keywords
    """
    vendor = _load_active_vendor()
    catalog = _load_vendor_catalog(vendor)
    return PlatformContext(
        vendor=vendor,
        display_name=catalog.get("display_name", vendor),
        products=catalog.get("products", []),
        workload_map=catalog.get("workload_map", {}),
        signal_keywords=catalog.get("signal_keywords", []),
    )


# ── Routes ────────────────────────────────────────────────────────────────


@router.get("/platform")
async def get_platform(context: PlatformContext = Depends(get_platform_context)):
    """Get the current active platform vendor context with full product catalog."""
    return {
        "active_vendor": context.vendor,
        "display_name": context.display_name,
        "products": context.products,
        "workload_map": context.workload_map,
        "signal_keywords": context.signal_keywords,
        "supported_vendors": SUPPORTED_VENDORS,
    }


@router.put("/platform")
async def update_platform(update: PlatformUpdate):
    """Update the active platform vendor context."""
    if update.vendor not in SUPPORTED_VENDORS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported vendor '{update.vendor}'. Choose from: {SUPPORTED_VENDORS}",
        )

    with open(_CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    config["active_vendor"] = update.vendor

    with open(_CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    # Return the full updated context
    catalog = _load_vendor_catalog(update.vendor)
    return {
        "active_vendor": update.vendor,
        "display_name": catalog.get("display_name", update.vendor),
        "message": f"Platform context updated to {update.vendor}",
    }


@router.get("/platform/{vendor}/products")
async def get_vendor_products(vendor: str):
    """Get the full product catalog for a specific vendor."""
    if vendor not in SUPPORTED_VENDORS:
        raise HTTPException(status_code=404, detail=f"Vendor '{vendor}' not found")
    return _load_vendor_catalog(vendor)


@router.get("/platform/competitive/{seller_vendor}/vs/{competitor_vendor}")
async def get_competitive_battlecard(seller_vendor: str, competitor_vendor: str):
    """Get the competitive battle card for a vendor matchup."""
    filename = f"{seller_vendor}_vs_{competitor_vendor}.yaml"
    battlecard_path = _COMPETITIVE_DIR / filename
    if not battlecard_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No battle card found for {seller_vendor} vs {competitor_vendor}",
        )
    with open(battlecard_path) as f:
        return yaml.safe_load(f)
