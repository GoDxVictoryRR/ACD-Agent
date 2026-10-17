from core.db import drop_graph, ro, rw

sg = "test_algo_scratch"
try:
    drop_graph(sg)
    rw(
        sg,
        """
    CREATE (a:ScratchNode {node_id: '1', name: 'Alpha', label: 'Entity'}),
           (b:ScratchNode {node_id: '2', name: 'Beta', label: 'Officer'}),
           (c:ScratchNode {node_id: '3', name: 'Gamma', label: 'Entity'}),
           (d:ScratchNode {node_id: '4', name: 'Delta', label: 'Entity'}),
           (a)-[:CONNECTED_TO {weight: 1.0}]->(b),
           (b)-[:CONNECTED_TO {weight: 1.0}]->(c),
           (c)-[:CONNECTED_TO {weight: 1.0}]->(d)
    """,
    )

    # 1. pageRank
    pr = ro(sg, "CALL algo.pageRank('ScratchNode', 'CONNECTED_TO') YIELD node, score RETURN node.name, score")
    print("pageRank:", pr.get("rows"))

    # 2. betweenness
    bw = ro(
        sg,
        "CALL algo.betweenness({nodeLabels:['ScratchNode'], relationshipTypes:['CONNECTED_TO'], samplingSize:32, samplingSeed:42}) YIELD node, score RETURN node.name, score",
    )
    print("betweenness:", bw.get("rows"))

    # 3. WCC
    wcc = ro(sg, "CALL algo.WCC() YIELD node, componentId RETURN node.name, componentId")
    print("WCC:", wcc.get("rows"))

    # 4. labelPropagation
    lp = ro(
        sg,
        "CALL algo.labelPropagation({nodeLabels:['ScratchNode'], relationshipTypes:['CONNECTED_TO'], maxIterations:10}) YIELD node, communityId RETURN node.name, communityId",
    )
    print("labelPropagation:", lp.get("rows"))

finally:
    drop_graph(sg)
    print("Cleaned up scratch graph.")
