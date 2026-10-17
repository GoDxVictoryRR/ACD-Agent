from core.db import ro

q = """
MATCH (a {node_id: $a_id}), (b {node_id: $b_id})
WHERE NOT a:Case AND NOT b:Case
CALL algo.SPpaths({
    sourceNode: a,
    targetNode: b,
    relTypes: ['OFFICER_OF', 'SHAREHOLDER_OF', 'INTERMEDIARY_OF', 'REGISTERED_ADDRESS', 'CONNECTED_TO', 'SAME_AS'],
    relDirection: 'both',
    weightProp: 'weight',
    maxLen: 4,
    pathCount: 1
})
YIELD path, pathWeight
RETURN [n in nodes(path) | {
           id: coalesce(n.node_id, ''),
           name: coalesce(n.name, n.address, n.node_id, 'unknown'),
           label: labels(n)[0]
       }] AS path_nodes,
       [r in relationships(path) | {type: type(r), weight: coalesce(r.weight, 2.0)}] AS path_rels,
       pathWeight
"""
try:
    res = ro("ownership", q, {"a_id": "10001171", "b_id": "10000001"})
    print("Success! Rows:", len(res.get("rows", [])))
    if res.get("rows"):
        print("Nodes:", [n["name"] for n in res["rows"][0][0]])
        print("Weight:", res["rows"][0][2])
except Exception as e:
    print("Error:", e)
