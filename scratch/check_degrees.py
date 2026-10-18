import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.config import GRAPH_NAME
from core.db import ro

q = '''
MATCH (o1:Officer)-[:OFFICER_OF]-(e2:Entity)-[:OFFICER_OF]-(o2:Officer)
WHERE o1 <> o2
  AND NOT o1.name CONTAINS 'MOSSFON' AND NOT o2.name CONTAINS 'MOSSFON'
  AND NOT o1.name CONTAINS 'BEARER' AND NOT o2.name CONTAINS 'BEARER'
RETURN o1.name, e2.name, o2.name
LIMIT 20
'''
res = ro(GRAPH_NAME, q)
for o1, e2, o2 in res.get('rows', []):
    d1 = ro(GRAPH_NAME, "MATCH (o:Officer {name: $n})-[r]-() RETURN count(r)", {"n": o1}).get('rows', [[0]])[0][0]
    d2 = ro(GRAPH_NAME, "MATCH (o:Officer {name: $n})-[r]-() RETURN count(r)", {"n": o2}).get('rows', [[0]])[0][0]
    print(f"{o1} (deg {d1}) <-> {e2} <-> {o2} (deg {d2})")
