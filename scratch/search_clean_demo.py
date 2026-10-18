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
LIMIT 200
'''
res = ro(GRAPH_NAME, q)
rows = res.get('rows', [])

valid_pairs = []
for e1_name, o1_name, e2_name, o2_name, e3_name in rows:
    if not is_sp(e1_name) and not is_sp(e2_name) and not is_sp(e3_name) and not is_sp(o1_name) and not is_sp(o2_name):
        d1 = ro(GRAPH_NAME, f"MATCH (o:Officer {{name: '{o1_name}'}})-[r]-() RETURN count(r)").get('rows', [[0]])[0][0]
        d2 = ro(GRAPH_NAME, f"MATCH (o:Officer {{name: '{o2_name}'}})-[r]-() RETURN count(r)").get('rows', [[0]])[0][0]
        if d1 <= 14 and d2 <= 14:
            valid_pairs.append((e1_name, e3_name, o1_name, d1, e2_name, o2_name, d2))

print(f"Testing {len(valid_pairs)} candidate pairs for depth 1=clear, depth 2=clear, depth 4=escalate...")

found = []
for e1, e3, o1, d1, e2, o2, d2 in valid_pairs:
    r1 = run_deterministic_investigation(e1, watchlist=[e3], depth=1)
    if r1['verdict'] != 'clear':
        continue
    r2 = run_deterministic_investigation(e1, watchlist=[e3], depth=2)
    if r2['verdict'] != 'clear':
        continue
    r3 = run_deterministic_investigation(e1, watchlist=[e3], depth=3)
    r4 = run_deterministic_investigation(e1, watchlist=[e3], depth=4)
    print(f"SUCCESS: {e1} -> {e3} | d1={r1['verdict']} d2={r2['verdict']} d3={r3['verdict']} d4={r4['verdict']}")
    print(f"  Path: {e1} -[OFFICER_OF]-> {o1} (deg {d1}) -[OFFICER_OF]-> {e2} -[OFFICER_OF]-> {o2} (deg {d2}) -[OFFICER_OF]-> {e3}")
    found.append((e1, e3, r1['verdict'], r2['verdict'], r3['verdict'], r4['verdict']))
    if len(found) >= 5:
        break

print(f"\nTotal matches: {len(found)}")
