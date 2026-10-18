"""
tests/test_tools.py — Unit tests for the 7 typed graph tools and MCP wrapper.

Runs against a temporary fixture graph test_ownership_<uuid8> and tears it down.
"""

from __future__ import annotations

import asyncio
import uuid

import pytest

from core import tools
from core.db import drop_graph, rw
from mcp_server.server import server


@pytest.fixture(scope="module")
def fixture_graph():
    graph_name = f"test_tools_{uuid.uuid4().hex[:8]}"

    # Populate a tiny test ownership network
    setup_q = """
    CREATE (e1:Entity {node_id: 'E_ALPHA', name: 'Alpha Holding Corp', jurisdiction: 'BVI'})
    CREATE (e2:Entity {node_id: 'E_BETA', name: 'Beta Trading Ltd', jurisdiction: 'Panama'})
    CREATE (e3:Entity {node_id: 'E_TARGET', name: 'Designated Watchlist Corp', jurisdiction: 'Seychelles'})
    CREATE (o1:Officer {node_id: 'O_DIRECTOR', name: 'John Director', country: 'UK'})
    CREATE (a1:Address {node_id: 'A_SUITE', address: 'Suite 100 Portcullis', country: 'BVI'})

    CREATE (o1)-[:OFFICER_OF {link: 'Director', weight: 1.0}]->(e1)
    CREATE (o1)-[:OFFICER_OF {link: 'Director', weight: 1.0}]->(e2)
    CREATE (e1)-[:REGISTERED_ADDRESS {link: 'Office', weight: 3.0}]->(a1)
    CREATE (e2)-[:CONNECTED_TO {link: 'Associate', weight: 2.0}]->(e3)
    """
    try:
        rw(graph_name, setup_q)
    except Exception as exc:
        pytest.skip(f"FalkorDB not running, skipping live graph tests: {exc}")

    yield graph_name
    drop_graph(graph_name)


def test_resolve_entity_exact(fixture_graph):
    res = tools.resolve_entity("Alpha Holding Corp", graph_name=fixture_graph)
    assert res.status == "ok"
    assert len(res.data) == 1
    assert res.data[0]["id"] == "E_ALPHA"


def test_resolve_entity_unknown(fixture_graph):
    res = tools.resolve_entity("NonExistent Company XYZ", graph_name=fixture_graph)
    assert res.status == "unknown_entity"
    assert len(res.data) == 0


def test_resolve_entity_sql_injection_safe(fixture_graph):
    # Malicious Cypher injection string should be treated as literal data
    malicious = "' OR 1=1 WITH e DETACH DELETE e //"
    res = tools.resolve_entity(malicious, graph_name=fixture_graph)
    assert res.status == "unknown_entity"


def test_ownership_chain(fixture_graph):
    res = tools.ownership_chain("E_ALPHA", max_depth=2, graph_name=fixture_graph)
    assert res.status == "ok"
    assert len(res.data) >= 1


def test_ownership_chain_depth_cap(fixture_graph):
    # Enforces max depth <= MAX_DEPTH even if requested depth is 99
    # MAX_DEPTH was bumped to 4 to support 3-hop demo contrast; evidence: core/config.py
    from core.config import MAX_DEPTH

    res = tools.ownership_chain("E_ALPHA", max_depth=99, graph_name=fixture_graph)
    assert res.params["max_depth"] <= MAX_DEPTH


def test_shared_links(fixture_graph):
    res = tools.shared_links("E_ALPHA", graph_name=fixture_graph)
    assert res.status == "ok"
    hubs = res.data
    assert any(h["hub_id"] == "O_DIRECTOR" for h in hubs)


def test_path_between(fixture_graph):
    res = tools.path_between("E_ALPHA", "E_TARGET", max_depth=3, graph_name=fixture_graph)
    assert res.status == "ok"
    assert len(res.data) >= 1
    assert res.data[0]["path_weight"] > 0


