import sys

sys.path.insert(0, ".")
from core.db import ro

# Let's inspect paths between entities where intermediate nodes are NOT Intermediaries
# and NOT THE BEARER, and NOT high-degree hubs.
# Query: find pairs (e1:Entity), (e2:Entity) connected by a path of length 3..4
# where no intermediate node is an Intermediary, and no node is THE BEARER.
q = """
MATCH p = (e1:Entity)-[r1:OFFICER_OF|SHAREHOLDER_OF|DIRECTOR_OF|CONNECTED_TO|BENEFICIARY_OF]-(m1)
          -[r2:OFFICER_OF|SHAREHOLDER_OF|DIRECTOR_OF|CONNECTED_TO|BENEFICIARY_OF]-(m2)
          -[r3:OFFICER_OF|SHAREHOLDER_OF|DIRECTOR_OF|CONNECTED_TO|BENEFICIARY_OF]-(e2:Entity)
WHERE e1 <> e2
  AND NOT m1:Intermediary AND NOT m2:Intermediary
  AND NOT m1:Case AND NOT m2:Case
  AND coalesce(m1.name, '') <> 'THE BEARER'
  AND coalesce(m2.name, '') <> 'THE BEARER'
  AND m1.name IS NOT NULL AND m2.name IS NOT NULL
RETURN e1.name, labels(m1)[0], m1.name, labels(m2)[0], m2.name, e2.name
LIMIT 20
"""

try:
    res = ro("ownership", q)
    print("Found hub-free paths of length 3:", len(res["rows"]))
    for r in res["rows"][:10]:
        print(f"{r[0]} -> ({r[1]}: {r[2]}) -> ({r[3]}: {r[4]}) -> {r[5]}")
except Exception as e:
    print("Error querying hub-free paths:", e)
