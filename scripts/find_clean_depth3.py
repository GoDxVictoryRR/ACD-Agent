import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from collections import deque

from agent.fallback import run_deterministic_investigation
from core.db import ro
from core.tools import _OWNERSHIP_REL_TYPES, path_between

print("Searching for E1 -[r1]- N1 -[r2]- E2 -[r3]- E3 where deg(N1)<5 and deg(N2)<5...")

# We want:
# e1: Entity
# n1: Officer or Intermediary or Address with degree < 5
# e2: Entity
# n2: Officer or Intermediary or Address with degree < 5 or direct relationship between e2 and e3
q = """
MATCH (e1:Entity)-[r1]-(n1:Officer)-[r2]-(e2:Entity)-[r3]-(n2:Officer)-[r4]-(e3:Entity)
WHERE e1.node_id <> e2.node_id AND e2.node_id <> e3.node_id AND e1.node_id <> e3.node_id
  AND NOT e1:Case AND NOT e2:Case AND NOT e3:Case
WITH e1, n1, e2, n2, e3
LIMIT 200
MATCH (n1)-[rn1]-()
WITH e1, n1, e2, n2, e3, count(rn1) AS deg1
WHERE deg1 < 5
MATCH (n2)-[rn2]-()
WITH e1, n1, e2, n2, e3, deg1, count(rn2) AS deg2
WHERE deg2 < 5
RETURN e1.node_id, e1.name, e3.node_id, e3.name, deg1, deg2
LIMIT 20
"""

# Wait, the above is 4 hops: e1 - n1 - e2 - n2 - e3 is 4 hops!
# What is 3 hops?
# e1:Entity -[r1]- n1 -[r2]- e2:Entity -[r3]- e3:Entity (if r3 is SAME_AS or CONNECTED_TO)
# OR
# e1:Entity -[r1]- n1 -[r2]- n2 -[r3]- e3:Entity (where n1 is Officer and n2 is Intermediary)
# Let's search both!

q3_same_as = """
MATCH (e1:Entity)-[r1]-(n1:Officer)-[r2]-(e2:Entity)-[r3:SAME_AS|SAME_NAME_AS|CONNECTED_TO]-(e3:Entity)
WHERE e1.node_id <> e2.node_id AND e2.node_id <> e3.node_id AND e1.node_id <> e3.node_id
  AND NOT e1:Case AND NOT e2:Case AND NOT e3:Case
WITH e1, n1, e2, r3, e3
MATCH (n1)-[rn1]-()
WITH e1, n1, e2, r3, e3, count(rn1) AS deg1
WHERE deg1 < 5
RETURN e1.node_id, e1.name, e3.node_id, e3.name, deg1
LIMIT 30
"""

res = ro("ownership", q3_same_as)
print(f"Found {len(res.get('rows', []))} candidate pairs via SAME_AS/CONNECTED_TO")

found = []
for e1_id, e1_name, e3_id, e3_name, deg1 in res.get("rows", []):
    # Check uniqueness of names
    cnt1 = ro(
        "ownership", "MATCH (e:Entity) WHERE toLower(e.name) = toLower($name) RETURN count(e)", {"name": e1_name}
    )["rows"][0][0]
    cnt3 = ro(
        "ownership", "MATCH (e:Entity) WHERE toLower(e.name) = toLower($name) RETURN count(e)", {"name": e3_name}
    )["rows"][0][0]
    if cnt1 != 1 or cnt3 != 1:
        continue

    # Test path_between
    sp = path_between(e1_id, e3_id, max_depth=4)
    if sp.status != "ok" or not sp.data:
        continue
    cost = sp.data[0].get("path_weight", 999.0)
    nodes = sp.data[0].get("nodes", [])
    if len(nodes) - 1 != 3 or cost > 8.0:
        continue

    # BFS verify no path at depth 1 or 2
    bfs_dist = {}
    queue = deque([(e1_id, 0)])
    bfs_dist[e1_id] = 0
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

    # Test investigations
    inv1 = run_deterministic_investigation(e1_name, watchlist=[e3_name], depth=1)
    inv2 = run_deterministic_investigation(e1_name, watchlist=[e3_name], depth=2)
    inv3 = run_deterministic_investigation(e1_name, watchlist=[e3_name], depth=3)

    print(f"Candidate: {e1_name} -> {e3_name}")
    print(f"  d1: {inv1['verdict']} (findings={len(inv1['evaluation']['findings'])})")
    print(f"  d2: {inv2['verdict']} (findings={len(inv2['evaluation']['findings'])})")
    print(f"  d3: {inv3['verdict']} (findings={len(inv3['evaluation']['findings'])})")

    if (
        len(inv1["evaluation"]["findings"]) == 0
        and len(inv2["evaluation"]["findings"]) == 0
        and inv3["verdict"] == "escalate"
    ):
        found.append(
            {
                "e1_id": e1_id,
                "e1_name": e1_name,
                "e3_id": e3_id,
                "e3_name": e3_name,
                "cost": cost,
                "path": sp.data[0].get("path_text"),
            }
        )
        print("  *** PERFECT MATCH FOUND ***")
        break

print(f"\nTotal matches: {len(found)}")
