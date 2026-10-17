"""
scripts/find_primary_case.py — Comprehensive search for demo cases in FalkorDB.
"""

import sys
from collections import deque
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.fallback import run_deterministic_investigation
from core.db import ro
from core.tools import _OWNERSHIP_REL_TYPES, path_between

print("=== Scanning 3-hop paths in graph ===")

# Query 3-hop paths between two Entities
q_paths = """
MATCH (e1:Entity)-[r1]-(n1)-[r2]-(n2)-[r3]-(e2:Entity)
WHERE e1.node_id <> e2.node_id
  AND NOT e1:Case AND NOT e2:Case
RETURN e1.node_id AS id1, e1.name AS name1, e2.node_id AS id2, e2.name AS name2
LIMIT 200
"""

res_paths = ro("ownership", q_paths)
rows = res_paths.get("rows", [])
print(f"Sampled {len(rows)} 3-hop entity pairs.")

found_primary = None

for id1, name1, id2, name2 in rows:
    # Check uniqueness of names
    cnt1 = ro("ownership", "MATCH (e:Entity) WHERE toLower(e.name) = toLower($name) RETURN count(e)", {"name": name1})[
        "rows"
    ][0][0]
    cnt2 = ro("ownership", "MATCH (e:Entity) WHERE toLower(e.name) = toLower($name) RETURN count(e)", {"name": name2})[
        "rows"
    ][0][0]
    if cnt1 != 1 or cnt2 != 1:
        continue

    # Try both directions: id1 as source, id2 as watchlist; then id2 as source, id1 as watchlist
    for src_id, src_name, tgt_id, tgt_name in [(id1, name1, id2, name2), (id2, name2, id1, name1)]:
        # Check SPpaths
        sp = path_between(src_id, tgt_id, max_depth=4)
        if sp.status != "ok" or not sp.data:
            continue

        cost = sp.data[0].get("path_weight", 999.0)
        nodes = sp.data[0].get("nodes", [])
        hops = len(nodes) - 1
        if hops != 3 or cost > 8.0:
            continue

        # Check BFS distance: no path of length 1 or 2
        bfs_dist = {}
        queue = deque([(src_id, 0)])
        bfs_dist[src_id] = 0
        shorter_found = False
        while queue:
            curr, h = queue.popleft()
            if h >= 2:
                continue
            q_step = (
                f"MATCH (n)-[:{_OWNERSHIP_REL_TYPES}]-(nbr) WHERE n.node_id = $curr AND NOT nbr:Case RETURN nbr.node_id"
            )
            step_res = ro("ownership", q_step, {"curr": curr})
            for sr in step_res.get("rows", []):
                nbr_id = sr[0]
                if nbr_id == tgt_id:
                    shorter_found = True
                    break
                if nbr_id not in bfs_dist:
                    bfs_dist[nbr_id] = h + 1
                    queue.append((nbr_id, h + 1))
            if shorter_found:
                break

        if shorter_found:
            continue

        # Run investigations at depths 1, 2, 3
        inv1 = run_deterministic_investigation(src_name, watchlist=[tgt_name], depth=1)
        inv2 = run_deterministic_investigation(src_name, watchlist=[tgt_name], depth=2)
        inv3 = run_deterministic_investigation(src_name, watchlist=[tgt_name], depth=3)

        print(f"Testing {src_name} -> {tgt_name}: d1={inv1['verdict']}, d2={inv2['verdict']}, d3={inv3['verdict']}")

        if inv1["verdict"] == "clear" and inv2["verdict"] == "clear" and inv3["verdict"] == "escalate":
            found_primary = {
                "src_id": src_id,
                "src_name": src_name,
                "tgt_id": tgt_id,
                "tgt_name": tgt_name,
                "cost": cost,
                "path_text": sp.data[0].get("path_text"),
                "inv1": inv1,
                "inv2": inv2,
                "inv3": inv3,
            }
            print("\n================== PRIMARY CASE CONFIRMED ==================")
            print(f"Source: {src_name} ({src_id})")
            print(f"Target: {tgt_name} ({tgt_id})")
            print(f"Cost: {cost:.1f}")
            print(f"Path: {sp.data[0].get('path_text')}")
            print(f"Verdicts: d1={inv1['verdict']}, d2={inv2['verdict']}, d3={inv3['verdict']}")
            print("============================================================\n")
            break

    if found_primary:
        break

if not found_primary:
    print("No primary case found in first 200 paths, expanding search...")
