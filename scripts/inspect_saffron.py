import sys

sys.path.insert(0, ".")
from core.db import ro

print("--- SAFFRON INVESTMENTS LIMITED ---")
res = ro("ownership", 'MATCH (e:Entity {node_id: "10000221"})-[r]-(n) RETURN labels(n)[0], n.name, type(r)')
for r in res["rows"]:
    print(r)

print("\n--- Cosicosi Company ---")
res2 = ro("ownership", 'MATCH (e:Entity {name: "Cosicosi Company"})-[r]-(n) RETURN labels(n)[0], n.name, type(r)')
for r in res2["rows"]:
    print(r)

print("\n--- MAYER & COLLINS TRADING COMPANY LTD. ---")
res3 = ro("ownership", 'MATCH (e:Entity {node_id: "10191463"})-[r]-(n) RETURN labels(n)[0], n.name, type(r)')
for r in res3["rows"]:
    print(r)
