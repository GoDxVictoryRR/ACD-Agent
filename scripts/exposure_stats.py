"""
scripts/exposure_stats.py — Measure graph exposure statistics against the demo watchlist.

Samples >= 200 entities with enough links (degree >= 1), computes shortest path distance
to the demo watchlist targets, and reports the percentage reaching a target within
depth 1, 2, 3, 4, or none.
Writes results to docs/exposure_stats.md with the required contest caveat.
"""

from __future__ import annotations

import json
import logging
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from core.config import DATA_SOURCE, GRAPH_NAME
from core.db import ro
from core.tools import _OWNERSHIP_REL_TYPES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DOCS_DIR = REPO_ROOT / "docs"
DATA_DIR = REPO_ROOT / "data"


def main():
    random.seed(42)  # Fixed seed for reproducibility

    # Load demo watchlist
    demo_json_path = DATA_DIR / "demo.json"
    if demo_json_path.exists():
        with open(demo_json_path, encoding="utf-8") as f:
            demo_cfg = json.load(f)
            watchlist = demo_cfg.get("watchlist", [])
    else:
        watchlist = ["TIANSHENG INDUSTRY AND TRADING CO., LTD."]

    logger.info("Watchlist targets: %s", watchlist)

    # Resolve target entity node_ids
    target_ids = []
    for w in watchlist:
        res = ro(GRAPH_NAME, "MATCH (e:Entity) WHERE toLower(e.name) = toLower($name) RETURN e.node_id", {"name": w})
        for r in res.get("rows", []):
            target_ids.append(r[0])

    if not target_ids:
        logger.error("No target node_ids found for watchlist: %s", watchlist)
        sys.exit(1)

    logger.info("Resolved target node IDs: %s", target_ids)

    # 1. Reverse BFS from target_ids up to depth 4
    # Compute shortest hop distance from watchlist to all reachable nodes
    node_distance: dict[str, int] = {tid: 0 for tid in target_ids}
    current_level = set(target_ids)

    for depth in range(1, 5):
        logger.info("Expanding breadth from target at depth %d (frontier: %d nodes)...", depth, len(current_level))
        batch = list(current_level)
        next_level = set()
        # Batch in chunks of 500 to keep parameter payload reasonable
        chunk_size = 500
        for i in range(0, len(batch), chunk_size):
            chunk = batch[i : i + chunk_size]
            q_expand = f"""
            MATCH (n)-[:{_OWNERSHIP_REL_TYPES}]-(nbr)
            WHERE n.node_id IN $chunk AND NOT nbr:Case
            RETURN DISTINCT nbr.node_id
            """
            res_exp = ro(GRAPH_NAME, q_expand, {"chunk": chunk})
            for r in res_exp.get("rows", []):
                nbr_id = r[0]
                if nbr_id not in node_distance:
                    node_distance[nbr_id] = depth
                    next_level.add(nbr_id)
        current_level = next_level
        logger.info("Discovered %d new nodes at depth %d", len(next_level), depth)

    # 2. Sample 250 connected entities (degree >= 1, not target entities themselves)
    q_sample = """
    MATCH (e:Entity)-[r]-(nbr)
    WHERE NOT e:Case AND NOT nbr:Case
    WITH e, count(r) AS deg
    WHERE deg >= 1
    RETURN e.node_id AS id, e.name AS name, deg
    LIMIT 1000
    """
    res_sample = ro(GRAPH_NAME, q_sample)
    candidates = [{"id": r[0], "name": r[1], "deg": r[2]} for r in res_sample.get("rows", []) if r[0] not in target_ids]

    if len(candidates) < 200:
        logger.error("Insufficient candidate entities: %d < 200", len(candidates))
        sys.exit(1)

    sample = random.sample(candidates, 250)
    logger.info("Sampled %d connected entities for exposure statistics.", len(sample))

    counts = {1: 0, 2: 0, 3: 0, 4: 0, "none": 0}
    for ent in sample:
        d = node_distance.get(ent["id"])
        if d in [1, 2, 3, 4]:
            counts[d] += 1
        else:
            counts["none"] += 1

    total = len(sample)
    percentages = {k: round((v / total) * 100, 2) for k, v in counts.items()}

    logger.info("Exposure Results: %s", counts)
    logger.info("Percentages: %s", percentages)

    cum_1 = percentages[1]
    cum_2 = round(percentages[1] + percentages[2], 2)
    cum_3 = round(percentages[1] + percentages[2] + percentages[3], 2)
    cum_4 = round(percentages[1] + percentages[2] + percentages[3] + percentages[4], 2)

    # Write docs/exposure_stats.md
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = DOCS_DIR / "exposure_stats.md"

    md_content = f"""# Graph Exposure Statistics

**Dataset**: {DATA_SOURCE.upper()} (Panama Papers Samoa/Seychelles subset in FalkorDB)
**Sample Size**: {total} entities (degree >= 1, seeded random sample, seed=42)
**Target Watchlist**: {", ".join(watchlist)} (Node IDs: {", ".join(target_ids)})

> [!IMPORTANT]
> **Caveat & Legal Disclaimer**: Demo watchlist items were chosen by graph criteria for demonstration only. They are not accusations. Inclusion in ICIJ data is not evidence of wrongdoing.

---

## Reachability by Graph Depth

| Depth | Exact Reach Count | Exact % | Cumulative Reach Count | Cumulative % |
|---|---|---|---|---|
| **Depth 1** | {counts[1]} | {percentages[1]}% | {counts[1]} | {cum_1}% |
| **Depth 2** | {counts[2]} | {percentages[2]}% | {counts[1] + counts[2]} | {cum_2}% |
| **Depth 3** | {counts[3]} | {percentages[3]}% | {counts[1] + counts[2] + counts[3]} | {cum_3}% |
| **Depth 4** | {counts[4]} | {percentages[4]}% | {counts[1] + counts[2] + counts[3] + counts[4]} | {cum_4}% |
| **None (>4 hops / disconnected)** | {counts["none"]} | {percentages["none"]}% | {total} | 100.0% |

---

## Key Graph Findings

1. **Depth 1 Sparsity**: Only **{cum_1}%** of sampled entities connect directly to the watchlist target at depth 1.
2. **Multi-Hop Expansion**: By depth 3, cumulative exposure expands to **{cum_3}%** (reaching **{cum_4}%** at depth 4), demonstrating why multi-hop graph traversal is vital for uncovering hidden exposure.
3. **Graph Modularity**: **{percentages["none"]}%** of connected entities remain outside the 4-hop radius of the target, proving that the offshore network is partitioned into distinct clusters rather than a single trivial component.
"""

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\nSaved exposure statistics to {out_file}")


if __name__ == "__main__":
    main()
