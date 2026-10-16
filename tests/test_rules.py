"""
tests/test_rules.py — Unit tests for the deterministic rules engine.
Tests rules evaluation in total isolation without DB or LLM.
"""
from __future__ import annotations

from core.rules import evaluate


def test_evaluate_unresolved_entity():
    evidence = {"resolved_entity": None}
    res = evaluate(evidence, max_depth=2)
    assert res.verdict == "insufficient_evidence"
    assert not res.resolved


def test_evaluate_insufficient_links():
    evidence = {
        "resolved_entity": {"id": "E1", "name": "Isolated Ltd"},
        "ownership_chain": [],
        "shared_links": [],
    }
    res = evaluate(evidence, max_depth=2)
    assert res.verdict == "insufficient_evidence"
    assert res.total_links == 0


def test_evaluate_watchlist_path_escalate():
    evidence = {
        "resolved_entity": {"id": "E1", "name": "Blue Star Maritime"},
        "ownership_chain": [{"nodes": [{"id": "E1", "name": "Blue Star Maritime"}]}],
        "shared_links": [],
        "paths_to_watchlist": [
            {
                "path_weight": 4.0,
                "nodes": [
                    {"id": "E1", "name": "Blue Star Maritime"},
                    {"id": "O1", "name": "Director"},
                    {"id": "E_TARGET", "name": "Sanctioned Entity"},
                ],
            }
        ],
    }
    res = evaluate(evidence, max_depth=3)
    assert res.verdict == "escalate"
    findings = res.findings
    assert any(f.rule_id == "WATCHLIST_PATH" and f.severity == "high" for f in findings)


def test_evaluate_address_hub_review():
    evidence = {
        "resolved_entity": {"id": "E2", "name": "Orion Logistics"},
        "ownership_chain": [{"nodes": [{"id": "E2", "name": "Orion Logistics"}]}],
        "shared_links": [
            {
                "hub_type": "Address",
                "hub_name": "Suite 301, St. James Court",
                "hub_id": "A_HUB",
                "linked_count": 55,
            }
        ],
    }
    res = evaluate(evidence, max_depth=2)
    assert res.verdict == "review"
    assert any(f.rule_id == "ADDRESS_HUB" and f.severity == "medium" for f in res.findings)


def test_evaluate_nominee_officer_hub_review():
    evidence = {
        "resolved_entity": {"id": "E3", "name": "Silverline Capital"},
        "ownership_chain": [{"nodes": [{"id": "E3", "name": "Silverline Capital"}]}],
        "shared_links": [
            {
                "hub_type": "Officer",
                "hub_name": "John Alexander Vance",
                "hub_id": "O_VANCE",
                "linked_count": 45,
            }
        ],
    }
    res = evaluate(evidence, max_depth=2)
    assert res.verdict == "review"
    assert any(f.rule_id == "NOMINEE_OFFICER_HUB" and f.severity == "medium" for f in res.findings)


def test_evaluate_clean_entity_clear():
    evidence = {
        "resolved_entity": {"id": "E4", "name": "Solitary Enterprises"},
        "ownership_chain": [
            {"nodes": [{"id": "E4", "name": "Solitary Enterprises"}, {"id": "A1", "name": "12 Shirley Street"}]}
        ],
        "shared_links": [
            {
                "hub_type": "Address",
                "hub_name": "12 Shirley Street",
                "hub_id": "A1",
                "linked_count": 1,
            }
        ],
        "paths_to_watchlist": [],
    }
    res = evaluate(evidence, max_depth=2)
    assert res.verdict == "clear"
    assert len(res.findings) == 0
