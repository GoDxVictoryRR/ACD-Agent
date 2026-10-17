"""
data/load.py — FalkorDB graph loader.

Loads nodes and relationships from data/seed/ (synthetic) or data/seed/icij/ (ICIJ subset).
Features:
- DATA_SOURCE=icij|synthetic configurable via environment or CLI.
- Idempotent: checks node/edge counts before loading; skips if already populated.
- --reset flag drops the graph and rebuilds from scratch.
- Batching with UNWIND $batch AS row (batch size configurable via LOAD_BATCH_SIZE env var).
- Applies range indexes on node_id and full-text indexes on name/address per FalkorDB docs.
- Reports counts, load time, graph memory usage, p95 of 3-hop & 4-hop expansions,
  and estimated remote load time (round trips * 50-150ms).
- Exposes ensure_seed() for FastAPI startup self-seeding.
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.config import (
    ALLOWED_REL_TYPES,
    DATA_SOURCE,
    DEFAULT_EDGE_WEIGHT,
    EDGE_WEIGHT,
    GRAPH_NAME,
    LOAD_BATCH_SIZE,
)
from core.db import drop_graph, get_db, graph_exists, ro, rw

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BATCH_SIZE = LOAD_BATCH_SIZE

# Track Cypher round-trips for remote latency estimation
_round_trips_count = 0


def _exec_rw(target_graph: str, query: str, params: dict[str, Any] | None = None) -> Any:
    global _round_trips_count
    _round_trips_count += 1
    return rw(target_graph, query, params)


def _exec_ro(target_graph: str, query: str, params: dict[str, Any] | None = None) -> Any:
    global _round_trips_count
    _round_trips_count += 1
    return ro(target_graph, query, params)


def get_seed_dir(source: str | None = None) -> Path:
    src = (source or os.getenv("DATA_SOURCE", DATA_SOURCE)).lower().strip()
    if src == "icij":
        icij_dir = REPO_ROOT / "data" / "seed" / "icij"
        if (icij_dir / "nodes-entities.csv").exists():
            return icij_dir
        logger.warning("ICIJ seed dir %s missing or empty; falling back to synthetic.", icij_dir)
    return REPO_ROOT / "data" / "seed"


def apply_indexes(target_graph: str = GRAPH_NAME) -> None:
    """Create range indexes and full-text indexes on the graph."""
    logger.info("Applying indexes to graph '%s'...", target_graph)
    labels = ["Entity", "Officer", "Intermediary", "Address", "Other"]
    for label in labels:
        try:
            _exec_rw(target_graph, f"CREATE INDEX FOR (n:{label}) ON (n.node_id)")
        except Exception as exc:
            logger.debug("Range index for %s.node_id: %s", label, exc)

    try:
        _exec_rw(target_graph, "CREATE INDEX FOR (c:Case) ON (c.case_id)")
    except Exception as exc:
        logger.debug("Range index for Case.case_id: %s", exc)

    fulltext_configs = [
        ("Entity", "name"),
        ("Officer", "name"),
        ("Intermediary", "name"),
        ("Address", "address"),
    ]
    for lbl, prop in fulltext_configs:
        try:
            _exec_rw(target_graph, f"CALL db.idx.fulltext.createNodeIndex('{lbl}', '{prop}')")
        except Exception as exc:
            logger.debug("Fulltext index for %s.%s: %s", lbl, prop, exc)


ALLOWED_LABELS: frozenset[str] = frozenset({"Entity", "Officer", "Intermediary", "Address", "Other", "Case"})


def load_node_csv(
    target_graph: str,
    csv_path: Path,
    label: str,
    batch_size: int = BATCH_SIZE,
    node_labels: dict[str, str] | None = None,
) -> int:
    if not csv_path.exists():
        logger.warning("Node file not found: %s", csv_path)
        return 0

    rows: list[dict[str, Any]] = []
    total_loaded = 0

    with open(csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
            if node_labels is not None and "node_id" in r:
                node_labels[r["node_id"]] = label

            if len(rows) >= batch_size:
                _insert_node_batch(target_graph, label, rows)
                total_loaded += len(rows)
                rows = []

        if rows:
            _insert_node_batch(target_graph, label, rows)
            total_loaded += len(rows)

    return total_loaded


def _insert_node_batch(target_graph: str, label: str, batch: list[dict[str, Any]]) -> None:
    if label == "Entity":
        q = """
        UNWIND $batch AS row
        CREATE (:Entity {
            node_id: row.node_id,
            name: row.name,
            jurisdiction: coalesce(row.jurisdiction, ''),
            status: coalesce(row.status, ''),
            sourceID: coalesce(row.sourceID, '')
        })
        """
    elif label == "Officer":
        q = """
        UNWIND $batch AS row
        CREATE (:Officer {
            node_id: row.node_id,
            name: row.name,
            country: coalesce(row.country, ''),
            sourceID: coalesce(row.sourceID, '')
        })
        """
    elif label == "Intermediary":
        q = """
        UNWIND $batch AS row
        CREATE (:Intermediary {
            node_id: row.node_id,
            name: row.name,
            country: coalesce(row.country, ''),
            status: coalesce(row.status, ''),
            sourceID: coalesce(row.sourceID, '')
        })
        """
    elif label == "Address":
        q = """
        UNWIND $batch AS row
        CREATE (:Address {
            node_id: row.node_id,
            address: coalesce(row.address, row.name, ''),
            country: coalesce(row.country, ''),
            sourceID: coalesce(row.sourceID, '')
        })
        """
    else:
        q = f"""
        UNWIND $batch AS row
        CREATE (:{label} {{
            node_id: row.node_id,
            name: coalesce(row.name, ''),
            type: coalesce(row.type, ''),
            sourceID: coalesce(row.sourceID, '')
        }})
        """
    _exec_rw(target_graph, q, {"batch": batch})


def load_relationships_csv(
    target_graph: str,
    csv_path: Path,
    batch_size: int = BATCH_SIZE,
    node_labels: dict[str, str] | None = None,
) -> int:
    if not csv_path.exists():
        logger.warning("Relationships file not found: %s", csv_path)
        return 0

    batches_by_type: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    total_loaded = 0

    with open(csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for r in reader:
            raw_rel = r.get("rel_type", "CONNECTED_TO")
            rel_type = raw_rel.upper().replace(" ", "_").replace("-", "_")
            if rel_type not in ALLOWED_REL_TYPES:
                rel_type = "CONNECTED_TO"

            start_lbl = r.get("start_label") or (node_labels.get(r["start_id"], "") if node_labels else "")
            end_lbl = r.get("end_label") or (node_labels.get(r["end_id"], "") if node_labels else "")

            if start_lbl not in ALLOWED_LABELS:
                start_lbl = ""
            if end_lbl not in ALLOWED_LABELS:
                end_lbl = ""

            weight = float(r.get("weight") or EDGE_WEIGHT.get(rel_type, DEFAULT_EDGE_WEIGHT))
            clean_row = {
                "start_id": str(r["start_id"]),
                "end_id": str(r["end_id"]),
                "link": str(r.get("link", "")),
                "weight": weight,
            }

            batch_key = (start_lbl, rel_type, end_lbl)
            batches_by_type.setdefault(batch_key, []).append(clean_row)
            if len(batches_by_type[batch_key]) >= batch_size:
                _insert_rel_batch(target_graph, batch_key, batches_by_type[batch_key])
                total_loaded += len(batches_by_type[batch_key])
                batches_by_type[batch_key] = []

    for batch_key, remaining in batches_by_type.items():
        if remaining:
            _insert_rel_batch(target_graph, batch_key, remaining)
            total_loaded += len(remaining)

    return total_loaded


def _insert_rel_batch(
    target_graph: str,
    batch_key: tuple[str, str, str],
    batch: list[dict[str, Any]],
) -> None:
    start_lbl, rel_type, end_lbl = batch_key
    src_spec = f":{start_lbl}" if start_lbl else ""
    dst_spec = f":{end_lbl}" if end_lbl else ""
    q = f"""
    UNWIND $batch AS row
    MATCH (src{src_spec} {{node_id: row.start_id}})
    MATCH (dst{dst_spec} {{node_id: row.end_id}})
    CREATE (src)-[:{rel_type} {{link: row.link, weight: row.weight}}]->(dst)
    """
    _exec_rw(target_graph, q, {"batch": batch})


def get_graph_counts(target_graph: str = GRAPH_NAME) -> dict[str, int]:
    """Return counts of nodes and relationships in target graph."""
    try:
        node_res = ro(target_graph, "MATCH (n) RETURN count(n) AS cnt")
        node_count = node_res["rows"][0][0] if node_res["rows"] else 0
        edge_res = ro(target_graph, "MATCH ()-[r]->() RETURN count(r) AS cnt")
        edge_count = edge_res["rows"][0][0] if edge_res["rows"] else 0
        return {"nodes": node_count, "edges": edge_count}
    except Exception:
        return {"nodes": 0, "edges": 0}


def get_falkordb_memory() -> dict[str, Any]:
    """Return FalkorDB server memory usage."""
    try:
        db = get_db()
        info = db.connection.info("memory")
        return {
            "used_memory_human": info.get("used_memory_human", "unknown"),
            "used_memory_bytes": info.get("used_memory", 0),
            "used_memory_peak_human": info.get("used_memory_peak_human", "unknown"),
        }
    except Exception as exc:
        logger.debug("Could not fetch memory info: %s", exc)
        return {"used_memory_human": "unknown", "used_memory_bytes": 0}


def benchmark_expansions(target_graph: str = GRAPH_NAME, sample_size: int = 50) -> dict[str, float]:
    """Sample random entities and benchmark p95 time for 3-hop and 4-hop expansions."""
    from core.tools import _OWNERSHIP_REL_TYPES

    sample_q = f"MATCH (e:Entity) RETURN e.node_id LIMIT {sample_size}"
    try:
        res = ro(target_graph, sample_q)
        entity_ids = [r[0] for r in res.get("rows", [])]
    except Exception as exc:
        logger.warning("Could not fetch sample entities for benchmark: %s", exc)
        return {"p95_3hop_ms": 0.0, "p95_4hop_ms": 0.0}

    if not entity_ids:
        return {"p95_3hop_ms": 0.0, "p95_4hop_ms": 0.0}

    times_3hop: list[float] = []
    times_4hop: list[float] = []

    for eid in entity_ids:
        # 3-hop
        t0 = time.perf_counter()
        q3 = f"""
        MATCH path = (e:Entity {{node_id: $eid}})-[:{_OWNERSHIP_REL_TYPES}*1..3]-(target)
        WHERE NOT target:Case
        RETURN path
        LIMIT 200
        """
        ro(target_graph, q3, {"eid": str(eid)})
        times_3hop.append((time.perf_counter() - t0) * 1000)

        # 4-hop
        t0 = time.perf_counter()
        q4 = f"""
        MATCH path = (e:Entity {{node_id: $eid}})-[:{_OWNERSHIP_REL_TYPES}*1..4]-(target)
        WHERE NOT target:Case
        RETURN path
        LIMIT 200
        """
        ro(target_graph, q4, {"eid": str(eid)})
        times_4hop.append((time.perf_counter() - t0) * 1000)

    times_3hop.sort()
    times_4hop.sort()

    idx95 = int(len(times_3hop) * 0.95)
    p95_3 = round(times_3hop[min(idx95, len(times_3hop) - 1)], 2)
    p95_4 = round(times_4hop[min(idx95, len(times_4hop) - 1)], 2)

    return {"p95_3hop_ms": p95_3, "p95_4hop_ms": p95_4}


def load_dataset(
    target_graph: str = GRAPH_NAME,
    reset: bool = False,
    source: str | None = None,
    batch_size: int = BATCH_SIZE,
) -> dict[str, Any]:
    global _round_trips_count
    _round_trips_count = 0
    t0 = time.perf_counter()

    data_src = (source or os.getenv("DATA_SOURCE", DATA_SOURCE)).lower().strip()
    seed_path = get_seed_dir(data_src)
    logger.info("Loading dataset from '%s' into graph '%s' (batch_size=%d)...", seed_path, target_graph, batch_size)

    if reset:
        logger.info("Dropping existing graph '%s'...", target_graph)
        drop_graph(target_graph)

    # If graph exists and has data, check counts
    if not reset and graph_exists(target_graph):
        current = get_graph_counts(target_graph)
        if current["nodes"] > 1000:
            logger.info(
                "Graph '%s' already populated (%d nodes, %d edges). Skipping load.",
                target_graph,
                current["nodes"],
                current["edges"],
            )
            mem = get_falkordb_memory()
            return {
                "status": "skipped",
                "data_source": data_src,
                "counts": current,
                "graph_memory": mem,
                "elapsed_s": 0.0,
            }

    # Verify seed files exist; if not, generate synthetic data
    if not (seed_path / "nodes-entities.csv").exists():
        logger.info("Seed directory empty. Generating synthetic dataset...")
        from data.make_synthetic import generate_synthetic_dataset

        generate_synthetic_dataset(seed_path)

    # 1. Apply indexes first
    apply_indexes(target_graph)

    # 2. Load nodes
    node_labels: dict[str, str] = {}
    node_counts = {
        "Entity": load_node_csv(target_graph, seed_path / "nodes-entities.csv", "Entity", batch_size, node_labels),
        "Officer": load_node_csv(target_graph, seed_path / "nodes-officers.csv", "Officer", batch_size, node_labels),
        "Intermediary": load_node_csv(
            target_graph, seed_path / "nodes-intermediaries.csv", "Intermediary", batch_size, node_labels
        ),
        "Address": load_node_csv(target_graph, seed_path / "nodes-addresses.csv", "Address", batch_size, node_labels),
        "Other": load_node_csv(target_graph, seed_path / "nodes-others.csv", "Other", batch_size, node_labels),
    }
    logger.info("Loaded nodes: %s", node_counts)

    # 3. Load relationships
    edge_count = load_relationships_csv(target_graph, seed_path / "relationships.csv", batch_size, node_labels)
    logger.info("Loaded relationships: %d", edge_count)

    elapsed = time.perf_counter() - t0
    total_nodes = sum(node_counts.values())
    total_round_trips = _round_trips_count

    # Memory and expansion benchmark
    mem = get_falkordb_memory()
    exp_bench = benchmark_expansions(target_graph, sample_size=50)

    # Remote load time estimation: 50ms - 150ms per round trip
    remote_min_s = round(total_round_trips * 0.050, 1)
    remote_max_s = round(total_round_trips * 0.150, 1)

    logger.info(
        "Graph '%s' loaded in %.2f s (nodes: %d, edges: %d, memory: %s, 3-hop p95: %.1f ms).",
        target_graph,
        elapsed,
        total_nodes,
        edge_count,
        mem["used_memory_human"],
        exp_bench["p95_3hop_ms"],
    )

    return {
        "status": "loaded",
        "data_source": data_src,
        "seed_dir": str(seed_path),
        "nodes": total_nodes,
        "node_breakdown": node_counts,
        "edges": edge_count,
        "load_time_s": round(elapsed, 2),
        "graph_memory": mem,
        "round_trips": total_round_trips,
        "estimated_remote_load_s": [remote_min_s, remote_max_s],
        "p95_3hop_ms": exp_bench["p95_3hop_ms"],
        "p95_4hop_ms": exp_bench["p95_4hop_ms"],
    }


def ensure_seed(target_graph: str = GRAPH_NAME) -> None:
    """Ensure the target graph has data. Called on API startup."""
    try:
        counts = get_graph_counts(target_graph)
        if counts["nodes"] < 100:
            logger.info("Self-seeding graph '%s' on startup...", target_graph)
            load_dataset(target_graph, reset=False)
    except Exception as exc:
        logger.warning("ensure_seed error: %s. Attempting fresh load.", exc)
        load_dataset(target_graph, reset=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Load seed dataset into FalkorDB")
    parser.add_argument("--graph", default=GRAPH_NAME, help=f"Target graph name (default: {GRAPH_NAME})")
    parser.add_argument("--reset", action="store_true", help="Drop and rebuild graph from scratch")
    parser.add_argument(
        "--source", choices=["icij", "synthetic"], default=None, help="Dataset source (icij or synthetic)"
    )
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help=f"Batch size (default: {BATCH_SIZE})")
    args = parser.parse_args()

    result = load_dataset(
        target_graph=args.graph,
        reset=args.reset,
        source=args.source,
        batch_size=args.batch_size,
    )
    print("\n" + "=" * 60)
    print("LOADER SUMMARY REPORT")
    print("=" * 60)
    print(f"Status:                   {result['status']}")
    print(f"Data Source:              {result.get('data_source')}")
    print(f"Seed Directory:           {result.get('seed_dir')}")
    print(f"Total Nodes:              {result.get('nodes', 0):,}")
    print(f"Node Breakdown:           {result.get('node_breakdown')}")
    print(f"Total Edges:              {result.get('edges', 0):,}")
    print(f"Local Load Time:          {result.get('load_time_s', 0):.2f} s")
    print(
        f"Graph Memory:             {result.get('graph_memory', {}).get('used_memory_human')} ({result.get('graph_memory', {}).get('used_memory_bytes', 0):,} bytes)"
    )
    print(f"Cypher Round Trips:       {result.get('round_trips', 0):,}")
    print(
        f"Est. Remote Load Time:    {result.get('estimated_remote_load_s', [0, 0])[0]}s - {result.get('estimated_remote_load_s', [0, 0])[1]}s (at 50-150ms / RT)"
    )
    print(f"3-Hop Expansion p95:      {result.get('p95_3hop_ms', 0):.2f} ms")
    print(f"4-Hop Expansion p95:      {result.get('p95_4hop_ms', 0):.2f} ms")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
