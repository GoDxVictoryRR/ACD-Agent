from core.db import drop_graph, ro, rw

sg = "test_bidirectional"
try:
    drop_graph(sg)
    rw(
        sg,
        """
    CREATE (e1:ScratchNode {node_id: '1', name: 'Entity1', label: 'Entity'}),
           (hub:ScratchNode {node_id: '2', name: 'HubOfficer', label: 'Officer'}),
           (e2:ScratchNode {node_id: '3', name: 'Entity2', label: 'Entity'}),
           (e3:ScratchNode {node_id: '4', name: 'Entity3', label: 'Entity'}),
           (hub)-[:CONNECTED_TO]->(e1), (e1)-[:CONNECTED_TO]->(hub),
           (hub)-[:CONNECTED_TO]->(e2), (e2)-[:CONNECTED_TO]->(hub),
           (hub)-[:CONNECTED_TO]->(e3), (e3)-[:CONNECTED_TO]->(hub)
    """,
    )

    bw = ro(
        sg,
        "CALL algo.betweenness({nodeLabels:['ScratchNode'], relationshipTypes:['CONNECTED_TO'], samplingSize:32, samplingSeed:42}) YIELD node, score RETURN node.name, score",
    )
    print("Betweenness with bidirectional edges:", bw.get("rows"))

    pr = ro(sg, "CALL algo.pageRank('ScratchNode', 'CONNECTED_TO') YIELD node, score RETURN node.name, score")
    print("PageRank with bidirectional edges:", pr.get("rows"))

    wcc = ro(sg, "CALL algo.WCC() YIELD node, componentId RETURN node.name, componentId")
    print("WCC:", wcc.get("rows"))

    lp = ro(
        sg,
        "CALL algo.labelPropagation({nodeLabels:['ScratchNode'], relationshipTypes:['CONNECTED_TO'], maxIterations:10}) YIELD node, communityId RETURN node.name, communityId",
    )
    print("labelPropagation:", lp.get("rows"))

finally:
    drop_graph(sg)
