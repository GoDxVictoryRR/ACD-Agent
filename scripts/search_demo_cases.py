"""
scripts/search_demo_cases.py — Find and verify all demo cases in live FalkorDB graph.
"""

import sys
from collections import defaultdict, deque
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.fallback import run_deterministic_investigation
from core.db import ro
from core.tools import _OWNERSHIP_REL_TYPES, path_between

print("=== Searching for Demo Cases in Live Graph ===")

# 1. Load entities and check name uniqueness
res_all = ro("ownership", "MATCH (e:Entity) RETURN e.node_id, e.name")
name_counts = defaultdict(int)
id_to_name = {}
for r in res_all.get("rows", []):
    nid, name = r[0], r[1].strip()
    name_counts[name.lower()] += 1
    id_to_name[nid] = name

unique_name_entities = {nid: name for nid, name in id_to_name.items() if name_counts[name.lower()] == 1}
print(f"Total entities: {len(id_to_name):,}, Unique-name entities: {len(unique_name_entities):,}")

# Query candidates with 1 to 3 connections
# We can find candidate entities that have degree 1..3
q_cands = """
MATCH (e:Entity)-[r]-(nbr)
WHERE NOT nbr:Case
WITH e, count(r) AS deg
WHERE deg >= 1 AND deg <= 3
RETURN e.node_id AS id, e.name AS name, deg
LIMIT 300
"""
res_cands = ro("ownership", q_cands)
cand_rows = [r for r in res_cands.get("rows", []) if r[0] in unique_name_entities]
print(f"Sampled {len(cand_rows)} unique-name candidates with 1-3 links")

primary_cases = []

for a_id, a_name, a_deg in cand_rows:
    # Look for paths of length 3 to other unique entities
    q_nbrs = f"""
    MATCH path = (e:Entity {{node_id: $aid}})-[:{_OWNERSHIP_REL_TYPES}*3..3]-(target:Entity)
    WHERE NOT target:Case AND target.node_id <> $aid
    RETURN target.node_id, target.name
    LIMIT 10
    """
    res_nbrs = ro("ownership", q_nbrs, {"aid": a_id})
    for b_id, b_name in res_nbrs.get("rows", []):
        if b_id in unique_name_entities and b_id != a_id:
            # Check SPpaths
            sp = path_between(a_id, b_id, max_depth=4)
            if sp.status == "ok" and sp.data:
                cost = sp.data[0].get("path_weight", 999)
                nodes = sp.data[0].get("nodes", [])
                hops = len(nodes) - 1
                if hops == 3 and cost <= 8.0:
                    # Verify with bounded BFS that no shorter path (hops 1 or 2) exists
                    bfs_dist = {}
                    queue = deque([(a_id, 0)])
                    bfs_dist[a_id] = 0
                    shorter_found = False
                    while queue:
                        curr, h = queue.popleft()
                        if h >= 2:
                            continue
                        q_step = f"MATCH (n {{node_id: $curr}})-[:{_OWNERSHIP_REL_TYPES}]-(nbr) WHERE NOT nbr:Case RETURN nbr.node_id"
                        step_res = ro("ownership", q_step, {"curr": curr})
                        for sr in step_res.get("rows", []):
                            nbr_id = sr[0]
                            if nbr_id == b_id:
                                shorter_found = True
                                break
                            if nbr_id not in bfs_dist:
                                bfs_dist[nbr_id] = h + 1
                                queue.append((nbr_id, h + 1))
                        if shorter_found:
                            break

                    if shorter_found:
                        continue

                    # Run investigation at depths 1, 2, 3
                    inv1 = run_deterministic_investigation(a_name, watchlist=[b_name], depth=1)
                    inv2 = run_deterministic_investigation(a_name, watchlist=[b_name], depth=2)
                    inv3 = run_deterministic_investigation(a_name, watchlist=[b_name], depth=3)

                    if inv1["verdict"] == "clear" and inv2["verdict"] == "clear" and inv3["verdict"] == "escalate":
                        primary_cases.append(
                            {
                                "source_id": a_id,
                                "source_name": a_name,
                                "target_id": b_id,
                                "target_name": b_name,
                                "path_text": sp.data[0].get("path_text"),
                                "cost": cost,
                                "d1": inv1["verdict"],
                                "d2": inv2["verdict"],
                                "d3": inv3["verdict"],
                            }
                        )
                        print(f"FOUND PRIMARY CASE: {a_name} ({a_id}) -> {b_name} ({b_id})")
                        print(f"  Path: {sp.data[0].get('path_text')}")
                        print(
                            f"  Cost: {cost:.1f} | d1={inv1['verdict']} | d2={inv2['verdict']} | d3={inv3['verdict']}"
                        )
                        if len(primary_cases) >= 3:
                            break
    if len(primary_cases) >= 3:
        break

print(f"\nTotal primary cases found: {len(primary_cases)}")
