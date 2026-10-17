import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from core.db import ro

print("=== Testing algo.SPpaths with pathCount ===")

# Test SPpaths between 10001171 and 10000001
q = """
MATCH (a {node_id: '10001171'}), (b {node_id: '10000001'})
CALL algo.SPpaths({sourceNode: a, targetNode: b, relTypes: ['SAME_AS', 'OFFICER_OF', 'INTERMEDIARY_OF', 'REGISTERED_ADDRESS', 'CONNECTED_TO'], relDirection: 'both', pathCount: 3, weightProp: 'weight'})
YIELD path, pathWeight
RETURN [n in nodes(path) | n.node_id] AS node_ids,
       [n in nodes(path) | coalesce(n.name, n.address)] AS names,
       pathWeight
"""
try:
    res = ro("ownership", q)
    print(f"SPpaths returned {len(res.get('rows', []))} paths:")
    for r in res.get("rows", []):
        print("  Weight:", r[2], "Nodes:", r[1])
except Exception as e:
    print("SPpaths error:", e)
