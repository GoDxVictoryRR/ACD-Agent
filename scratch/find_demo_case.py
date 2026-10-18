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
MATCH (e1:Entity)-[:OFFICER_OF]-(o1:Officer)-[:OFFICER_OF]-(e2:Entity)-[:OFFICER_OF]-(o2:Officer)-[:OFFICER_OF]-(e3:Entity)
WHERE e1 <> e2 AND e2 <> e3 AND e1 <> e3
  AND NOT o1.name CONTAINS 'MOSSFON'
  AND NOT o2.name CONTAINS 'MOSSFON'
RETURN DISTINCT e1.name, e3.name
LIMIT 200
'''
res = ro(GRAPH_NAME, q)
pairs = res.get('rows', [])
print(f"Checking {len(pairs)} pairs...")

found = []
for e1, e3 in pairs:
    if is_sp(e1) or is_sp(e3):
        continue
    r1 = run_deterministic_investigation(e1, watchlist=[e3], depth=1)
    if r1['verdict'] != 'clear':
        continue
    r2 = run_deterministic_investigation(e1, watchlist=[e3], depth=2)
    if r2['verdict'] != 'clear':
        continue
    r3 = run_deterministic_investigation(e1, watchlist=[e3], depth=3)
    r4 = run_deterministic_investigation(e1, watchlist=[e3], depth=4)
    print(f"MATCH: {e1} -> {e3} | d1={r1['verdict']} d2={r2['verdict']} d3={r3['verdict']} d4={r4['verdict']}")
    found.append((e1, e3, r1['verdict'], r2['verdict'], r3['verdict'], r4['verdict']))
    if len(found) >= 5:
        break

print(f"Total found: {len(found)}")
