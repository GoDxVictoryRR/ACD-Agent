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

# Step 1: Find all officers in the graph that have degree == 2 and are not service providers
print("Querying all degree-2 officers in the graph...")
q_all = '''
MATCH (o:Officer)
OPTIONAL MATCH (o)-[r]-()
WITH o, count(r) AS deg
WHERE deg = 2
  AND NOT o.name CONTAINS 'MOSSFON'
  AND NOT o.name CONTAINS 'BEARER'
RETURN o.node_id, o.name
'''
res = ro(GRAPH_NAME, q_all)
deg2_officers = {r[0]: r[1] for r in res.get('rows', []) if not is_sp(r[1])}
print(f"Total clean degree-2 officers in graph: {len(deg2_officers)}")

# Find all entities connected to these degree-2 officers
q_ents = '''
MATCH (e:Entity)-[:OFFICER_OF]-(o:Officer)
WHERE o.node_id IN $ids
RETURN e.name, o.node_id
'''
res_ents = ro(GRAPH_NAME, q_ents, {'ids': list(deg2_officers.keys())})
ent_to_offs = {}
off_to_ents = {}
for ename, oid in res_ents.get('rows', []):
    if not is_sp(ename):
        ent_to_offs.setdefault(ename, set()).add(oid)
        off_to_ents.setdefault(oid, set()).add(ename)

# Find entities e2 that have at least 2 distinct degree-2 officers
bridges = {e2: list(offs) for e2, offs in ent_to_offs.items() if len(offs) >= 2}
print(f"Entities connected to >= 2 degree-2 officers: {len(bridges)}")

chains = []
for e2, offs in bridges.items():
    for i in range(len(offs)):
        for j in range(i + 1, len(offs)):
            o1 = offs[i]
            o2 = offs[j]
            e1_candidates = off_to_ents.get(o1, set()) - {e2}
            e3_candidates = off_to_ents.get(o2, set()) - {e2}
            for e1 in e1_candidates:
                for e3 in e3_candidates:
                    if e1 != e3:
                        chains.append((e1, deg2_officers[o1], e2, deg2_officers[o2], e3))

print(f"Found {len(chains)} full 4-hop chains through degree-2 officers!")
for c in chains[:5]:
    print(f"  {c[0]} -> {c[1]} -> {c[2]} -> {c[3]} -> {c[4]}")

for e1, o1, e2, o2, e3 in chains[:15]:
    r1 = run_deterministic_investigation(e1, watchlist=[e3], depth=1)
    if r1['verdict'] != 'clear':
        continue
    r2 = run_deterministic_investigation(e1, watchlist=[e3], depth=2)
    if r2['verdict'] != 'clear':
        continue
    r3 = run_deterministic_investigation(e1, watchlist=[e3], depth=3)
    r4 = run_deterministic_investigation(e1, watchlist=[e3], depth=4)
    print(f"\nEvaluating: {e1} -> {e3}")
    print(f"  d1: {r1['verdict']} | findings: {[f['rule_id'] for f in r1['evaluation']['findings']]}")
    print(f"  d2: {r2['verdict']} | findings: {[f['rule_id'] for f in r2['evaluation']['findings']]}")
    print(f"  d3: {r3['verdict']} | findings: {[f['rule_id'] for f in r3['evaluation']['findings']]}")
    print(f"  d4: {r4['verdict']} | findings: {[f['rule_id'] for f in r4['evaluation']['findings']]}")
    if r4['verdict'] == 'escalate':
        print("  *** PERFECT CANDIDATE! ***")
        break
