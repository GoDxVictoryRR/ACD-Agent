"""
core/tools.py — The 7 typed graph tools for ACD-Agent.

Invariants:
- All queries parameterized. No raw Cypher written or seen by LLM.
- Reads use ro(); writes only in record_decision and cluster_view scratch graph.
- Every read tool returns a ToolResult pydantic model.
- Case nodes and ABOUT/CITED edges are ALWAYS excluded from read traversals (Invariant: Case nodes
  must never pollute ownership path counts, link counts, or rule inputs).
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from core.config import (
    CLUSTER_NODE_CAP,
    GRAPH_NAME,
    MAX_DEPTH,
    OWNERSHIP_CHAIN_ROW_CAP,
    RECALL_CASES_LIMIT,
    RESOLVE_LIMIT,
    SHARED_LINKS_LIMIT,
    VERDICTS,
)
from core.db import drop_graph, ro, rw

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
# Relationship types that represent meta/audit edges — must NEVER appear in
# ownership traversals or rule inputs. This is enforced by excluding them in
# every read query and checked by scripts/check_invariants.py.
_META_RELS = frozenset({"ABOUT", "CITED"})

# Ownership relationship types used for traversal in ownership_chain
_OWNERSHIP_REL_TYPES = "OFFICER_OF|SHAREHOLDER_OF|INTERMEDIARY_OF|REGISTERED_ADDRESS|CONNECTED_TO|BENEFICIARY_OF|DIRECTOR_OF|UNDERLYING|SAME_NAME_AS|SAME_ADDRESS_AS|RELATED_ENTITY|ADDRESS_OF|SAME_AS|SAME_COMPANY_AS|SIMILAR"


def _node_display_name(node_map: dict) -> str:
    """Return the best display name for a node (name > address > node_id > 'unknown')."""
    return node_map.get("name") or node_map.get("address") or node_map.get("node_id") or "unknown"


class ToolResult(BaseModel):
    tool: str
    params: dict[str, Any] = Field(default_factory=dict)
    status: Literal["ok", "empty", "unknown_entity", "ambiguous", "error"]
    data: list[Any] = Field(default_factory=list)
    elapsed_ms: float = 0.0
    notes: str = ""


# ── Tool 1: resolve_entity ──────────────────────────────────────────────────
def resolve_entity(
    name: str,
    limit: int = RESOLVE_LIMIT,
    graph_name: str = GRAPH_NAME,
) -> ToolResult:
    """
    Resolve an entity name or node_id to an entity node.
    - If name matches node_id directly -> status: ok.
    - If exactly one case-insensitive exact name match -> status: ok.
    - If multiple exact matches or partial matches -> status: ambiguous with candidates
      containing (node_id, jurisdiction, source, status).
    - If no entity matches -> status: unknown_entity.
    """
    t0 = time.perf_counter()
    clean_name = name.strip()
    limit = max(1, min(limit, 10))

    if not clean_name:
        return ToolResult(
            tool="resolve_entity",
            params={"name": name, "limit": limit},
            status="unknown_entity",
            elapsed_ms=0.0,
            notes="Empty entity name provided",
        )

    def _build_candidate(r: list[Any]) -> dict[str, Any]:
        return {
            "id": r[0],
            "node_id": r[0],
            "name": r[1],
            "label": r[2],
            "jurisdiction": r[3] or "",
            "source": r[4] or "",
            "status": r[5] or "",
        }

    # 1. Check direct node_id match
    id_q = """
    MATCH (e:Entity {node_id: $name})
    RETURN e.node_id AS node_id, e.name AS name, labels(e)[0] AS label,
           coalesce(e.jurisdiction, '') AS jurisdiction,
           coalesce(e.sourceID, '') AS source,
           coalesce(e.status, '') AS status
    LIMIT 1
    """
    try:
        id_res = ro(graph_name, id_q, {"name": clean_name})
        id_rows = id_res.get("rows", [])
        if id_rows:
            elapsed = (time.perf_counter() - t0) * 1000
            return ToolResult(
                tool="resolve_entity",
                params={"name": name, "limit": limit},
                status="ok",
                data=[_build_candidate(id_rows[0])],
                elapsed_ms=round(elapsed, 2),
                notes=f"Direct node_id match found: '{clean_name}'",
            )
    except Exception as exc:
        logger.debug("Direct node_id match check error: %s", exc)

    # 2. Exact case-insensitive name match
    exact_q = """
    MATCH (e:Entity)
    WHERE toLower(e.name) = toLower($name)
    RETURN e.node_id AS node_id, e.name AS name, labels(e)[0] AS label,
           coalesce(e.jurisdiction, '') AS jurisdiction,
           coalesce(e.sourceID, '') AS source,
           coalesce(e.status, '') AS status
    LIMIT $limit
    """
    try:
        res = ro(graph_name, exact_q, {"name": clean_name, "limit": limit})
        rows = res.get("rows", [])
        if len(rows) == 1:
            elapsed = (time.perf_counter() - t0) * 1000
            return ToolResult(
                tool="resolve_entity",
                params={"name": name, "limit": limit},
                status="ok",
                data=[_build_candidate(rows[0])],
                elapsed_ms=round(elapsed, 2),
                notes="Single exact case-insensitive match found",
            )
        elif len(rows) > 1:
            elapsed = (time.perf_counter() - t0) * 1000
            candidates = [_build_candidate(r) for r in rows]
            return ToolResult(
                tool="resolve_entity",
                params={"name": name, "limit": limit},
                status="ambiguous",
                data=candidates,
                elapsed_ms=round(elapsed, 2),
                notes=f"Multiple exact matches found for '{clean_name}' ({len(candidates)} candidates) — disambiguate by node_id",
            )
    except Exception as exc:
        logger.debug("Exact match failed: %s", exc)

    # 3. Full-text search fallback, then contains fallback
    ft_q = """
    CALL db.idx.fulltext.queryNodes('Entity', $query)
    YIELD node
    RETURN node.node_id AS node_id, node.name AS name, labels(node)[0] AS label,
           coalesce(node.jurisdiction, '') AS jurisdiction,
           coalesce(node.sourceID, '') AS source,
           coalesce(node.status, '') AS status
    LIMIT $limit
    """
    candidates = []
    try:
        res = ro(graph_name, ft_q, {"query": clean_name, "limit": limit})
        for r in res.get("rows", []):
            candidates.append(_build_candidate(r))
    except Exception:
        contains_q = """
        MATCH (e:Entity)
        WHERE toLower(e.name) CONTAINS toLower($name)
        RETURN e.node_id AS node_id, e.name AS name, labels(e)[0] AS label,
               coalesce(e.jurisdiction, '') AS jurisdiction,
               coalesce(e.sourceID, '') AS source,
               coalesce(e.status, '') AS status
        LIMIT $limit
        """
        try:
            res = ro(graph_name, contains_q, {"name": clean_name, "limit": limit})
            for r in res.get("rows", []):
                candidates.append(_build_candidate(r))
        except Exception as exc:
            elapsed = (time.perf_counter() - t0) * 1000
            return ToolResult(
                tool="resolve_entity",
                params={"name": name, "limit": limit},
                status="error",
                elapsed_ms=round(elapsed, 2),
                notes=f"Query failed: {exc}",
            )

    elapsed = (time.perf_counter() - t0) * 1000
    if not candidates:
        return ToolResult(
            tool="resolve_entity",
            params={"name": name, "limit": limit},
            status="unknown_entity",
            data=[],
            elapsed_ms=round(elapsed, 2),
            notes=f"No entity matching '{clean_name}' found in graph",
        )
    elif len(candidates) == 1 and candidates[0]["name"].strip().lower() == clean_name.lower():
        return ToolResult(
            tool="resolve_entity",
            params={"name": name, "limit": limit},
            status="ok",
            data=candidates,
            elapsed_ms=round(elapsed, 2),
            notes="Single exact candidate matched",
        )
    else:
        return ToolResult(
            tool="resolve_entity",
            params={"name": name, "limit": limit},
            status="ambiguous",
            data=candidates,
            elapsed_ms=round(elapsed, 2),
            notes=f"{len(candidates)} candidate entities found for '{clean_name}' — disambiguate by node_id",
        )


# ── Tool 2: ownership_chain ─────────────────────────────────────────────────
def ownership_chain(
    entity_id: str,
    max_depth: int = 2,
    graph_name: str = GRAPH_NAME,
) -> ToolResult:
    """
    Traverse ownership and control paths from the entity up to max_depth (1..MAX_DEPTH).
    STRICTLY excludes Case nodes and ABOUT/CITED meta-edges.
    Returns paths with full node names (not placeholders), labels, and relationship types.
    Each hop shows: name (label) -[REL_TYPE]-> name (label).
    Capped at OWNERSHIP_CHAIN_ROW_CAP rows.
    """
    t0 = time.perf_counter()
    depth = max(1, min(max_depth, MAX_DEPTH))

    # CRITICAL: Only traverse ownership rel types, never ABOUT/CITED.
    # Also exclude Case label targets.
    q = f"""
    MATCH path = (e:Entity {{node_id: $entity_id}})-[:{_OWNERSHIP_REL_TYPES}*1..{depth}]-(target)
    WHERE NOT target:Case
    RETURN [n in nodes(path) | {{
               id: coalesce(n.node_id, ''),
               name: coalesce(n.name, n.address, n.node_id, 'unknown'),
               label: labels(n)[0]
           }}] AS path_nodes,
           [r in relationships(path) | {{
               type: type(r),
               weight: coalesce(r.weight, 2.0),
               link: coalesce(r.link, '')
           }}] AS path_rels
    LIMIT {OWNERSHIP_CHAIN_ROW_CAP}
    """
    try:
        res = ro(graph_name, q, {"entity_id": str(entity_id)})
        rows = res.get("rows", [])
        paths = []
        for r in rows:
            nodes = r[0]
            rels = r[1]
            # Build human-readable path string: A -[REL_TYPE]-> B (Label) -> ...
            path_text_parts = []
            if nodes:
                path_text_parts.append(f"{nodes[0].get('name', '?')} ({nodes[0].get('label', '?')})")
                for i, rel in enumerate(rels):
                    next_node = nodes[i + 1] if i + 1 < len(nodes) else {}
                    path_text_parts.append(
                        f"-[{rel.get('type', '?')}]-> {next_node.get('name', '?')} ({next_node.get('label', '?')})"
                    )
            paths.append(
                {
                    "nodes": nodes,
                    "relationships": rels,
                    "path_text": " ".join(path_text_parts),
                }
            )

        elapsed = (time.perf_counter() - t0) * 1000
        status = "ok" if paths else "empty"
        return ToolResult(
            tool="ownership_chain",
            params={"entity_id": entity_id, "max_depth": depth},
            status=status,
            data=paths,
            elapsed_ms=round(elapsed, 2),
            notes=f"Found {len(paths)} paths at depth {depth} (Case nodes excluded)",
        )
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000
        return ToolResult(
            tool="ownership_chain",
            params={"entity_id": entity_id, "max_depth": depth},
            status="error",
            elapsed_ms=round(elapsed, 2),
            notes=f"Query error: {exc}",
        )


# ── Tool 3: shared_links ────────────────────────────────────────────────────
def shared_links(
    entity_id: str,
    limit: int = SHARED_LINKS_LIMIT,
    graph_name: str = GRAPH_NAME,
) -> ToolResult:
    """
    Find hub nodes (Officer, Address, Intermediary) connected to this entity
    and count how many other distinct entities each hub connects to.
    Case nodes and meta-edges excluded.
    """
    t0 = time.perf_counter()
    limit = max(1, min(limit, 20))

    q = f"""
    MATCH (e:Entity {{node_id: $entity_id}})-[r1:{_OWNERSHIP_REL_TYPES}]-(hub)-[r2:{_OWNERSHIP_REL_TYPES}]-(other:Entity)
    WHERE (hub:Officer OR hub:Address OR hub:Intermediary)
      AND other.node_id <> $entity_id
    RETURN labels(hub)[0] AS hub_type,
           coalesce(hub.name, hub.address, hub.node_id, 'unknown') AS hub_name,
           hub.node_id AS hub_id,
           count(DISTINCT other) AS linked_count
    ORDER BY linked_count DESC
    LIMIT {limit}
    """
    try:
        res = ro(graph_name, q, {"entity_id": str(entity_id)})
        rows = res.get("rows", [])
        hubs = []
        for r in rows:
            hubs.append(
                {
                    "hub_type": r[0],
                    "hub_name": r[1],
                    "hub_id": r[2],
                    "linked_count": r[3],
                }
            )

        elapsed = (time.perf_counter() - t0) * 1000
        status = "ok" if hubs else "empty"
        return ToolResult(
            tool="shared_links",
            params={"entity_id": entity_id, "limit": limit},
            status=status,
            data=hubs,
            elapsed_ms=round(elapsed, 2),
            notes=f"Found {len(hubs)} connected hubs (Case nodes excluded)",
        )
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000
        return ToolResult(
            tool="shared_links",
            params={"entity_id": entity_id, "limit": limit},
            status="error",
            elapsed_ms=round(elapsed, 2),
            notes=f"Query error: {exc}",
        )


# ── Tool 4: path_between ────────────────────────────────────────────────────
def _find_disjoint_bfs(
    a_id: str,
    b_id: str,
    excluded_ids: set[str],
    max_depth: int = 4,
    graph_name: str = GRAPH_NAME,
) -> dict[str, Any] | None:
    """Find an alternative path between a_id and b_id excluding intermediate nodes."""
    from collections import deque

    queue = deque([(a_id, [a_id], 0.0)])
    visited = {a_id} | excluded_ids

    while queue:
        curr, path_nodes, cost = queue.popleft()
        if len(path_nodes) - 1 >= max_depth:
            continue
        q = f"""
        MATCH (n {{node_id: $curr}})-[r:{_OWNERSHIP_REL_TYPES}]-(nbr)
        WHERE NOT nbr:Case
        RETURN nbr.node_id, coalesce(r.weight, 2.0), type(r), coalesce(nbr.name, nbr.address, nbr.node_id), labels(nbr)[0]
        """
        try:
            res = ro(graph_name, q, {"curr": curr})
            for nid, weight, rtype, name, lbl in res.get("rows", []):
                if nid == b_id:
                    return {
                        "node_ids": path_nodes + [nid],
                        "cost": cost + float(weight),
                        "hops": len(path_nodes),
                    }
                if nid not in visited:
                    visited.add(nid)
                    queue.append((nid, path_nodes + [nid], cost + float(weight)))
        except Exception:
            break
    return None


# ── Tool 4: path_between ────────────────────────────────────────────────────
def path_between(
    a_id: str,
    b_id: str,
    max_depth: int = 4,
    graph_name: str = GRAPH_NAME,
    is_watchlist: bool = False,
    watchlist: list[str] | None = None,
) -> ToolResult:
    """
    Find shortest weighted path between two nodes within max_depth.
    Uses algo.SPpaths (or shortestPath Cypher fallback).
    Tags results with target_id and is_watchlist flag.
    Checks for node-disjoint paths (PATH_REDUNDANCY / PATH_DEPENDENCY).
    Case nodes and meta-edges strictly excluded.
    """
    t0 = time.perf_counter()
    depth = max(1, min(max_depth, MAX_DEPTH))

    nodes = None
    rels = None
    path_weight = None

    # First attempt algo.SPpaths with relDirection: 'both' and ownership rel types only
    sp_q = f"""
    MATCH (a {{node_id: $a_id}}), (b {{node_id: $b_id}})
    WHERE NOT a:Case AND NOT b:Case
    CALL algo.SPpaths({{
        sourceNode: a,
        targetNode: b,
        relTypes: [{", ".join(f"'{rt}'" for rt in _OWNERSHIP_REL_TYPES.split("|"))}],
        relDirection: 'both',
        weightProp: 'weight',
        maxLen: {depth},
        pathCount: 1
    }})
    YIELD path, pathWeight
    RETURN [n in nodes(path) | {{
               id: coalesce(n.node_id, ''),
               name: coalesce(n.name, n.address, n.node_id, 'unknown'),
               label: labels(n)[0]
           }}] AS path_nodes,
           [r in relationships(path) | {{type: type(r), weight: coalesce(r.weight, 2.0)}}] AS path_rels,
           pathWeight
    """
    sp_succeeded = False
    try:
        res = ro(graph_name, sp_q, {"a_id": str(a_id), "b_id": str(b_id)})
        rows = res.get("rows", [])
        sp_succeeded = True
        if rows:
            nodes, rels = rows[0][0], rows[0][1]
            path_weight = float(rows[0][2])
    except Exception as sp_exc:
        logger.debug("SPpaths raised: %s; falling back to BFS traversal", sp_exc)

    # Fallback to BFS traversal only if SPpaths raised an error
    if not sp_succeeded and nodes is None:
        bfs_res = _find_disjoint_bfs(str(a_id), str(b_id), set(), max_depth=depth, graph_name=graph_name)
        if bfs_res:
            path_weight = bfs_res["cost"]
            # Fetch node details for found BFS path
            nodes = [{"id": nid, "name": nid, "label": "Node"} for nid in bfs_res["node_ids"]]
            rels = [{"type": "CONNECTED_TO", "weight": 2.0} for _ in range(len(nodes) - 1)]

    elapsed = (time.perf_counter() - t0) * 1000
    if nodes:
        target_id = str(b_id)
        target_name = nodes[-1].get("name", "") if nodes else ""

        # Determine is_watchlist flag
        is_wl = bool(is_watchlist)
        if not is_wl and watchlist:
            target_names_ids = {target_id.lower(), target_name.lower()}
            wl_clean = {w.strip().lower() for w in watchlist if w.strip()}
            if any(w in target_names_ids or target_name.lower() in w for w in wl_clean):
                is_wl = True

        # Node-disjoint path evaluation (Requirement 5)
        intermediate_nodes = nodes[1:-1]
        intermediate_ids = {n.get("id") for n in intermediate_nodes if n.get("id")}

        disjoint_count = 1
        independent_paths = False
        exposure_depends_on = None

        if intermediate_ids:
            disjoint_path = _find_disjoint_bfs(
                str(a_id), str(b_id), intermediate_ids, max_depth=depth, graph_name=graph_name
            )
            if disjoint_path is not None:
                disjoint_count = 2
                independent_paths = True
            else:
                disjoint_count = 1
                independent_paths = False
                if len(intermediate_nodes) == 1:
                    exposure_depends_on = intermediate_nodes[0].get("name") or intermediate_nodes[0].get("id")
                else:
                    exposure_depends_on = ", ".join([n.get("name") or n.get("id") for n in intermediate_nodes])
        else:
            disjoint_count = 1
            independent_paths = False

        return ToolResult(
            tool="path_between",
            params={"a_id": a_id, "b_id": b_id, "max_depth": depth},
            status="ok",
            data=[
                {
                    "nodes": nodes,
                    "relationships": rels,
                    "path_weight": path_weight,
                    "path_text": _build_path_text(nodes, rels),
                    "target_id": target_id,
                    "target_name": target_name,
                    "is_watchlist": is_wl,
                    "disjoint_paths_count": disjoint_count,
                    "independent_paths": independent_paths,
                    "exposure_depends_on": exposure_depends_on,
                }
            ],
            elapsed_ms=round(elapsed, 2),
            notes=f"Path found (is_watchlist={is_wl}, disjoint_count={disjoint_count})",
        )
    else:
        return ToolResult(
            tool="path_between",
            params={"a_id": a_id, "b_id": b_id, "max_depth": depth},
            status="empty",
            data=[],
            elapsed_ms=round(elapsed, 2),
            notes=f"No path between {a_id} and {b_id} within depth {depth}",
        )


def _build_path_text(nodes: list[dict], rels: list[dict]) -> str:
    """Build human-readable path: A (Type) -[REL]-> B (Type) -[REL]-> C (Type)."""
    if not nodes:
        return ""
    parts = [f"{nodes[0].get('name', '?')} ({nodes[0].get('label', '?')})"]
    for i, rel in enumerate(rels):
        next_node = nodes[i + 1] if i + 1 < len(nodes) else {}
        parts.append(f"-[{rel.get('type', '?')}]-> {next_node.get('name', '?')} ({next_node.get('label', '?')})")
    return " ".join(parts)


# ── Tool 5: cluster_view ────────────────────────────────────────────────────
def cluster_view(
    entity_id: str,
    max_depth: int = 2,
    node_cap: int = CLUSTER_NODE_CAP,
    graph_name: str = GRAPH_NAME,
    watchlist: list[str] | None = None,
) -> ToolResult:
    """
    Build a scratch graph case_<uuid8> containing the entity's 2-hop neighborhood.
    Computes PageRank, Betweenness, WCC, and Label Propagation community detection.
    Evaluates COMMUNITY_WATCHLIST and HUB_CENTRALITY.
    Returns metrics and always deletes scratch graph in finally block.
    Case nodes and meta-edges excluded from neighborhood fetch.
    """
    t0 = time.perf_counter()
    depth = max(1, min(max_depth, 2))
    scratch_name = f"case_{uuid.uuid4().hex[:8]}"

    try:
        # Fetch neighborhood — strict exclusion of Case nodes and meta-edges
        fetch_q = f"""
        MATCH path = (e:Entity {{node_id: $entity_id}})-[:{_OWNERSHIP_REL_TYPES}*1..{depth}]-(neighbor)
        WHERE NOT neighbor:Case
        RETURN [n in nodes(path) | {{
                   id: coalesce(n.node_id, ''),
                   name: coalesce(n.name, n.address, n.node_id, 'unknown'),
                   label: labels(n)[0]
               }}] AS nodes,
               [r in relationships(path) | {{
                   start_id: startNode(r).node_id,
                   end_id: endNode(r).node_id,
                   type: type(r),
                   weight: coalesce(r.weight, 2.0)
               }}] AS rels
        LIMIT {node_cap}
        """
        res = ro(graph_name, fetch_q, {"entity_id": str(entity_id)})
        rows = res.get("rows", [])

        if not rows:
            elapsed = (time.perf_counter() - t0) * 1000
            return ToolResult(
                tool="cluster_view",
                params={"entity_id": entity_id, "max_depth": depth},
                status="empty",
                data=[],
                elapsed_ms=round(elapsed, 2),
                notes="No neighborhood found to build cluster view",
            )

        # Aggregate unique nodes and edges
        nodes_map: dict[str, dict[str, Any]] = {}
        edges_set: set[tuple[str, str, str, float]] = set()

        for r in rows:
            for n in r[0]:
                nodes_map[n["id"]] = n
            for rel in r[1]:
                # Insert bidirectional edges so scratch graph algorithms compute true network centrality & community propagation
                edges_set.add((rel["start_id"], rel["end_id"], rel["type"], float(rel["weight"])))
                edges_set.add((rel["end_id"], rel["start_id"], rel["type"], float(rel["weight"])))

        # Build scratch graph
        node_batch = list(nodes_map.values())
        rw(
            scratch_name,
            """
        UNWIND $batch AS n
        CREATE (:ScratchNode {node_id: n.id, name: n.name, label: n.label})
        """,
            {"batch": node_batch},
        )

        edge_batch = [
            {"src": s, "dst": d, "type": t, "weight": w}
            for s, d, t, w in edges_set
            if s in nodes_map and d in nodes_map
        ]

        if edge_batch:
            rw(
                scratch_name,
                """
            UNWIND $batch AS e
            MATCH (src:ScratchNode {node_id: e.src})
            MATCH (dst:ScratchNode {node_id: e.dst})
            CREATE (src)-[:CONNECTED_TO {weight: e.weight}]->(dst)
            """,
                {"batch": edge_batch},
            )

        # Run algorithms on scratch graph (documented names and casing)
        # 1. algo.pageRank
        pagerank_top = []
        try:
            pr_res = ro(
                scratch_name,
                "CALL algo.pageRank('ScratchNode', 'CONNECTED_TO') YIELD node, score RETURN node.node_id, node.name, score ORDER BY score DESC LIMIT 5",
            )
            pagerank_top = [{"id": r[0], "name": r[1], "score": round(float(r[2]), 4)} for r in pr_res.get("rows", [])]
        except Exception as pr_exc:
            logger.debug("PageRank failed in cluster_view: %s", pr_exc)

        # 2. algo.betweenness
        betweenness_top = []
        bw_map: dict[str, float] = {}
        try:
            bw_res = ro(
                scratch_name,
                "CALL algo.betweenness({nodeLabels:['ScratchNode'], relationshipTypes:['CONNECTED_TO'], samplingSize:32, samplingSeed:42}) YIELD node, score RETURN node.node_id, node.name, score ORDER BY score DESC",
            )
            for r in bw_res.get("rows", []):
                score = round(float(r[2]), 4)
                bw_map[str(r[0])] = score
                if len(betweenness_top) < 5:
                    betweenness_top.append({"id": str(r[0]), "name": r[1], "score": score})
        except Exception as bw_exc:
            logger.debug("Betweenness failed in cluster_view: %s", bw_exc)

        # 3. algo.WCC
        communities = []
        wcc_map: dict[str, int] = {}
        try:
            wcc_res = ro(
                scratch_name, "CALL algo.WCC() YIELD node, componentId RETURN node.node_id, node.name, componentId"
            )
            comm_sizes: dict[int, int] = {}
            for r in wcc_res.get("rows", []):
                nid, comp_id = str(r[0]), int(r[2])
                wcc_map[nid] = comp_id
                comm_sizes[comp_id] = comm_sizes.get(comp_id, 0) + 1
            communities = [
                {"community_id": cid, "size": sz}
                for cid, sz in sorted(comm_sizes.items(), key=lambda x: x[1], reverse=True)[:5]
            ]
        except Exception as wcc_exc:
            logger.debug("WCC failed in cluster_view: %s", wcc_exc)

        # 4. algo.labelPropagation
        lp_map: dict[str, int] = {}
        try:
            lp_res = ro(
                scratch_name,
                "CALL algo.labelPropagation({nodeLabels:['ScratchNode'], relationshipTypes:['CONNECTED_TO'], maxIterations:10}) YIELD node, communityId RETURN node.node_id, node.name, communityId",
            )
            for r in lp_res.get("rows", []):
                lp_map[str(r[0])] = int(r[2])
        except Exception as lp_exc:
            logger.debug("labelPropagation failed in cluster_view: %s", lp_exc)

        # Identify shared watchlist communities (Requirement 4)
        shared_watchlist_communities = []
        target_comm = lp_map.get(str(entity_id)) if str(entity_id) in lp_map else wcc_map.get(str(entity_id))
        if target_comm is not None and watchlist:
            wl_clean = {w.strip().lower() for w in watchlist if w.strip()}
            for nid, ninfo in nodes_map.items():
                if nid == str(entity_id):
                    continue
                n_name = ninfo.get("name", "").lower()
                if any(w in n_name or n_name in w for w in wl_clean):
                    node_comm = lp_map.get(nid) if nid in lp_map else wcc_map.get(nid)
                    if node_comm is not None and node_comm == target_comm:
                        shared_watchlist_communities.append(
                            {
                                "watchlist_name": ninfo.get("name"),
                                "watchlist_id": nid,
                                "community_id": target_comm,
                            }
                        )

        # Identify high centrality nodes (Requirement 4)
        from core.config import CENTRALITY_BETWEENNESS_MIN

        high_centrality_nodes = []
        for nid, score in bw_map.items():
            if score >= CENTRALITY_BETWEENNESS_MIN:
                ninfo = nodes_map.get(nid, {})
                high_centrality_nodes.append(
                    {
                        "id": nid,
                        "name": ninfo.get("name", nid),
                        "label": ninfo.get("label", ""),
                        "score": score,
                    }
                )

        elapsed = (time.perf_counter() - t0) * 1000
        data = [
            {
                "nodes_count": len(node_batch),
                "edges_count": len(edge_batch),
                "top_pagerank": pagerank_top,
                "top_betweenness": betweenness_top,
                "communities": communities,
                "shared_watchlist_communities": shared_watchlist_communities,
                "high_centrality_nodes": high_centrality_nodes,
                # Return nodes for graph visualization (limited to 25)
                "viz_nodes": node_batch[:25],
                "viz_edges": edge_batch[:50],
            }
        ]
        return ToolResult(
            tool="cluster_view",
            params={"entity_id": entity_id, "max_depth": depth},
            status="ok",
            data=data,
            elapsed_ms=round(elapsed, 2),
            notes=f"Scratch graph analyzed ({len(node_batch)} nodes, {len(edge_batch)} edges, high_centrality={len(high_centrality_nodes)})",
        )
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000
        return ToolResult(
            tool="cluster_view",
            params={"entity_id": entity_id, "max_depth": depth},
            status="error",
            elapsed_ms=round(elapsed, 2),
            notes=f"cluster_view error: {exc}",
        )
    finally:
        # Crucial Invariant: Always cleanup scratch graph
        drop_graph(scratch_name)


# ── Tool 6: recall_cases ────────────────────────────────────────────────────
def recall_cases(
    entity_id: str,
    limit: int = RECALL_CASES_LIMIT,
    graph_name: str = GRAPH_NAME,
) -> ToolResult:
    """
    Find past investigation decisions relevant to this entity:
    1. Cases directly about this entity (for idempotent re-investigation)
    2. Cases about entities reachable via 1-2 ownership hops (for pattern detection)

    Returns: case_id, verdict, created_at, depth, related_entity, shared_nodes.
    """
    t0 = time.perf_counter()
    limit = max(1, min(limit, 10))

    # Own cases first, then related
    q = f"""
    MATCH (e:Entity {{node_id: $entity_id}})
    OPTIONAL MATCH (c_own:Case)-[:ABOUT]->(e)
    WITH e, collect(DISTINCT c_own) AS own_cases

    OPTIONAL MATCH (e)-[:{_OWNERSHIP_REL_TYPES}*1..2]-(shared:Entity)
    WHERE shared.node_id <> $entity_id
    OPTIONAL MATCH (c_rel:Case)-[:ABOUT]->(shared)
    WITH own_cases, collect(DISTINCT c_rel) AS rel_cases, collect(DISTINCT shared) AS shared_nodes_list

    WITH own_cases + rel_cases AS all_cases, shared_nodes_list
    UNWIND all_cases AS c
    WHERE c IS NOT NULL
    RETURN DISTINCT c.case_id AS id,
           c.verdict AS verdict,
           c.created_at AS created_at,
           c.depth AS depth,
           c.entity_id AS entity_id,
           collect(DISTINCT coalesce(shared_nodes_list[0].name, 'direct link'))[..3] AS shared_nodes
    LIMIT {limit}
    """
    # Simpler approach: two separate queries + merge
    own_q = """
    MATCH (e:Entity {node_id: $entity_id})
    MATCH (c:Case)-[:ABOUT]->(e)
    RETURN DISTINCT c.case_id AS id,
           c.verdict AS verdict,
           c.created_at AS created_at,
           c.depth AS depth,
           e.name AS related_entity,
           [] AS shared_nodes
    ORDER BY c.created_at DESC
    LIMIT 5
    """
    rel_q = f"""
    MATCH (e:Entity {{node_id: $entity_id}})
    MATCH (e)-[:{_OWNERSHIP_REL_TYPES}*1..2]-(shared:Entity)
    WHERE shared.node_id <> $entity_id
    MATCH (c:Case)-[:ABOUT]->(shared)
    RETURN DISTINCT c.case_id AS id,
           c.verdict AS verdict,
           c.created_at AS created_at,
           c.depth AS depth,
           shared.name AS related_entity,
           collect(DISTINCT coalesce(shared.name, shared.node_id))[..3] AS shared_nodes
    LIMIT {limit}
    """
    try:
        cases = []
        seen = set()
        for q, params in [(own_q, {"entity_id": str(entity_id)}), (rel_q, {"entity_id": str(entity_id)})]:
            res = ro(graph_name, q, params)
            for r in res.get("rows", []):
                cid = r[0]
                if cid and cid not in seen:
                    seen.add(cid)
                    cases.append(
                        {
                            "case_id": cid,
                            "verdict": r[1],
                            "created_at": r[2],
                            "depth": r[3],
                            "related_entity": r[4],
                            "shared_nodes": r[5] if len(r) > 5 else [],
                        }
                    )
            if len(cases) >= limit:
                break

        elapsed = (time.perf_counter() - t0) * 1000
        status = "ok" if cases else "empty"
        return ToolResult(
            tool="recall_cases",
            params={"entity_id": entity_id, "limit": limit},
            status=status,
            data=cases[:limit],
            elapsed_ms=round(elapsed, 2),
            notes=f"Found {len(cases[:limit])} cases (own + related)",
        )
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000
        return ToolResult(
            tool="recall_cases",
            params={"entity_id": entity_id, "limit": limit},
            status="error",
            elapsed_ms=round(elapsed, 2),
            notes=f"recall_cases error: {exc}",
        )


# ── Tool 7: record_decision ─────────────────────────────────────────────────


_RULESET_VERSION = "v1"  # bump when rules.py thresholds change


def _make_case_id(entity_id: str, depth: int, watchlist_ids: list[str]) -> str:
    """Deterministic case_id: hash of (entity_id, depth, sorted watchlist IDs, ruleset version).
    Same inputs produce the same ID → upsert is idempotent.
    """
    payload = json.dumps(
        {
            "entity_id": entity_id,
            "depth": depth,
            "watchlist_ids": sorted(watchlist_ids),
            "ruleset": _RULESET_VERSION,
        },
        sort_keys=True,
    )
    return "case_" + hashlib.sha256(payload.encode()).hexdigest()[:16]


def record_decision(
    entity_id: str,
    verdict: str,
    depth: int,
    evidence_ids: list[str],
    rule_ids: list[str],
    memo: str = "",
    case_id: str | None = None,
    graph_name: str = GRAPH_NAME,
) -> dict[str, Any]:
    """
    Write back an investigation decision as a (:Case) node.
    Uses deterministic case_id (hash of entity+depth+watchlist+ruleset) for upsert idempotency.
    Caps total Case nodes at 200, pruning oldest.
    Invariant: Verdict must be in VERDICTS enum.
    Creates:
      (c:Case {case_id, verdict, depth, rule_ids, memo, created_at})
      (c)-[:ABOUT]->(e:Entity)
      (c)-[:CITED]->(cited) for each node_id in evidence_ids
    """
    if verdict not in VERDICTS:
        raise ValueError(f"Invalid verdict '{verdict}'. Allowed: {sorted(VERDICTS)}")

    # Derive deterministic case_id from entity+depth+watchlist if not provided
    cid = case_id or _make_case_id(entity_id, depth, evidence_ids)
    now_iso = datetime.now(UTC).isoformat()

    # MERGE → idempotent upsert (same case_id updates, does not duplicate)
    q_case = """
    MERGE (c:Case {case_id: $case_id})
    SET c.verdict = $verdict,
        c.depth = $depth,
        c.rule_ids = $rule_ids,
        c.memo = $memo,
        c.created_at = $created_at
    WITH c
    MATCH (e:Entity {node_id: $entity_id})
    MERGE (c)-[:ABOUT]->(e)
    RETURN c.case_id, c.verdict
    """
    rw(
        graph_name,
        q_case,
        {
            "case_id": cid,
            "verdict": verdict,
            "depth": depth,
            "rule_ids": rule_ids,
            "memo": memo,
            "created_at": now_iso,
            "entity_id": str(entity_id),
        },
    )

    # Link cited evidence nodes
    if evidence_ids:
        q_cited = """
        UNWIND $evidence_ids AS eid
        MATCH (c:Case {case_id: $case_id})
        MATCH (cited {node_id: eid})
        MERGE (c)-[:CITED]->(cited)
        """
        try:
            rw(graph_name, q_cited, {"case_id": cid, "evidence_ids": [str(x) for x in evidence_ids]})
        except Exception as exc:
            logger.warning("Could not link cited evidence nodes: %s", exc)

    # Prune oldest Cases if over cap (200)
    try:
        rw(
            graph_name,
            """
        MATCH (c:Case)
        WITH c ORDER BY c.created_at ASC
        WITH collect(c) AS cases
        WHERE size(cases) > 200
        UNWIND cases[..size(cases)-200] AS old
        DETACH DELETE old
        """,
            {},
        )
    except Exception as prune_exc:
        logger.debug("Case prune failed (non-fatal): %s", prune_exc)

    return {
        "case_id": cid,
        "verdict": verdict,
        "depth": depth,
        "created_at": now_iso,
        "rule_ids": rule_ids,
    }
