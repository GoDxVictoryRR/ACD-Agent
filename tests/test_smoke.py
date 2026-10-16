"""
tests/test_smoke.py — FalkorDB connection and query smoke test.

Verifies:
1. Connection to FalkorDB works.
2. Read-write query creates nodes and an edge in a temporary graph.
3. Read-only query reads them back.
4. Temporary graph is cleaned up.
"""
from __future__ import annotations

import uuid

from core.db import drop_graph, get_db, ro, rw


def test_falkordb_connection():
    db = get_db()
    assert db is not None


def test_smoke_graph_lifecycle():
    test_graph = f"smoke_{uuid.uuid4().hex[:8]}"

    try:
        # Create 2 nodes and 1 relationship
        create_res = rw(
            test_graph,
            """
            CREATE (a:Entity {name: 'Alpha Ltd', jurisdiction: 'BVI'})
            CREATE (b:Officer {name: 'Jane Doe', country: 'UK'})
            CREATE (b)-[:OFFICER_OF {role: 'Director'}]->(a)
            RETURN a.name, b.name
            """,
        )
        assert len(create_res["rows"]) == 1
        assert create_res["rows"][0][0] == "Alpha Ltd"
        assert create_res["rows"][0][1] == "Jane Doe"

        # Read back via read-only ro()
        read_res = ro(
            test_graph,
            """
            MATCH (o:Officer)-[r:OFFICER_OF]->(e:Entity)
            RETURN o.name, type(r), e.name
            """,
        )
        assert len(read_res["rows"]) == 1
        row = read_res["rows"][0]
        assert row[0] == "Jane Doe"
        assert row[1] == "OFFICER_OF"
        assert row[2] == "Alpha Ltd"
    finally:
        drop_graph(test_graph)
