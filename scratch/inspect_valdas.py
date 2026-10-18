import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent.fallback import run_deterministic_investigation
from core.config import GRAPH_NAME
from core.db import ro
from core.tools import path_between, resolve_entity

e1_info = resolve_entity('VALDAS LIMITED')
e2_info = resolve_entity('Podilympus Trading Limited')
print('VALDAS LIMITED:', e1_info.data)
print('Podilympus Trading Limited:', e2_info.data)

e1_id = e1_info.data[0]['node_id']
e2_id = e2_info.data[0]['node_id']

# Inspect path
pb = path_between(e1_id, e2_id, max_depth=4, is_watchlist=True)
print('\nPath Between status:', pb.status)
if pb.data:
    print('Path weight:', pb.data[0].get('path_weight'))
    print('Nodes on path:')
    for n in pb.data[0].get('nodes', []):
        lbl = n.get('label')
        nm = n.get('name')
        nid = n.get('id')
        print(f"  - {lbl}: {nm} (id: {nid})")
        # Check degree
        deg_res = ro(GRAPH_NAME, f"MATCH (n {{node_id: '{nid}'}})-[r]-() RETURN count(r)")
        print(f"    Degree in graph: {deg_res.get('rows', [[0]])[0][0]}")
    print('Relationships on path:')
    for r in pb.data[0].get('relationships', []):
        print(f"  - {r.get('type')}: weight {r.get('weight')}")

print('\nDeterministic Investigations:')
for d in [1, 2, 3, 4]:
    res = run_deterministic_investigation('VALDAS LIMITED', watchlist=['Podilympus Trading Limited'], depth=d)
    print(f'=== Depth {d} ===')
    print('Verdict:', res['verdict'])
    print('Total links:', res['evaluation']['total_links'])
    print('Findings:')
    for f in res['evaluation']['findings']:
        print('  *', f['rule_id'], '|', f['text'])
