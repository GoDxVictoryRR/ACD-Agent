import sys

sys.path.insert(0, ".")
from core.db import ro

# Let's search for entities where:
# 1. Target entity e1 has depth 1 neighborhood that does NOT include e2 or any direct connection to e2.
# 2. Shortest path via non-intermediary, non-bearer edges has length exactly 3 or 4.
q = """
MATCH p = (e1:Entity)<-[:OFFICER_OF]-(o1:Officer)-[:OFFICER_OF]->(e2:Entity)<-[:OFFICER_OF]-(o2:Officer)-[:OFFICER_OF]->(e3:Entity)
WHERE o1.node_id <> o2.node_id
  AND e1.node_id <> e2.node_id
  AND e2.node_id <> e3.node_id
  AND e1.node_id <> e3.node_id
  AND toUpper(trim(o1.name)) <> 'THE BEARER'
  AND toUpper(trim(o2.name)) <> 'THE BEARER'
  AND toUpper(trim(o1.name)) <> 'MOSSFON SUBSCRIBERS LTD.'
  AND toUpper(trim(o2.name)) <> 'MOSSFON SUBSCRIBERS LTD.'
  // Ensure no direct 2-hop path between e1 and e3:
  AND NOT (e1)<-[:OFFICER_OF]-()-[:OFFICER_OF]->(e3)
RETURN e1.name, e1.node_id, o1.name, e2.name, o2.name, e3.name, e3.node_id
LIMIT 20
"""

try:
    res = ro("ownership", q)
    print("Found candidate pairs with no 2-hop connection:", len(res["rows"]))
    for r in res["rows"][:10]:
        print(f"Target: '{r[0]}' ({r[1]}) --[{r[2]}]--> '{r[3]}' --[{r[4]}]--> TargetWatchlist: '{r[5]}' ({r[6]})")
except Exception as e:
    print("Error:", e)
