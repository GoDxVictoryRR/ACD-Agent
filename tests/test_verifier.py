"""
tests/test_verifier.py — Unit tests for the memo verifier and template generator.
"""

from __future__ import annotations

from core.rules import evaluate
from core.verifier import generate_template_memo, verify_memo


def test_verify_memo_valid():
    evidence = {
        "resolved_entity": {"id": "E1", "name": "Oceanic Star Maritime Holdings Ltd"},
        "ownership_chain": [
            {
                "nodes": [
                    {"id": "E1", "name": "Oceanic Star Maritime Holdings Ltd"},
                    {"id": "O1", "name": "Marcus Sterling"},
                ]
            }
        ],
        "shared_links": [],
    }

    valid_memo = (
        "Investigation of Oceanic Star Maritime Holdings Ltd revealed connections to Marcus Sterling. "
        "Further human review is recommended."
    )
    is_valid, unverified = verify_memo(valid_memo, evidence)
    assert is_valid
    assert len(unverified) == 0


def test_verify_memo_rejects_hallucinated_name():
    evidence = {
        "resolved_entity": {"id": "E1", "name": "Oceanic Star Maritime Holdings Ltd"},
        "ownership_chain": [],
        "shared_links": [],
    }

    # Mentions a made-up entity "Acme Offshore Laundering Inc"
    hallucinated_memo = (
        "Oceanic Star Maritime Holdings Ltd was found to be co-owned by Acme Offshore Laundering Inc. "
        "This indicates extreme exposure."
    )
    is_valid, unverified = verify_memo(hallucinated_memo, evidence)
    assert not is_valid
    assert any("Acme Offshore Laundering" in name for name in unverified)


def test_generate_template_memo():
    evidence = {
        "resolved_entity": {"id": "E1", "name": "Oceanic Star Maritime Holdings Ltd"},
        "ownership_chain": [{"nodes": [{"id": "E1", "name": "Oceanic Star Maritime"}, {"id": "A1", "name": "Addr"}]}],
        "shared_links": [{"hub_type": "Address", "hub_name": "Addr", "hub_id": "A1", "linked_count": 1}],
        "paths_to_watchlist": [
            {
                "is_watchlist": True,
                "path_weight": 4.0,
                "nodes": [
                    {"id": "E1", "name": "Oceanic Star Maritime"},
                    {"id": "O1", "name": "Marcus Sterling"},
                    {"id": "E_TARGET", "name": "Alpha Watchlist Entity Inc"},
                ],
            }
        ],
    }
    eval_res = evaluate(evidence, max_depth=3)
    memo = generate_template_memo("Oceanic Star Maritime Holdings Ltd", eval_res, depth=3)
    assert "INVESTIGATION MEMORANDUM" in memo
    assert "ESCALATE" in memo
    assert "Disclaimer" in memo
