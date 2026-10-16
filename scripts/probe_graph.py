"""Diagnostic probe for graph issues."""
import sys

sys.path.insert(0, r"C:\Users\hardi\Downloads\ACD-agent")

from core.db import ro

# Check paths with and without Case nodes
r = ro("ownership", """
MATCH path = (e:Entity {node_id: $eid})-[*1..1]-(target)
WHERE NOT target:Case
RETURN [n in nodes(path) | {id: n.node_id, name: coalesce(n.name, n.address, '?'), label: labels(n)[0]}] AS pn,
       [rel in relationships(path) | type(rel)] AS rels
LIMIT 20
""", {"eid": "ENT_BLUESTAR_01"})
print("Paths at d=1 excluding Case nodes:")
for row in r.get("rows", []):
    path_str = " -> ".join(f"{n['name']}({n['label']})" for n in row[0])
    print(f"  {path_str} | rels: {row[1]}")

print()
r2 = ro("ownership", """
MATCH path = (e:Entity {node_id: $eid})-[*1..1]-(target)
RETURN [n in nodes(path) | {id: n.node_id, name: coalesce(n.name, n.address, '?'), label: labels(n)[0]}] AS pn,
       [rel in relationships(path) | type(rel)] AS rels
LIMIT 20
""", {"eid": "ENT_BLUESTAR_01"})
print("Paths at d=1 INCLUDING Case nodes:")
for row in r2.get("rows", []):
    path_str = " -> ".join(f"{n['name']}({n['label']})" for n in row[0])
    print(f"  {path_str} | rels: {row[1]}")

print()
print("d=1 total without Case:", len(r.get("rows", [])))
print("d=1 total with Case:", len(r2.get("rows", [])))

# Inspect the planted 3-hop path
print()
r3 = ro("ownership", """
MATCH path = (e:Entity {node_id: $eid})-[*1..4]-(t:Entity)
WHERE t.node_id = 'ENT_IRONCLAD_SANCTIONS'
RETURN [n in nodes(path) | {name: coalesce(n.name, n.address, '?'), label: labels(n)[0]}] AS pn,
       [rel in relationships(path) | type(rel)] AS rels,
       length(path) AS hops
ORDER BY hops
LIMIT 5
""", {"eid": "ENT_BLUESTAR_01"})
print("Paths from Blue Star to Ironclad:")
for row in r3.get("rows", []):
    path_str = " -> ".join(f"{n['name']}({n['label']})" for n in row[0])
    print(f"  [{row[2]} hops] {path_str}")
    print(f"  rels: {row[1]}")
