"""
mcp_server/server.py — MCP Server wrapper for ACD-Agent graph tools.

Verified with official Python MCP SDK:
- Uses MCPServer class from mcp.server.
- Decorates functions with @server.tool().
- Runs over stdio by default.
- Thin wrapper: delegates all logic to core.tools.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mcp.server import MCPServer

from core import tools

server = MCPServer(
    name="ownership-lens",
    description="FalkorDB investigation tools for offshore control and ownership networks.",
    version="1.0.0",
)


@server.tool()
def resolve_entity(name: str, limit: int = 5) -> str:
    """Resolve an entity name to a node_id via full-text search and exact matching."""
    res = tools.resolve_entity(name=name, limit=limit)
    return res.model_dump_json()


@server.tool()
def ownership_chain(entity_id: str, max_depth: int = 2) -> str:
    """Traverse ownership, shareholding, and officer paths from the entity up to max_depth (1..3)."""
    res = tools.ownership_chain(entity_id=entity_id, max_depth=max_depth)
    return res.model_dump_json()


@server.tool()
def shared_links(entity_id: str, limit: int = 10) -> str:
    """Find hub nodes (officers, addresses, intermediaries) connected to this entity and their degree."""
    res = tools.shared_links(entity_id=entity_id, limit=limit)
    return res.model_dump_json()


@server.tool()
def path_between(a_id: str, b_id: str, max_depth: int = 3) -> str:
    """Find shortest weighted path between two entity nodes within max_depth."""
    res = tools.path_between(a_id=a_id, b_id=b_id, max_depth=max_depth)
    return res.model_dump_json()


@server.tool()
def cluster_view(entity_id: str, max_depth: int = 2, node_cap: int = 500) -> str:
    """Compute PageRank, Betweenness, and Community Detection on the entity's 2-hop neighborhood."""
    res = tools.cluster_view(entity_id=entity_id, max_depth=max_depth, node_cap=node_cap)
    return res.model_dump_json()


@server.tool()
def recall_cases(entity_id: str, limit: int = 5) -> str:
    """Retrieve prior investigation decisions and cited evidence associated with this entity within 2 hops."""
    res = tools.recall_cases(entity_id=entity_id, limit=limit)
    return res.model_dump_json()


@server.tool()
def record_decision(
    entity_id: str,
    verdict: str,
    depth: int,
    evidence_ids: list[str],
    rule_ids: list[str],
    memo: str = "",
) -> str:
    """Write back an investigation decision as a Case node with ABOUT and CITED relationships."""
    res = tools.record_decision(
        entity_id=entity_id,
        verdict=verdict,
        depth=depth,
        evidence_ids=evidence_ids,
        rule_ids=rule_ids,
        memo=memo,
    )
    return json.dumps(res)


if __name__ == "__main__":
    server.run()
