import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from collections import deque

from agent.fallback import run_deterministic_investigation
from core.db import ro
from core.tools import _OWNERSHIP_REL_TYPES, path_between, shared_links

print("Searching for primary cases with zero findings at d1 and d2...")

# Step 1: Find entities where shared_links returns 0 hubs
# An entity has no hubs if all its connected officers have < 5 links,
# all connected intermediaries have < 10 links, and all connected addresses have < 5 links.
q_clean_ent = """
MATCH (e:Entity)
WHERE NOT e:Case
OPTIONAL MATCH (e)-[:OFFICER_OF]-(o:Officer)
OPTIONAL MATCH (e)-[:INTERMEDIARY_OF]-(i:Intermediary)
OPTIONAL MATCH (e)-[:REGISTERED_ADDRESS|ADDRESS_OF]-(a:Address)
WITH e,
     count(DISTINCT o) AS off_cnt,
     count(DISTINCT i) AS int_cnt,
     count(DISTINCT a) AS add_cnt
WHERE (off_cnt + int_cnt + add_cnt) >= 1
RETURN e.node_id, e.name
LIMIT 500
"""
res_clean = ro("ownership", q_clean_ent)
print(f"Sampled {len(res_clean.get('rows', []))} candidate entities.")

candidate_sources = []
for nid, name in res_clean.get("rows", []):
    # Check uniqueness of name
    q_u = "MATCH (e:Entity) WHERE toLower(e.name) = toLower($name) RETURN count(e)"
    if ro("ownership", q_u, {"name": name})["rows"][0][0] != 1:
        continue
    # Check hubs
    sl = shared_links(nid)
    if sl.status == "ok" and len(sl.data) == 0:
        candidate_sources.append((nid, name))
        if len(candidate_sources) >= 50:
            break

print(f"Found {len(candidate_sources)} entities with 0 hubs at depth 1!")

# For these candidate sources, see if any reach another Entity at depth 3
found_cases = []
for src_id, src_name in candidate_sources:
    # 3-hop query: (src)-[r1]-(n1)-[r2]-(n2)-[r3]-(tgt:Entity)
    q_3hop = """
    MATCH (src:Entity)-[r1]-(n1)-[r2]-(n2)-[r3]-(tgt:Entity)
    WHERE src.node_id = $src_id AND tgt.node_id <> $src_id AND NOT tgt:Case
    RETURN DISTINCT tgt.node_id, tgt.name
    LIMIT 20
    """
    res_3 = ro("ownership", q_3hop, {"src_id": src_id})
    for tgt_id, tgt_name in res_3.get("rows", []):
        if ro("ownership", q_u, {"name": tgt_name})["rows"][0][0] != 1:
            continue

        sp = path_between(src_id, tgt_id, max_depth=4)
        if sp.status != "ok" or not sp.data:
            continue
        cost = sp.data[0].get("path_weight", 999.0)
        nodes = sp.data[0].get("nodes", [])
        hops = len(nodes) - 1
        if hops != 3 or cost > 8.0:
            continue

        # BFS verify no path of length 1 or 2
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

        inv1 = run_deterministic_investigation(src_name, watchlist=[tgt_name], depth=1)
        inv2 = run_deterministic_investigation(src_name, watchlist=[tgt_name], depth=2)
        inv3 = run_deterministic_investigation(src_name, watchlist=[tgt_name], depth=3)

        if inv1["verdict"] == "clear" and inv2["verdict"] == "clear" and inv3["verdict"] == "escalate":
            found_cases.append(
                {
                    "source_id": src_id,
                    "source_name": src_name,
                    "target_id": tgt_id,
                    "target_name": tgt_name,
                    "cost": cost,
                    "path": sp.data[0].get("path_text"),
                    "f1_count": len(inv1["evaluation"]["findings"]),
                    "f2_count": len(inv2["evaluation"]["findings"]),
                    "f3_rules": [f["rule_id"] for f in inv3["evaluation"]["findings"]],
                }
            )
            print("\n*** MATCH FOUND ***")
            print(f"Source: {src_name} ({src_id})")
            print(f"Target: {tgt_name} ({tgt_id})")
            print(f"Cost: {cost:.1f} | Path: {sp.data[0].get('path_text')}")
            print(
                f"Findings: d1={len(inv1['evaluation']['findings'])}, d2={len(inv2['evaluation']['findings'])}, d3={[f['rule_id'] for f in inv3['evaluation']['findings']]}"
            )
            if len(inv1["evaluation"]["findings"]) == 0 and len(inv2["evaluation"]["findings"]) == 0:
                print(">>> STRICT ZERO FINDINGS AT D1 AND D2! <<<")
                break
    if found_cases and found_cases[-1]["f1_count"] == 0 and found_cases[-1]["f2_count"] == 0:
        break

print(f"\nDone! Found {len(found_cases)} cases.")
