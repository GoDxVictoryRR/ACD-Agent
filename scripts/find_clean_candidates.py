import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from collections import deque

from agent.fallback import run_deterministic_investigation
from core.db import ro
from core.tools import _OWNERSHIP_REL_TYPES, path_between

print("Searching for low-degree entities clean at d1 & d2...")

q = """
MATCH (e:Entity)-[r]-(nbr)
WHERE NOT nbr:Case
WITH e, count(r) AS deg
WHERE deg >= 1 AND deg <= 3
RETURN e.node_id, e.name
LIMIT 1000
"""
res = ro("ownership", q)
rows = res.get("rows", [])
print(f"Sampled {len(rows)} low-degree entities.")

clean_entities = []
for nid, name in rows:
    # First check name uniqueness
    q_name = "MATCH (e:Entity) WHERE toLower(e.name) = toLower($name) RETURN count(e)"
    cnt = ro("ownership", q_name, {"name": name})["rows"][0][0]
    if cnt != 1:
        continue
    inv1 = run_deterministic_investigation(name, watchlist=[], depth=1)
    if inv1["verdict"] == "clear":
        inv2 = run_deterministic_investigation(name, watchlist=[], depth=2)
        if inv2["verdict"] == "clear":
            clean_entities.append((nid, name))
            if len(clean_entities) >= 30:
                print(f"Collected {len(clean_entities)} clean candidates...")
                break

print(f"Found {len(clean_entities)} entities that are CLEAR at d1 and d2 without watchlist.")

# Now for each clean entity, see if it has an Entity neighbor at exact depth 3
primary_matches = []
for src_id, src_name in clean_entities:
    # Find entities reachable at distance 3
    q_hop3 = f"""
    MATCH path = (e:Entity)-[:{_OWNERSHIP_REL_TYPES}*3..3]-(target:Entity)
    WHERE e.node_id = $src_id AND NOT target:Case AND target.node_id <> $src_id
    RETURN target.node_id, target.name
    LIMIT 20
    """
    res_hop3 = ro("ownership", q_hop3, {"src_id": src_id})
    print(f"Candidate {src_name} ({src_id}) has {len(res_hop3.get('rows', []))} hop3 targets")
    for tgt_id, tgt_name in res_hop3.get("rows", []):
        # Check target name uniqueness
        q_tname = "MATCH (e:Entity) WHERE toLower(e.name) = toLower($name) RETURN count(e)"
        tcnt = ro("ownership", q_tname, {"name": tgt_name})["rows"][0][0]
        if tcnt != 1:
            continue

        # Check SPpaths
        sp = path_between(src_id, tgt_id, max_depth=4)
        if sp.status == "ok" and sp.data:
            cost = sp.data[0].get("path_weight", 999)
            nodes = sp.data[0].get("nodes", [])
            hops = len(nodes) - 1
            if hops == 3 and cost <= 8.0:
                # Verify BFS: no path at depth 1 or 2
                bfs_dist = {}
                queue = deque([(src_id, 0)])
                bfs_dist[src_id] = 0
                shorter = False
                while queue:
                    curr, h = queue.popleft()
                    if h >= 2:
                        continue
                    q_step = f"MATCH (n)-[:{_OWNERSHIP_REL_TYPES}]-(nbr) WHERE n.node_id = $curr AND NOT nbr:Case RETURN nbr.node_id"
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

                # Run investigations with watchlist = [tgt_name]
                inv1 = run_deterministic_investigation(src_name, watchlist=[tgt_name], depth=1)
                inv2 = run_deterministic_investigation(src_name, watchlist=[tgt_name], depth=2)
                inv3 = run_deterministic_investigation(src_name, watchlist=[tgt_name], depth=3)

                if inv1["verdict"] == "clear" and inv2["verdict"] == "clear" and inv3["verdict"] == "escalate":
                    primary_matches.append(
                        {
                            "src_id": src_id,
                            "src_name": src_name,
                            "tgt_id": tgt_id,
                            "tgt_name": tgt_name,
                            "cost": cost,
                            "path": sp.data[0].get("path_text"),
                            "inv1": inv1["verdict"],
                            "inv2": inv2["verdict"],
                            "inv3": inv3["verdict"],
                        }
                    )
                    print("!!! MATCH FOUND !!!")
                    print(f"Source: {src_name} ({src_id})")
                    print(f"Target: {tgt_name} ({tgt_id})")
                    print(f"Path: {sp.data[0].get('path_text')} (cost: {cost})")
                    print(f"Verdicts: d1={inv1['verdict']}, d2={inv2['verdict']}, d3={inv3['verdict']}")
                    if len(primary_matches) >= 3:
                        break
    if len(primary_matches) >= 3:
        break

print(f"\nFound {len(primary_matches)} primary matches!")
