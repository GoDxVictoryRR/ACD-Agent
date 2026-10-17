import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.db import drop_graph, ro, rw
from data.load import apply_indexes

g = "test_speed"
drop_graph(g)
apply_indexes(g)

# create 1000 entities and 1000 officers
rw(g, "UNWIND range(1, 1000) AS i CREATE (:Entity {node_id: 'E_' + toString(i), name: 'Ent ' + toString(i)})")
rw(g, "UNWIND range(1, 1000) AS i CREATE (:Officer {node_id: 'O_' + toString(i), name: 'Off ' + toString(i)})")

# test inserting 1000 relationships
batch = [{"start_id": f"O_{i}", "end_id": f"E_{i}", "link": "officer of", "weight": 1.0} for i in range(1, 1001)]
t0 = time.perf_counter()
rw(
    g,
    "UNWIND $batch AS row MATCH (src {node_id: row.start_id}) MATCH (dst {node_id: row.end_id}) CREATE (src)-[:OFFICER_OF {link: row.link, weight: row.weight}]->(dst)",
    {"batch": batch},
)
t1 = time.perf_counter()
print(f"1000 rels loaded in {t1 - t0:.2f}s")

cnt = ro(g, "MATCH ()-[r]->() RETURN count(r)")["rows"][0][0]
print(f"Count: {cnt}")
drop_graph(g)
