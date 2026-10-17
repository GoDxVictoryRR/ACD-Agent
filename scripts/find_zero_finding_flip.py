import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from collections import deque

from agent.fallback import run_deterministic_investigation
from core.db import ro
from core.tools import _OWNERSHIP_REL_TYPES, path_between

print("Searching for primary cases with strictly 0 findings at d1 and d2...")

q_paths = """
MATCH (e1:Entity)-[r1]-(n1)-[r2]-(n2)-[r3]-(e2:Entity)
WHERE e1.node_id <> e2.node_id
  AND NOT e1:Case AND NOT e2:Case
RETURN e1.node_id AS id1, e1.name AS name1, e2.node_id AS id2, e2.name AS name2
LIMIT 1000
"""
res_paths = ro("ownership", q_paths)
rows = res_paths.get("rows", [])
print(f"Sampled {len(rows)} 3-hop entity pairs.")

found = []
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

    for src_id, src_name, tgt_id, tgt_name in [(id1, name1, id2, name2), (id2, name2, id1, name1)]:
        sp = path_between(src_id, tgt_id, max_depth=4)
        if sp.status != "ok" or not sp.data:
            continue
        cost = sp.data[0].get("path_weight", 999.0)
        nodes = sp.data[0].get("nodes", [])
        if len(nodes) - 1 != 3 or cost > 8.0:
            continue

        # BFS check for no path at depth 1 or 2
        bfs_dist = {}
        queue = deque([(src_id, 0)])
        bfs_dist[src_id] = 0
        shorter = False
        while queue:
            curr, h = queue.popleft()
            if h >= 2:
                continue
            q_step = (
                f"MATCH (n)-[:{_OWNERSHIP_REL_TYPES}]-(nbr) WHERE n.node_id = $curr AND NOT nbr:Case RETURN nbr.node_id"
            )
            sres = ro("ownership", q_step, {"curr": curr})
            for r in sres.get("rows", []):
                nbr_id = r[0]
                if nbr_id == tgt_id:
                    shorter = True
                    break
                if nbr_id not in bfs_dist:
                    bfs_dist[nbr_id] = h + 1
                    queue.append((nbr_id, h + 1))
            if shorter:
                break
        if shorter:
            continue

        # Investigations
        inv1 = run_deterministic_investigation(src_name, watchlist=[tgt_name], depth=1)
        if len(inv1["evaluation"]["findings"]) != 0:
            continue
        inv2 = run_deterministic_investigation(src_name, watchlist=[tgt_name], depth=2)
        if len(inv2["evaluation"]["findings"]) != 0:
            continue
        inv3 = run_deterministic_investigation(src_name, watchlist=[tgt_name], depth=3)
        if inv3["verdict"] == "escalate":
            found.append(
                {
                    "src_id": src_id,
                    "src_name": src_name,
                    "tgt_id": tgt_id,
                    "tgt_name": tgt_name,
                    "cost": cost,
                    "path": sp.data[0].get("path_text"),
                    "f1": len(inv1["evaluation"]["findings"]),
                    "f2": len(inv2["evaluation"]["findings"]),
                    "f3": [f["rule_id"] for f in inv3["evaluation"]["findings"]],
                }
            )
            print(f"PERFECT MATCH FOUND: {src_name} ({src_id}) -> {tgt_name} ({tgt_id})")
            print(f"  Cost: {cost:.1f} | Path: {sp.data[0].get('path_text')}")
            print(
                f"  Findings: d1={len(inv1['evaluation']['findings'])}, d2={len(inv2['evaluation']['findings'])}, d3={[f['rule_id'] for f in inv3['evaluation']['findings']]}"
            )
            if len(found) >= 5:
                break
    if len(found) >= 5:
        break

print(f"\nFound {len(found)} perfect matches!")
