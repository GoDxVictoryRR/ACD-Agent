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


def test_evaluate_unknown_entity():
    # Resolution status unknown_entity must yield insufficient_evidence
    evidence = {
        "resolved_entity": {"status": "unknown_entity", "name": "Ghost Corp"},
    }
    res = evaluate(evidence, max_depth=2)
    assert res.verdict == "insufficient_evidence"
    assert not res.resolved


def test_evaluate_ambiguous_entity():
    # Resolution status ambiguous must yield insufficient_evidence
    evidence = {
        "resolved_entity": {"status": "ambiguous", "name": "Multiple Matches Ltd"},
    }
    res = evaluate(evidence, max_depth=2)
    assert res.verdict == "insufficient_evidence"
    assert not res.resolved


def test_evaluate_isolated_zero_links():
    # Degree 0 entity returns insufficient_evidence, never clear
    evidence = {
        "resolved_entity": {"id": "E1", "name": "Isolated Corp", "status": "ok"},
        "ownership_chain": [],
        "shared_links": [],
    }
    res = evaluate(evidence, max_depth=2)
    assert res.verdict == "insufficient_evidence"
    assert res.total_links == 0


def test_evaluate_isolated_single_link():
    # Degree 1 entity (< MIN_LINKS=2) returns insufficient_evidence, never clear
    evidence = {
        "resolved_entity": {"id": "E1", "name": "Low Link Corp", "status": "ok"},
        "ownership_chain": [{"nodes": [{"id": "E1", "name": "Low Link Corp"}]}],
        "shared_links": [],
    }
    res = evaluate(evidence, max_depth=2)
    assert res.verdict == "insufficient_evidence"
    assert res.total_links == 1


