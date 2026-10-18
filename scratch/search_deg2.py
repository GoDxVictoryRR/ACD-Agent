import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent.fallback import run_deterministic_investigation
from core.config import GRAPH_NAME
from core.db import ro
from core.rules import is_placeholder_name

SERVICE_PATTERNS = [
    'mossack', 'fonseca', 'mossfon', 'portcullis', 'trust', 'management',
    'services', 'nominee', 'nominees', 'corporate services',
    'fiduciary', 'secretarial', 'consulting', 'registrars',
    'agents', 'solicitors', 'law', 'chambers', 'legal', 'advisory'
]

def is_sp(name: str) -> bool:
    if not name or is_placeholder_name(name):
        return True
    nl = name.lower()
    return any(p in nl for p in SERVICE_PATTERNS)

# Find officers with degree exactly 2
q = '''
MATCH (o1:Officer)-[:OFFICER_OF]-(e2:Entity)-[:OFFICER_OF]-(o2:Officer)
WHERE o1 <> o2
  AND NOT o1.name CONTAINS 'MOSSFON' AND NOT o2.name CONTAINS 'MOSSFON'
  AND NOT o1.name CONTAINS 'BEARER' AND NOT o2.name CONTAINS 'BEARER'
WITH o1, e2, o2
MATCH (e1:Entity)-[:OFFICER_OF]-(o1)
MATCH (o2)-[:OFFICER_OF]-(e3:Entity)
WHERE e1 <> e2 AND e2 <> e3 AND e1 <> e3
RETURN DISTINCT e1.name, o1.name, e2.name, o2.name, e3.name
LIMIT 500
'''
res = ro(GRAPH_NAME, q)
rows = res.get('rows', [])

print(f"Total rows: {len(rows)}")
deg_cache = {}
def get_deg(name):
    if name not in deg_cache:
        d = ro(GRAPH_NAME, f"MATCH (n {{name: '{name}'}})-[r]-() RETURN count(r)").get('rows', [[0]])[0][0]
        deg_cache[name] = d
    return deg_cache[name]

qualifying = []
for e1, o1, e2, o2, e3 in rows:
    if is_sp(e1) or is_sp(e2) or is_sp(e3) or is_sp(o1) or is_sp(o2):
        continue
    d_o1 = get_deg(o1)
    d_o2 = get_deg(o2)
    if d_o1 == 2 and d_o2 == 2:
        qualifying.append((e1, o1, e2, o2, e3))

print(f"Qualifying paths where both officers have degree == 2: {len(qualifying)}")
for qp in qualifying[:10]:
    print(qp)

for e1, o1, e2, o2, e3 in qualifying[:10]:
    r1 = run_deterministic_investigation(e1, watchlist=[e3], depth=1)
    r2 = run_deterministic_investigation(e1, watchlist=[e3], depth=2)
    r4 = run_deterministic_investigation(e1, watchlist=[e3], depth=4)
    print(f"\nEvaluating {e1} -> {e3}:")
    print(f"  d1: {r1['verdict']} | findings: {[f['rule_id'] for f in r1['evaluation']['findings']]}")
    print(f"  d2: {r2['verdict']} | findings: {[f['rule_id'] for f in r2['evaluation']['findings']]}")
    print(f"  d4: {r4['verdict']} | findings: {[f['rule_id'] for f in r4['evaluation']['findings']]}")
