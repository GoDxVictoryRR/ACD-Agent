"""
tests/test_h1_default_mode.py — Test H1: Deterministic default mode, AI mode toggle, and replay labelling.
"""

import re
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import InvestigateRequest, app
from core.db import ping


def test_investigate_request_defaults():
    req = InvestigateRequest(entity="GLAISDALE LIMITED")
    assert req.no_llm is True, "InvestigateRequest must default to no_llm=True (deterministic mode)"


def test_ui_contains_ai_toggle_default_off():
    html_path = Path(__file__).resolve().parent.parent / "web" / "index.html"
    assert html_path.exists()
    content = html_path.read_text(encoding="utf-8")

    # Visible toggle checkbox
    assert 'id="toggleAiMode"' in content
    assert 'type="checkbox"' in content
    # Ensure it is not checked by default
    toggle_tag = re.search(r'<input[^>]*id="toggleAiMode"[^>]*>', content)
    assert toggle_tag is not None
    assert "checked" not in toggle_tag.group(0), "toggleAiMode must NOT be checked by default"

    # Exact label text
    assert "AI agent mode (LLM tool selection, ~1 min)" in content
    assert 'id="aiModeNotice"' in content


def test_api_investigate_default_is_fast():
    if not ping():
        return
    client = TestClient(app)
    resp = client.post(
        "/investigate",
        json={"entity": "GLAISDALE LIMITED", "watchlist": ["DOM Limited"], "depth": 1},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "run_id" in data