def test_cluster_view_and_cleanup(fixture_graph):
    res = tools.cluster_view("E_ALPHA", max_depth=2, graph_name=fixture_graph)
    assert res.status in ("ok", "empty")
    # Verify scratch graph was deleted (fixture_graph still works)
    from core.db import ro as db_ro

    scratch_check = db_ro(fixture_graph, "RETURN 1")
    assert scratch_check["rows"][0][0] == 1
    # Verify cluster result has viz keys if ok
    if res.status == "ok" and res.data:
        assert "viz_nodes" in res.data[0]
        assert "viz_edges" in res.data[0]


def test_record_decision_idempotent(fixture_graph):
    fixed_case_id = "case_test_idempotent_123"
    rec1 = tools.record_decision(
        entity_id="E_ALPHA",
        verdict="review",
        depth=2,
        evidence_ids=["O_DIRECTOR"],
        rule_ids=["OFFICER_HUB"],
        memo="Initial check",
        case_id=fixed_case_id,
        graph_name=fixture_graph,
    )
    rec2 = tools.record_decision(
        entity_id="E_ALPHA",
        verdict="review",
        depth=2,
        evidence_ids=["O_DIRECTOR"],
        rule_ids=["OFFICER_HUB"],
        memo="Repeat check",
        case_id=fixed_case_id,
        graph_name=fixture_graph,
    )
    assert rec1["case_id"] == rec2["case_id"]

    # Test recall_cases finds it
    recalled = tools.recall_cases("E_ALPHA", graph_name=fixture_graph)
    assert recalled.status == "ok"
    assert any(c["case_id"] == fixed_case_id for c in recalled.data)


def test_record_decision_invalid_verdict(fixture_graph):
    with pytest.raises(ValueError, match="Invalid verdict"):
        tools.record_decision(
            entity_id="E_ALPHA",
            verdict="guilty_of_fraud",  # Forbidden by Invariant 5 & 9
            depth=1,
            evidence_ids=[],
            rule_ids=[],
            graph_name=fixture_graph,
        )


def test_mcp_wrapper_tools_registered():
    loop = asyncio.new_event_loop()
    tools_list = loop.run_until_complete(server.list_tools())
    loop.close()
    tool_names = {t.name for t in tools_list}
    expected = {
        "resolve_entity",
        "ownership_chain",
        "shared_links",
        "path_between",
        "cluster_view",
        "recall_cases",
        "record_decision",
    }
    assert expected == tool_names


def test_resolve_entity_ambiguous_duplicate_names(fixture_graph):
    # Insert two entities with the exact same name in different jurisdictions
    rw(
        fixture_graph,
        """
        CREATE (:Entity {node_id: 'E_DUP1', name: 'Acme Duplicate Corp', jurisdiction: 'SAM', sourceID: 'Panama Papers', status: 'Active'})
        CREATE (:Entity {node_id: 'E_DUP2', name: 'Acme Duplicate Corp', jurisdiction: 'SEY', sourceID: 'Panama Papers', status: 'Defaulted'})
        """,
    )
    res = tools.resolve_entity("Acme Duplicate Corp", graph_name=fixture_graph)
    assert res.status == "ambiguous"
    assert len(res.data) == 2
    for cand in res.data:
        assert "node_id" in cand
        assert "jurisdiction" in cand
        assert "source" in cand
        assert "status" in cand
        assert cand["name"] == "Acme Duplicate Corp"
    node_ids = {c["node_id"] for c in res.data}
    assert node_ids == {"E_DUP1", "E_DUP2"}


def test_resolve_entity_by_node_id(fixture_graph):
    # Picking directly by node_id should resolve unambiguously
    rw(
        fixture_graph,
        "CREATE (:Entity {node_id: 'E_PICK_ID', name: 'Picked Entity Corp', jurisdiction: 'BVI', sourceID: 'Panama Papers', status: 'Active'})",
    )
    res = tools.resolve_entity("E_PICK_ID", graph_name=fixture_graph)
    assert res.status == "ok"
    assert len(res.data) == 1
    cand = res.data[0]
    assert cand["node_id"] == "E_PICK_ID"
    assert cand["name"] == "Picked Entity Corp"
    assert cand["jurisdiction"] == "BVI"
    assert cand["source"] == "Panama Papers"
    assert cand["status"] == "Active"
