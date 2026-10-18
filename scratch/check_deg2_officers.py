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
MATCH (o:Officer)
OPTIONAL MATCH (o)-[r]-()
WITH o, count(r) AS deg
WHERE deg = 2
  AND NOT o.name CONTAINS 'MOSSFON'
  AND NOT o.name CONTAINS 'BEARER'
RETURN o.name
LIMIT 100
'''
res = ro(GRAPH_NAME, q)
officers = [r[0] for r in res.get('rows', []) if not is_sp(r[0])]
print(f"Sample clean degree-2 officers: {len(officers)}")

# Map each officer to the 2 entities they connect
connections = {}
entity_to_officers = {}
for off in officers:
    eq = 'MATCH (e:Entity)-[:OFFICER_OF]-(o:Officer {name: $n}) RETURN e.name'
    ents = list(dict.fromkeys([e[0] for e in ro(GRAPH_NAME, eq, {'n': off}).get('rows', []) if not is_sp(e[0])]))
    if len(ents) == 2:
        connections[off] = ents
        for e in ents:
            entity_to_officers.setdefault(e, []).append(off)

print(f"Officers cleanly connecting exactly 2 non-SP entities: {len(connections)}")
for off, ents in list(connections.items())[:10]:
    print(f"  {off} -> {ents[0]} <-> {ents[1]}")

# Now look for 2-hop entity paths: e1 -(o1)-> e2 -(o2)-> e3
chains = []
for e2, offs in entity_to_officers.items():
    if len(offs) >= 2:
        for i in range(len(offs)):
            for j in range(i + 1, len(offs)):
                o1 = offs[i]
                o2 = offs[j]
                e1 = [x for x in connections[o1] if x != e2][0]
                e3 = [x for x in connections[o2] if x != e2][0]
                if e1 != e3:
                    chains.append((e1, o1, e2, o2, e3))

print(f"\nFound {len(chains)} 4-hop chains between ordinary entities where BOTH officers have degree == 2!")
for c in chains[:10]:
    print(f"  {c[0]} -(deg2: {c[1]})-> {c[2]} -(deg2: {c[3]})-> {c[4]}")

# Test investigations for these chains!
found_matches = []
for e1, o1, e2, o2, e3 in chains:
    r1 = run_deterministic_investigation(e1, watchlist=[e3], depth=1)
    if r1['verdict'] != 'clear':
        continue
    r2 = run_deterministic_investigation(e1, watchlist=[e3], depth=2)
    if r2['verdict'] != 'clear':
        continue
    r3 = run_deterministic_investigation(e1, watchlist=[e3], depth=3)
    r4 = run_deterministic_investigation(e1, watchlist=[e3], depth=4)
    print(f"\nTEST: {e1} -> {e3} (via {e2})")
    print(f"  d1: {r1['verdict']} (links: {r1['evaluation']['total_links']}, findings: {[f['rule_id'] for f in r1['evaluation']['findings']]})")
    print(f"  d2: {r2['verdict']} (links: {r2['evaluation']['total_links']}, findings: {[f['rule_id'] for f in r2['evaluation']['findings']]})")
    print(f"  d3: {r3['verdict']} (links: {r3['evaluation']['total_links']}, findings: {[f['rule_id'] for f in r3['evaluation']['findings']]})")
    print(f"  d4: {r4['verdict']} (links: {r4['evaluation']['total_links']}, findings: {[f['rule_id'] for f in r4['evaluation']['findings']]})")
    if r4['verdict'] == 'escalate':
        found_matches.append((e1, e3, o1, e2, o2))
        print("  >>> PERFECT MATCH FOUND! <<<")
        break

print(f"\nTotal perfect matches: {len(found_matches)}")
