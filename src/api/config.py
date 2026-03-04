from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "platform.yaml"
_PLATFORMS_DIR = Path(__file__).parent.parent.parent / "config" / "platforms"

SUPPORTED_VENDORS = ["google", "microsoft", "aws", "oracle", "salesforce", "ibm"]


class PlatformUpdate(BaseModel):
    vendor: str


@router.get("/platform")
async def get_platform():
    """Get the current active platform vendor context."""
    with open(_CONFIG_PATH) as f:
        config = yaml.safe_load(f)
    return {"active_vendor": config.get("active_vendor"), "supported_vendors": SUPPORTED_VENDORS}


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

    return {"active_vendor": update.vendor, "message": f"Platform context updated to {update.vendor}"}


@router.get("/platform/{vendor}/products")
async def get_vendor_products(vendor: str):
    """Get the product catalog for a specific vendor."""
    if vendor not in SUPPORTED_VENDORS:
        raise HTTPException(status_code=404, detail=f"Vendor '{vendor}' not found")

    vendor_file = _PLATFORMS_DIR / f"{vendor}.yaml"
    if not vendor_file.exists():
        raise HTTPException(status_code=404, detail=f"Product catalog not found for {vendor}")

    with open(vendor_file) as f:
        catalog = yaml.safe_load(f)

    return catalog
