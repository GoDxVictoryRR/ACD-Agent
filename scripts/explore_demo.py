"""
scripts/explore_demo.py — Finds candidate demo entities showing depth-1 vs depth-3 contrast.

Searches the graph for entities where:
1. Depth 1 has few direct connections (looks clean/minimal).
2. Within depth 3, a connection reaches a target/watchlist entity.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.config import GRAPH_NAME
from core.db import ro

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def explore_candidates(target_graph: str = GRAPH_NAME) -> list[dict]:
    # Query for entities with 1-2 direct links that have a path of length 2 or 3 to another entity
    q = """
    MATCH (e:Entity)
    WITH e, [(e)-[r]-(neighbor) | neighbor] AS d1_neighbors
    WHERE size(d1_neighbors) >= 1 AND size(d1_neighbors) <= 3
    MATCH path = (e)-[*2..3]-(target:Entity)
    WHERE target.node_id <> e.node_id
    RETURN e.node_id AS source_id,
           e.name AS source_name,
           size(d1_neighbors) AS d1_count,
           length(path) AS depth,
           target.node_id AS target_id,
           target.name AS target_name,
           [n in nodes(path) | coalesce(n.name, n.address, labels(n)[0])] AS path_nodes
    LIMIT 20
    """
    try:
        res = ro(target_graph, q)
        rows = res.get("rows", [])
        candidates = []
        for r in rows:
            candidates.append({
                "source_id": r[0],
                "source_name": r[1],
                "d1_count": r[2],
                "depth": r[3],
                "target_id": r[4],
                "target_name": r[5],
                "path": r[6],
            })
        return candidates
    except Exception as exc:
        logger.warning("explore_candidates query failed (graph may not be populated yet): %s", exc)
        return []


def write_demo_docs(candidates: list[dict]) -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DOCS_DIR / "demo_cases.md"

    content = [
        "# Demo Cases: Depth 1 vs Depth 3 Contrast",
        "",
        "The following candidate entities demonstrate the critical value of multi-hop graph traversal.",
        "At depth 1, the entity appears minimal or clean. At depth 3, exposure to high-risk hubs or watchlisted entities is uncovered.",
        "",
        "| Source Entity | D1 Links | Depth | Target / Watchlist Entity | Path |",
        "|---|---|---|---|---|",
    ]

    for c in candidates:
        path_str = " -> ".join(c["path"])
        content.append(f"| {c['source_name']} | {c['d1_count']} | {c['depth']} | {c['target_name']} | `{path_str}` |")

    # If no dynamic candidates found yet, document the planted synthetic demo cases
    if not candidates:
        content.extend([
            "| Blue Star Maritime Holdings Ltd | 2 | 3 | Ironclad Sanctions Entity Inc | `Blue Star Maritime Holdings Ltd -> Marcus Sterling -> Apex Nominees Ltd -> Apex Corporate Services SA -> Ironclad Sanctions Entity Inc` |",
            "| Silverline Capital Management Ltd | 1 | 1 | John Alexander Vance (Nominee Hub) | `Silverline Capital Management Ltd -> John Alexander Vance (50 shell entities)` |",
            "| Orion Global Logistics Corp | 1 | 1 | Suite 301, St. James Court (Address Hub) | `Orion Global Logistics Corp -> Suite 301, St. James Court (60+ resident companies)` |",
            "| Solitary Enterprises Ltd | 1 | - | (None - Clean entity) | `Solitary Enterprises Ltd -> 12 Shirley Street, Nassau` |",
        ])

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(content) + "\n")

    logger.info("Saved demo cases to %s", out_path)


def write_default_demo_json() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    demo_json_path = DATA_DIR / "demo.json"
    demo_data = {
        "demo_entities": [
            {
                "id": "ENT_BLUESTAR_01",
                "name": "Blue Star Maritime Holdings Ltd",
                "expected_depth_1": "insufficient_evidence",
                "expected_depth_3": "escalate",
                "description": "Appears minimal at depth 1 (one director, one address). At depth 3, links through nominee director to Ironclad Sanctions Entity Inc.",
            },
            {
                "id": "ENT_SILVERLINE_01",
                "name": "Silverline Capital Management Ltd",
                "expected_depth_1": "review",
                "expected_depth_3": "review",
                "description": "Exposed to high-degree nominee officer John Alexander Vance (officer in 50+ offshore shells).",
            },
            {
                "id": "ENT_ORION_01",
                "name": "Orion Global Logistics Corp",
                "expected_depth_1": "review",
                "expected_depth_3": "review",
                "description": "Registered at mass incorporation address hub (Suite 301, St. James Court) shared by 60+ entities.",
            },
            {
                "id": "ENT_SOLITARY_01",
                "name": "Solitary Enterprises Ltd",
                "expected_depth_1": "clear",
                "expected_depth_3": "clear",
                "description": "Clean entity with a single solitary address, zero hub overlap, zero sanctions connection.",
            },
        ],
        "watchlist": [
            "Ironclad Sanctions Entity Inc",
            "Apex Nominees Ltd",
        ],
    }

    with open(demo_json_path, "w", encoding="utf-8") as f:
        json.dump(demo_data, f, indent=2)

    logger.info("Saved default demo.json to %s", demo_json_path)


if __name__ == "__main__":
    candidates = explore_candidates()
    write_demo_docs(candidates)
    write_default_demo_json()
    print("Demo cases and demo.json initialized.")
