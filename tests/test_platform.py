"""Tests for Phase 2 — Platform Vendor Context."""

import pytest
from fastapi.testclient import TestClient

from src.api.config import map_workload, get_platform_context, SUPPORTED_VENDORS
from src.main import app

client = TestClient(app)


# ── map_workload ──────────────────────────────────────────────────────────


def test_map_workload_google_ai_ml():
    products = map_workload("google", "ai_ml")
    assert "vertex_ai" in products


def test_map_workload_microsoft_data_analytics():
    products = map_workload("microsoft", "data_analytics")
    assert "fabric" in products


def test_map_workload_unknown_workload_returns_empty():
    result = map_workload("google", "nonexistent_workload")
    assert result == []


def test_map_workload_unknown_vendor_returns_empty():
    result = map_workload("nonexistent_vendor", "ai_ml")
    assert result == []


# ── GET /api/config/platform ──────────────────────────────────────────────


def test_get_platform_returns_vendor():
    response = client.get("/api/config/platform")
    assert response.status_code == 200
    data = response.json()
    assert data["active_vendor"] in SUPPORTED_VENDORS


def test_get_platform_returns_products():
    response = client.get("/api/config/platform")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["products"], list)
    assert len(data["products"]) > 0


def test_get_platform_returns_signal_keywords():
    response = client.get("/api/config/platform")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["signal_keywords"], list)
    assert len(data["signal_keywords"]) > 0


def test_get_platform_returns_workload_map():
    response = client.get("/api/config/platform")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["workload_map"], dict)


# ── GET /api/config/platform/{vendor}/products ────────────────────────────


def test_get_vendor_products_google():
    response = client.get("/api/config/platform/google/products")
    assert response.status_code == 200
    data = response.json()
    assert data["vendor"] == "google"
    assert len(data["products"]) >= 5


def test_get_vendor_products_invalid_vendor():
    response = client.get("/api/config/platform/fakecorp/products")
    assert response.status_code == 404


# ── Competitive battle card ───────────────────────────────────────────────


def test_get_competitive_battlecard_google_vs_aws():
    response = client.get("/api/config/platform/competitive/google/vs/aws")
    assert response.status_code == 200
    data = response.json()
    assert data["seller_vendor"] == "google"
    assert data["competitor_vendor"] == "aws"
    assert "win_themes" in data
    assert "competitive_battlecard" in data


def test_get_competitive_battlecard_missing_pair():
    response = client.get("/api/config/platform/competitive/oracle/vs/ibm")
    assert response.status_code == 404


# ── All vendor catalogs loadable ─────────────────────────────────────────


@pytest.mark.parametrize("vendor", SUPPORTED_VENDORS)
def test_all_vendor_catalogs_load(vendor):
    response = client.get(f"/api/config/platform/{vendor}/products")
    assert response.status_code == 200
    data = response.json()
    assert data["vendor"] == vendor
    assert len(data["products"]) > 0
    assert "workload_map" in data
    assert "signal_keywords" in data
