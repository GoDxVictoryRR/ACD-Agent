"""
tests/regression/test_regression.py — Regression suite across 10 distinct entities.
Verifies consistency of verdicts across depth variations and rules execution.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent.fallback import run_deterministic_investigation
from core.db import ping

EXPECTED_FILE = Path(__file__).resolve().parent / "expected.json"


@pytest.fixture(scope="module")
def expected_verdicts():
    with open(EXPECTED_FILE, encoding="utf-8") as f:
        return json.load(f)


def test_regression_verdicts(expected_verdicts):
    if not ping():
        pytest.skip("FalkorDB is not running. Start Docker to run live regression tests.")

    watchlist = ["Ironclad Sanctions Entity Inc", "Apex Nominees Ltd"]

    # 1. Test Depth 1 vs Depth 3 flip on Blue Star Maritime
    bluestar = "Blue Star Maritime Holdings Ltd"
    r_d1 = run_deterministic_investigation(bluestar, watchlist=watchlist, depth=1)
    r_d3 = run_deterministic_investigation(bluestar, watchlist=watchlist, depth=3)

    assert r_d1["verdict"] == expected_verdicts[bluestar]["depth_1"]
    assert r_d3["verdict"] == expected_verdicts[bluestar]["depth_3"]
    # Invariant: depth 1 vs depth 3 must flip verdict to prove graph value!
    assert r_d1["verdict"] != r_d3["verdict"]

    # 2. Test remaining 9 entities
    for entity_name, exp in expected_verdicts.items():
        if entity_name == bluestar:
            continue
        exp_depth = 2
        exp_verdict = exp.get("depth_2")
        res = run_deterministic_investigation(entity_name, watchlist=watchlist, depth=exp_depth)
        assert res["verdict"] == exp_verdict, f"Mismatch for {entity_name}: got {res['verdict']}, expected {exp_verdict}"
