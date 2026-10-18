import sys

sys.path.insert(0, ".")
from core.db import ro

# Find: (e1:Entity)<-[:OFFICER_OF]-(o1:Officer)-[:OFFICER_OF]->(e2:Entity)<-[:OFFICER_OF]-(o2:Officer)-[:OFFICER_OF]->(e3:Entity)
# where o1 <> o2, e1 <> e2, e2 <> e3, e1 <> e3, and NOT o1.name IN ['THE BEARER', 'MOSSFON SUBSCRIBERS LTD.'], NOT o2.name IN ['THE BEARER', 'MOSSFON SUBSCRIBERS LTD.']
q = """
MATCH (e1:Entity)<-[:OFFICER_OF]-(o1:Officer)-[:OFFICER_OF]->(e2:Entity)<-[:OFFICER_OF]-(o2:Officer)-[:OFFICER_OF]->(e3:Entity)
WHERE o1.node_id <> o2.node_id
  AND e1.node_id <> e2.node_id
  AND e2.node_id <> e3.node_id
  AND e1.node_id <> e3.node_id
  AND toUpper(trim(o1.name)) <> 'THE BEARER'
  AND toUpper(trim(o2.name)) <> 'THE BEARER'
  AND toUpper(trim(o1.name)) <> 'MOSSFON SUBSCRIBERS LTD.'
  AND toUpper(trim(o2.name)) <> 'MOSSFON SUBSCRIBERS LTD.'
RETURN e1.name, o1.name, e2.name, o2.name, e3.name
LIMIT 10
"""

try:
    res = ro("ownership", q)
    print("Found multi-hop shell chains via distinct non-bearer officers:", len(res["rows"]))
    for r in res["rows"]:
        print(f"'{r[0]}' --(Officer: {r[1]})--> '{r[2]}' --(Officer: {r[3]})--> '{r[4]}'")
except Exception as e:
    print("Error:", e)
