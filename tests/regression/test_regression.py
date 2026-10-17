"""
tests/regression/test_regression.py — Regression suite across 10 distinct entities.
Verifies consistency of verdicts across depth variations and rules execution.
Supports both ICIJ and Synthetic data sources dynamically.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent.fallback import run_deterministic_investigation
from core.config import DATA_SOURCE
from core.db import ping

REGRESSION_DIR = Path(__file__).resolve().parent


@pytest.fixture(scope="module")
def regression_config():
    if DATA_SOURCE == "icij":
        expected_file = REGRESSION_DIR / "expected_icij.json"
        watchlist = ["TIANSHENG INDUSTRY AND TRADING CO., LTD."]
        primary_entity = "MOSSACK FONSECA & CO. (SAMOA) LIMITED."
    else:
        expected_file = REGRESSION_DIR / "expected.json"
        watchlist = ["Ironclad Sanctions Entity Inc", "Apex Nominees Ltd"]
        primary_entity = "Blue Star Maritime Holdings Ltd"

    with open(expected_file, encoding="utf-8") as f:
        expected = json.load(f)

    return {
        "expected": expected,
        "watchlist": watchlist,
        "primary_entity": primary_entity,
    }


def test_regression_verdicts(regression_config):
    if not ping():
        pytest.skip("FalkorDB is not running. Start Docker to run live regression tests.")

    expected_verdicts = regression_config["expected"]
    watchlist = regression_config["watchlist"]
    primary = regression_config["primary_entity"]

    # 1. Test Depth 1 vs Depth 3 flip on primary entity
    r_d1 = run_deterministic_investigation(primary, watchlist=watchlist, depth=1)
    r_d3 = run_deterministic_investigation(primary, watchlist=watchlist, depth=3)

    assert r_d1["verdict"] == expected_verdicts[primary]["depth_1"]
    assert r_d3["verdict"] == expected_verdicts[primary]["depth_3"]
    # Invariant: depth 1 vs depth 3 must flip verdict to prove graph value!
    assert r_d1["verdict"] != r_d3["verdict"]

    # 2. Test remaining 9 entities
    for entity_name, exp in expected_verdicts.items():
        if entity_name == primary:
            continue
        exp_depth = 2
        exp_verdict = exp.get("depth_2")
        res = run_deterministic_investigation(entity_name, watchlist=watchlist, depth=exp_depth)
        assert res["verdict"] == exp_verdict, (
            f"Mismatch for {entity_name}: got {res['verdict']}, expected {exp_verdict}"
        )
