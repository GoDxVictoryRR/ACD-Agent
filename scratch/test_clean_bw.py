import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import uuid

from core.config import GRAPH_NAME
from core.db import drop_graph, ro, rw

q = """
MATCH path = (e:Entity {node_id: '10024477'})-[:OFFICER_OF|SHAREHOLDER_OF|DIRECTOR_OF|BENEFICIARY_OF|CONNECTED_TO|RELATED_ENTITY|SAME_AS|SAME_COMPANY_AS*1..2]-(neighbor)
WHERE NOT neighbor:Case
  AND NOT neighbor:Intermediary
  AND NOT neighbor:Address
  AND ALL(n in nodes(path) WHERE NOT n:Case AND NOT n:Intermediary AND NOT n:Address)
RETURN [n in nodes(path) | {id: n.node_id, name: n.name, label: labels(n)[0]}] as nodes,
       [r in relationships(path) | {start_id: startNode(r).node_id, end_id: endNode(r).node_id, weight: coalesce(r.weight, 2.0)}] as rels
"""
res = ro(GRAPH_NAME, q).get('rows', [])
nodes_map = {}
edges_set = set()
for r in res:
    for n in r[0]:
        nodes_map[n['id']] = n
    for rel in r[1]:
        edges_set.add((rel['start_id'], rel['end_id']))
        edges_set.add((rel['end_id'], rel['start_id']))

scratch = 'test_' + uuid.uuid4().hex[:8]
try:
    for nid, n in nodes_map.items():
        rw(scratch, f"CREATE (:ScratchNode {{node_id: '{nid}', name: '{n['name']}'}})")
    for s, e in edges_set:
        rw(scratch, f"MATCH (a:ScratchNode {{node_id: '{s}'}}), (b:ScratchNode {{node_id: '{e}'}}) CREATE (a)-[:CONNECTED_TO]->(b)")
    bw = ro(scratch, 'CALL algo.betweenness({samplingSeed:42}) YIELD node, score RETURN node.node_id, score').get('rows', [])
    print('Betweenness with clean corporate neighbors:', bw)
finally:
    drop_graph(scratch)
