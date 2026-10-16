"""
data/load.py — FalkorDB graph loader.

Loads nodes and relationships from data/seed/ CSVs.
Features:
- Idempotent: checks node/edge counts before loading; skips if already populated.
- --reset flag drops the graph and rebuilds from scratch.
- Batching with UNWIND $batch AS row (batches of 1000).
- Applies range indexes and full-text indexes.
- Exposes ensure_seed() for FastAPI startup self-seeding.
"""
from __future__ import annotations

import argparse
import csv
import logging
import sys
import time
from pathlib import Path
from typing import Any

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.config import ALLOWED_REL_TYPES, DEFAULT_EDGE_WEIGHT, EDGE_WEIGHT, GRAPH_NAME
from core.db import drop_graph, graph_exists, ro, rw

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SEED_DIR = Path(__file__).resolve().parent / "seed"
BATCH_SIZE = 1000


def apply_indexes(target_graph: str = GRAPH_NAME) -> None:
    """Create range indexes and full-text indexes on the graph."""
    logger.info("Applying indexes to graph '%s'...", target_graph)
    # Range indexes
    labels = ["Entity", "Officer", "Intermediary", "Address", "Other"]
    for label in labels:
        try:
            rw(target_graph, f"CREATE INDEX FOR (n:{label}) ON (n.node_id)")
        except Exception as exc:
            logger.debug("Range index for %s.node_id: %s", label, exc)

    try:
        rw(target_graph, "CREATE INDEX FOR (c:Case) ON (c.case_id)")
    except Exception as exc:
        logger.debug("Range index for Case.case_id: %s", exc)

    # Full-text indexes
    fulltext_configs = [
        ("Entity", "name"),
        ("Officer", "name"),
        ("Intermediary", "name"),
        ("Address", "address"),
    ]
    for lbl, prop in fulltext_configs:
        try:
            rw(target_graph, f"CALL db.idx.fulltext.createNodeIndex('{lbl}', '{prop}')")
        except Exception as exc:
            logger.debug("Fulltext index for %s.%s: %s", lbl, prop, exc)


def load_node_csv(target_graph: str, csv_path: Path, label: str) -> int:
    if not csv_path.exists():
        logger.warning("Node file not found: %s", csv_path)
        return 0

    rows: list[dict[str, Any]] = []
    total_loaded = 0

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
            if len(rows) >= BATCH_SIZE:
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
            sourceID: coalesce(row.sourceID, '')
        }})
        """

    rw(target_graph, q, {"batch": batch})


def load_relationships_csv(target_graph: str, csv_path: Path) -> int:
    if not csv_path.exists():
        logger.warning("Relationships file not found: %s", csv_path)
        return 0

    batches_by_type: dict[str, list[dict[str, Any]]] = {}
    total_loaded = 0

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rel_type = r.get("rel_type", "CONNECTED_TO").upper().replace(" ", "_").replace("-", "_")
            if rel_type not in ALLOWED_REL_TYPES:
                rel_type = "CONNECTED_TO"

            weight = float(r.get("weight") or EDGE_WEIGHT.get(rel_type, DEFAULT_EDGE_WEIGHT))
            clean_row = {
                "start_id": str(r["start_id"]),
                "end_id": str(r["end_id"]),
                "link": str(r.get("link", "")),
                "weight": weight,
            }

            batches_by_type.setdefault(rel_type, []).append(clean_row)
            if len(batches_by_type[rel_type]) >= BATCH_SIZE:
                _insert_rel_batch(target_graph, rel_type, batches_by_type[rel_type])
                total_loaded += len(batches_by_type[rel_type])
                batches_by_type[rel_type] = []

    for rel_type, remaining in batches_by_type.items():
        if remaining:
            _insert_rel_batch(target_graph, rel_type, remaining)
            total_loaded += len(remaining)

    return total_loaded


def _insert_rel_batch(target_graph: str, rel_type: str, batch: list[dict[str, Any]]) -> None:
    # Relationship type cannot be parameter in Cypher; must use allowlisted string
    q = f"""
    UNWIND $batch AS row
    MATCH (src {{node_id: row.start_id}})
    MATCH (dst {{node_id: row.end_id}})
    CREATE (src)-[:{rel_type} {{link: row.link, weight: row.weight}}]->(dst)
    """
    rw(target_graph, q, {"batch": batch})


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


def load_dataset(target_graph: str = GRAPH_NAME, reset: bool = False) -> dict[str, Any]:
    t0 = time.perf_counter()

    if reset:
        logger.info("Dropping existing graph '%s'...", target_graph)
        drop_graph(target_graph)

    # If graph exists and has data, check counts
    if not reset and graph_exists(target_graph):
        current = get_graph_counts(target_graph)
        if current["nodes"] > 1000:
            logger.info("Graph '%s' already populated (%d nodes, %d edges). Skipping load.", target_graph, current["nodes"], current["edges"])
            return {"status": "skipped", "counts": current, "elapsed_s": 0.0}

    # Verify seed files exist; if not, generate synthetic data
    if not (SEED_DIR / "nodes-entities.csv").exists():
        logger.info("Seed directory empty. Generating synthetic dataset...")
        from data.make_synthetic import generate_synthetic_dataset
        generate_synthetic_dataset(SEED_DIR)

    # 1. Apply indexes first
    apply_indexes(target_graph)

    # 2. Load nodes
    node_counts = {
        "Entity": load_node_csv(target_graph, SEED_DIR / "nodes-entities.csv", "Entity"),
        "Officer": load_node_csv(target_graph, SEED_DIR / "nodes-officers.csv", "Officer"),
        "Intermediary": load_node_csv(target_graph, SEED_DIR / "nodes-intermediaries.csv", "Intermediary"),
        "Address": load_node_csv(target_graph, SEED_DIR / "nodes-addresses.csv", "Address"),
        "Other": load_node_csv(target_graph, SEED_DIR / "nodes-others.csv", "Other"),
    }
    logger.info("Loaded nodes: %s", node_counts)

    # 3. Load relationships
    edge_count = load_relationships_csv(target_graph, SEED_DIR / "relationships.csv")
    logger.info("Loaded relationships: %d", edge_count)

    elapsed = time.perf_counter() - t0
    total_nodes = sum(node_counts.values())
    logger.info("Graph '%s' loaded in %.2f seconds (nodes: %d, edges: %d).", target_graph, elapsed, total_nodes, edge_count)

    return {
        "status": "loaded",
        "nodes": total_nodes,
        "node_breakdown": node_counts,
        "edges": edge_count,
        "elapsed_s": round(elapsed, 2),
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
    args = parser.parse_args()

    result = load_dataset(args.graph, reset=args.reset)
    print(f"\nResult: {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
