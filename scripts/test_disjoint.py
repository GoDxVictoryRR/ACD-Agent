import sys
from collections import deque
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from core.db import ro
from core.tools import _OWNERSHIP_REL_TYPES, path_between


def find_disjoint_bfs(a_id: str, b_id: str, excluded_ids: set[str], max_depth: int = 4):
    queue = deque([(a_id, [a_id], 0.0)])
    visited = {a_id} | excluded_ids

    while queue:
        curr, path_nodes, cost = queue.popleft()
        if len(path_nodes) - 1 >= max_depth:
            continue
        q = f"""
        MATCH (n {{node_id: $curr}})-[r:{_OWNERSHIP_REL_TYPES}]-(nbr)
        WHERE NOT nbr:Case
        RETURN nbr.node_id, coalesce(r.weight, 2.0), type(r), coalesce(nbr.name, nbr.address), labels(nbr)[0]
        """
        res = ro("ownership", q, {"curr": curr})
        for nid, weight, rtype, name, lbl in res.get("rows", []):
            if nid == b_id:
                return {
                    "node_ids": path_nodes + [nid],
                    "cost": cost + float(weight),
                    "hops": len(path_nodes),
                }
            if nid not in visited:
                visited.add(nid)
                queue.append((nid, path_nodes + [nid], cost + float(weight)))
    return None


# Test with 10001171 and 10000001
sp = path_between("10001171", "10000001", max_depth=4)
p1 = sp.data[0]
intermediate_ids = set(n["id"] for n in p1["nodes"][1:-1])
print("Path 1:", [n["name"] for n in p1["nodes"]])
print("Intermediate IDs to exclude:", intermediate_ids)

p2 = find_disjoint_bfs("10001171", "10000001", intermediate_ids, max_depth=4)
print("Disjoint Path 2:", p2)
