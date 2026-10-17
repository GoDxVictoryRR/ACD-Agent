from core.db import drop_graph, ro, rw
from core.tools import _OWNERSHIP_REL_TYPES

eid = "10005699"  # CRYSTAL RISE HOLDINGS LIMITED
q = f"""
MATCH path = (e:Entity {{node_id: $eid}})-[:{_OWNERSHIP_REL_TYPES}*1..2]-(n)
WHERE NOT n:Case
RETURN [node in nodes(path) | {{id: node.node_id, name: coalesce(node.name, node.address, node.node_id), label: labels(node)[0]}}] AS nodes,
       [r in relationships(path) | {{src: startNode(r).node_id, dst: endNode(r).node_id, weight: coalesce(r.weight, 2.0)}}] AS rels
LIMIT 100
"""
res = ro("ownership", q, {"eid": eid})
rows = res.get("rows", [])
nodes_map = {}
edges_set = set()
for r in rows:
    for n in r[0]:
        nodes_map[n["id"]] = n
    for rel in r[1]:
        edges_set.add((rel["src"], rel["dst"], rel["weight"]))
        # bidirectional
        edges_set.add((rel["dst"], rel["src"], rel["weight"]))

sg = "test_crystal_scratch"
try:
    drop_graph(sg)
    rw(
        sg,
        "UNWIND $batch AS n CREATE (:ScratchNode {node_id: n.id, name: n.name, label: n.label})",
        {"batch": list(nodes_map.values())},
    )
    edge_batch = [{"src": s, "dst": d, "weight": w} for s, d, w in edges_set if s in nodes_map and d in nodes_map]
    rw(
        sg,
        "UNWIND $batch AS e MATCH (s:ScratchNode {node_id: e.src}), (d:ScratchNode {node_id: e.dst}) CREATE (s)-[:CONNECTED_TO {weight: e.weight}]->(d)",
        {"batch": edge_batch},
    )

    bw = ro(
        sg,
        "CALL algo.betweenness({nodeLabels:['ScratchNode'], relationshipTypes:['CONNECTED_TO'], samplingSize:32, samplingSeed:42}) YIELD node, score RETURN node.name, score ORDER BY score DESC LIMIT 5",
    )
    print("Betweenness top:", bw.get("rows"))

    pr = ro(
        sg,
        "CALL algo.pageRank('ScratchNode', 'CONNECTED_TO') YIELD node, score RETURN node.name, score ORDER BY score DESC LIMIT 5",
    )
    print("PageRank top:", pr.get("rows"))

    wcc = ro(sg, "CALL algo.WCC() YIELD node, componentId RETURN node.name, componentId LIMIT 5")
    print("WCC:", wcc.get("rows"))

    lp = ro(
        sg,
        "CALL algo.labelPropagation({nodeLabels:['ScratchNode'], relationshipTypes:['CONNECTED_TO'], maxIterations:10}) YIELD node, communityId RETURN node.name, communityId LIMIT 5",
    )
    print("labelPropagation:", lp.get("rows"))
finally:
    drop_graph(sg)
