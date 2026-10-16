"""
tests/test_api.py — Unit tests for the FastAPI backend using TestClient.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "db" in data
    assert "graph" in data
    assert "mode" in data
    assert "rss_mb" in data


def test_demo_endpoint():
    res = client.get("/demo")
    assert res.status_code == 200
    data = res.json()
    assert "demo_entities" in data
    assert "watchlist" in data


def test_investigate_validation():
    # Empty entity rejected
    res = client.post("/investigate", json={"entity": "", "depth": 2})
    assert res.status_code == 400

    # Depth out of bounds rejected
    res = client.post("/investigate", json={"entity": "Valid Name", "depth": 99})
    assert res.status_code == 422


def test_entities_search():
    res = client.get("/entities/search?q=")
    assert res.status_code == 200
    assert res.json() == []


def test_replay_not_found():
    res = client.get("/replay/nonexistent_slug_12345")
    assert res.status_code == 404
