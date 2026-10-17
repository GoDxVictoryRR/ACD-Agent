import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from collections import deque

from agent.fallback import run_deterministic_investigation
from core.db import ro
from core.tools import _OWNERSHIP_REL_TYPES, path_between

print("Searching from low-degree officers...")

# 1. Get officers with degree between 2 and 4
q_off = """
MATCH (o:Officer)-[r:OFFICER_OF]->(e:Entity)
WITH o, count(e) AS deg
WHERE deg >= 2 AND deg <= 3
RETURN o.node_id, o.name, deg
LIMIT 50
"""
res_off = ro("ownership", q_off)
officers = res_off.get("rows", [])
print(f"Found {len(officers)} candidate officers.")

found = []
for oid, oname, odeg in officers:
    # Get entities connected to this officer
    q_ents = "MATCH (o:Officer)-[:OFFICER_OF]->(e:Entity) WHERE o.node_id = $oid RETURN e.node_id, e.name"
    e_rows = ro("ownership", q_ents, {"oid": oid}).get("rows", [])
    if len(e_rows) < 2:
        continue

    # Try each pair (e1, e2)
    for i in range(len(e_rows)):
        e1_id, e1_name = e_rows[i]
        for j in range(len(e_rows)):
            if i == j:
                continue
            e2_id, e2_name = e_rows[j]
            # Now find a neighbor of e2 that is an Entity
            q_e3 = """
            MATCH (e2:Entity)-[r]-(e3:Entity)
            WHERE e2.node_id = $e2_id AND e3.node_id <> $e1_id AND e3.node_id <> $e2_id
              AND NOT e3:Case
            RETURN e3.node_id, e3.name, type(r)
            LIMIT 5
            """
            e3_rows = ro("ownership", q_e3, {"e2_id": e2_id, "e1_id": e1_id}).get("rows", [])
            for e3_id, e3_name, rel_type in e3_rows:
                # Check uniqueness of names
                cnt1 = ro(
                    "ownership",
                    "MATCH (e:Entity) WHERE toLower(e.name) = toLower($name) RETURN count(e)",
                    {"name": e1_name},
                )["rows"][0][0]
                cnt3 = ro(
                    "ownership",
                    "MATCH (e:Entity) WHERE toLower(e.name) = toLower($name) RETURN count(e)",
                    {"name": e3_name},
                )["rows"][0][0]
                if cnt1 != 1 or cnt3 != 1:
                    continue

                sp = path_between(e1_id, e3_id, max_depth=4)
                if sp.status != "ok" or not sp.data:
                    continue
                cost = sp.data[0].get("path_weight", 999.0)
                nodes = sp.data[0].get("nodes", [])
                hops = len(nodes) - 1
                if hops != 3 or cost > 8.0:
                    continue

                # Bounded BFS verification
                bfs_dist = {}
                queue = deque([(e1_id, 0)])
                bfs_dist[e1_id] = 0
                shorter = False
                while queue:
                    curr, h = queue.popleft()
                    if h >= 2:
                        continue
                    q_step = f"MATCH (n)-[:{_OWNERSHIP_REL_TYPES}]-(nbr) WHERE n.node_id = $curr AND NOT nbr:Case RETURN nbr.node_id"
                    sres = ro("ownership", q_step, {"curr": curr})
                    for r in sres.get("rows", []):
                        nbr_id = r[0]
                        if nbr_id == e3_id:
                            shorter = True
                            break
                        if nbr_id not in bfs_dist:
                            bfs_dist[nbr_id] = h + 1
                            queue.append((nbr_id, h + 1))
                    if shorter:
                        break
                if shorter:
                    continue

                # Run investigations
                inv1 = run_deterministic_investigation(e1_name, watchlist=[e3_name], depth=1)
                inv2 = run_deterministic_investigation(e1_name, watchlist=[e3_name], depth=2)
                inv3 = run_deterministic_investigation(e1_name, watchlist=[e3_name], depth=3)

                print(f"Testing {e1_name} -> {e3_name} (hops={hops}, cost={cost}):")
                print(f"  d1: {inv1['verdict']} rules={inv1['rules_fired']}")
                print(f"  d2: {inv2['verdict']} rules={inv2['rules_fired']}")
                print(f"  d3: {inv3['verdict']} rules={inv3['rules_fired']}")

                if inv1["verdict"] == "clear" and inv2["verdict"] == "clear" and inv3["verdict"] == "escalate":
                    found.append(
                        {
                            "source_id": e1_id,
                            "source_name": e1_name,
                            "target_id": e3_id,
                            "target_name": e3_name,
                            "cost": cost,
                            "path": sp.data[0].get("path_text"),
                            "inv1": inv1,
                            "inv2": inv2,
                            "inv3": inv3,
                        }
                    )
                    print("  >>> FOUND SUITABLE PRIMARY CASE! <<<")
                    break
            if found:
                break
        if found:
            break
    if found:
        break

if found:
    f = found[0]
    print("\n================ PRIMARY CASE DETAILS ================")
    print(f"Source: {f['source_name']} (ID: {f['source_id']})")
    print(f"Target: {f['target_name']} (ID: {f['target_id']})")
    print(f"Path: {f['path']}")
    print(f"Cost: {f['cost']}")
    print("======================================================")
else:
    print("No case found in this sample.")