def test_evaluate_clean_entity_clear_display():
    # Clean entity with >= 2 links returns clear and displays "No indicators found within depth N"
    evidence = {
        "resolved_entity": {"id": "E4", "name": "Clean Corp", "status": "ok"},
        "ownership_chain": [{"nodes": [{"id": "E4", "name": "Clean Corp"}, {"id": "A1", "name": "12 Shirley Street"}]}],
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
    res = evaluate(evidence, max_depth=3)
    assert res.verdict == "clear"
    assert res.display_verdict == "No indicators found within depth 3"
    assert len(res.findings) == 0


def test_path_to_non_watchlist_node_never_escalates():
    # Path tagging: every path carries target id and is_watchlist flag.
    # A path to a non-watchlist node (is_watchlist=False) NEVER escalates.
    evidence = {
        "resolved_entity": {"id": "E1", "name": "Oceanic Star Maritime", "status": "ok"},
        "ownership_chain": [{"nodes": [{"id": "E1", "name": "Oceanic Star Maritime"}, {"id": "A1", "name": "HQ"}]}],
        "shared_links": [{"hub_type": "Address", "hub_name": "HQ", "hub_id": "A1", "linked_count": 1}],
        "paths_to_watchlist": [
            {
                "target_id": "NON_WATCHLIST_NODE",
                "target_name": "Benign Partner Ltd",
                "is_watchlist": False,
                "path_weight": 2.0,
                "nodes": [
                    {"id": "E1", "name": "Oceanic Star Maritime"},
                    {"id": "O1", "name": "Director"},
                    {"id": "NON_WATCHLIST_NODE", "name": "Benign Partner Ltd"},
                ],
            }
        ],
    }
    res = evaluate(evidence, max_depth=3, watchlist=["OTHER_TARGET"])
    assert res.verdict != "escalate"
    assert not any(f.rule_id in ("WATCHLIST_PATH", "PATH_REDUNDANCY", "PATH_DEPENDENCY") for f in res.findings)


def test_path_redundancy_independent_paths_escalate():
    # >= 2 node-disjoint paths -> escalate, ledger says "independent paths"
    evidence = {
        "resolved_entity": {"id": "E1", "name": "Alpha Corp", "status": "ok"},
        "ownership_chain": [{"nodes": [{"id": "E1", "name": "Alpha Corp"}, {"id": "A1", "name": "Addr"}]}],
        "shared_links": [{"hub_type": "Address", "hub_name": "Addr", "hub_id": "A1", "linked_count": 1}],
        "paths_to_watchlist": [
            {
                "target_id": "TARGET_WL",
                "target_name": "Watchlisted Entity",
                "is_watchlist": True,
                "path_weight": 4.0,
                "disjoint_paths_count": 2,
                "independent_paths": True,
                "exposure_depends_on": None,
                "nodes": [
                    {"id": "E1", "name": "Alpha Corp"},
                    {"id": "O1", "name": "Director 1"},
                    {"id": "TARGET_WL", "name": "Watchlisted Entity"},
                ],
            }
        ],
    }
    res = evaluate(evidence, max_depth=3)
    assert res.verdict == "escalate"
    redundancy_findings = [f for f in res.findings if f.rule_id == "PATH_REDUNDANCY"]
    assert len(redundancy_findings) == 1
    assert "independent paths" in redundancy_findings[0].text
    assert redundancy_findings[0].severity == "high"


def test_path_dependency_single_intermediate_review():
    # A single path through one intermediate node -> review, ledger names it "exposure depends on <node>"
    evidence = {
        "resolved_entity": {"id": "E1", "name": "Alpha Corp", "status": "ok"},
        "ownership_chain": [{"nodes": [{"id": "E1", "name": "Alpha Corp"}, {"id": "A1", "name": "Addr"}]}],
        "shared_links": [{"hub_type": "Address", "hub_name": "Addr", "hub_id": "A1", "linked_count": 1}],
        "paths_to_watchlist": [
            {
                "target_id": "TARGET_WL",
                "target_name": "Watchlisted Entity",
                "is_watchlist": True,
                "path_weight": 4.0,
                "disjoint_paths_count": 1,
                "independent_paths": False,
                "exposure_depends_on": "MOSSFON SUBSCRIBERS LTD.",
                "nodes": [
                    {"id": "E1", "name": "Alpha Corp"},
                    {"id": "O_MOSSFON", "name": "MOSSFON SUBSCRIBERS LTD."},
                    {"id": "TARGET_WL", "name": "Watchlisted Entity"},
                ],
            }
        ],
    }
    res = evaluate(evidence, max_depth=3)
    assert res.verdict == "review"
    dep_findings = [f for f in res.findings if f.rule_id == "PATH_DEPENDENCY"]
    assert len(dep_findings) == 1
    assert "exposure depends on MOSSFON SUBSCRIBERS LTD." in dep_findings[0].text
    assert dep_findings[0].severity == "medium"


def test_community_watchlist_firing():
    # No weighted path within depth, same community as watchlist entity -> review
    evidence = {
        "resolved_entity": {"id": "E1", "name": "Alpha Corp", "status": "ok"},
        "ownership_chain": [{"nodes": [{"id": "E1", "name": "Alpha Corp"}, {"id": "A1", "name": "Addr"}]}],
        "shared_links": [{"hub_type": "Address", "hub_name": "Addr", "hub_id": "A1", "linked_count": 1}],
        "paths_to_watchlist": [],
        "cluster_view": [
            {
                "shared_watchlist_communities": [
                    {
                        "watchlist_name": "Bad Actor Inc",
                        "watchlist_id": "WL_99",
                        "community_id": 3,
                    }
                ],
                "high_centrality_nodes": [],
            }
        ],
    }
    res = evaluate(evidence, max_depth=2, watchlist=["Bad Actor Inc"])
    assert res.verdict == "review"
    cw_findings = [f for f in res.findings if f.rule_id == "COMMUNITY_WATCHLIST"]
    assert len(cw_findings) == 1
    assert "same network community" in cw_findings[0].text
    assert cw_findings[0].severity == "medium"


def test_community_watchlist_not_firing_when_path_exists():
    # If a direct high-severity path already exists, COMMUNITY_WATCHLIST does not fire redundantly
    evidence = {
        "resolved_entity": {"id": "E1", "name": "Alpha Corp", "status": "ok"},
        "ownership_chain": [{"nodes": [{"id": "E1", "name": "Alpha Corp"}, {"id": "A1", "name": "Addr"}]}],
        "shared_links": [{"hub_type": "Address", "hub_name": "Addr", "hub_id": "A1", "linked_count": 1}],
        "paths_to_watchlist": [
            {
                "target_id": "WL_99",
                "target_name": "Bad Actor Inc",
                "is_watchlist": True,
                "path_weight": 2.0,
                "disjoint_paths_count": 2,
                "independent_paths": True,
                "nodes": [
                    {"id": "E1", "name": "Alpha Corp"},
                    {"id": "WL_99", "name": "Bad Actor Inc"},
                ],
            }
        ],
        "cluster_view": [
            {
                "shared_watchlist_communities": [
                    {
                        "watchlist_name": "Bad Actor Inc",
                        "watchlist_id": "WL_99",
                        "community_id": 3,
                    }
                ],
                "high_centrality_nodes": [],
            }
        ],
    }
    res = evaluate(evidence, max_depth=2, watchlist=["Bad Actor Inc"])
    assert res.verdict == "escalate"
    assert not any(f.rule_id == "COMMUNITY_WATCHLIST" for f in res.findings)


def test_hub_centrality_firing():
    # Betweenness above calibrated threshold -> review
    evidence = {
        "resolved_entity": {"id": "E1", "name": "Alpha Corp", "status": "ok"},
        "ownership_chain": [{"nodes": [{"id": "E1", "name": "Alpha Corp"}, {"id": "A1", "name": "Addr"}]}],
        "shared_links": [{"hub_type": "Address", "hub_name": "Addr", "hub_id": "A1", "linked_count": 1}],
        "paths_to_watchlist": [],
        "cluster_view": [
            {
                "shared_watchlist_communities": [],
                "high_centrality_nodes": [
                    {
                        "id": "E1",
                        "name": "Alpha Corp",
                        "label": "Entity",
                        "score": 0.125,
                    }
                ],
            }
        ],
    }
    res = evaluate(evidence, max_depth=2)
    assert res.verdict == "review"
    hc_findings = [f for f in res.findings if f.rule_id == "HUB_CENTRALITY"]
    assert len(hc_findings) == 1
    assert "major structural bridge" in hc_findings[0].text


def test_hub_centrality_not_firing():
    # Empty high centrality nodes -> clear
    evidence = {
        "resolved_entity": {"id": "E1", "name": "Alpha Corp", "status": "ok"},
        "ownership_chain": [{"nodes": [{"id": "E1", "name": "Alpha Corp"}, {"id": "A1", "name": "Addr"}]}],
        "shared_links": [{"hub_type": "Address", "hub_name": "Addr", "hub_id": "A1", "linked_count": 1}],
        "paths_to_watchlist": [],
        "cluster_view": [
            {
                "shared_watchlist_communities": [],
                "high_centrality_nodes": [],
            }
        ],
    }
    res = evaluate(evidence, max_depth=2)
    assert res.verdict == "clear"
    assert not any(f.rule_id == "HUB_CENTRALITY" for f in res.findings)


def test_evaluate_address_hub_review():
    evidence = {
        "resolved_entity": {"id": "E2", "name": "Orion Logistics", "status": "ok"},
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
        "resolved_entity": {"id": "E3", "name": "Silverline Capital", "status": "ok"},
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


def test_dewburn_degree_one_returns_insufficient_evidence():
    """A3: Degree 1 entity connected solely to an intermediary provider must return insufficient_evidence."""
    evidence = {
        "resolved_entity": {"id": "10000290", "name": "Dewburn Enterprises Inc.", "status": "ok"},
        "ownership_chain": [
            {
                "nodes": [
                    {"id": "10000290", "name": "Dewburn Enterprises Inc.", "label": "Entity"},
                    {"id": "11011863", "name": "MOSSACK FONSECA & CO.", "label": "Intermediary"},
                ],
                "relationships": [{"type": "INTERMEDIARY_OF"}],
            }
        ],
        "shared_links": [],  # Intermediary is a service provider, not a client risk hub
        "paths_to_watchlist": [],
        "cluster_view": [{"high_centrality_nodes": [], "shared_watchlist_communities": []}],
    }
    res = evaluate(evidence, max_depth=2)
    assert res.verdict == "insufficient_evidence"
    assert res.total_links == 1
    assert len(res.findings) == 0


def test_intermediary_provider_size_never_flags_entity():
    """A2: Intermediaries are service providers. Large intermediary client volume does not flag target entity."""
    evidence = {
        "resolved_entity": {"id": "E_CLIENT", "name": "Standard Client Ltd", "status": "ok"},
        "ownership_chain": [
            {
                "nodes": [
                    {"id": "E_CLIENT", "name": "Standard Client Ltd", "label": "Entity"},
                    {"id": "I_BIG", "name": "Mega Intermediary Corp", "label": "Intermediary"},
                ],
                "relationships": [{"type": "INTERMEDIARY_OF"}],
            },
            {
                "nodes": [
                    {"id": "E_CLIENT", "name": "Standard Client Ltd", "label": "Entity"},
                    {"id": "O_DIR", "name": "Sole Director Person", "label": "Officer"},
                ],
                "relationships": [{"type": "OFFICER_OF"}],
            },
        ],
        "shared_links": [],  # Provider hubs not in shared links
        "paths_to_watchlist": [],
        "cluster_view": [],
    }
    res = evaluate(evidence, max_depth=2)
    # 2 direct links, 0 findings -> clean entity clears without intermediary flag
    assert res.verdict == "clear"
    assert not any("INTERMEDIARY" in f.rule_id for f in res.findings)

