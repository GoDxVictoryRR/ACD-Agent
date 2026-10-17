import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from core.db import rw

g = "ownership"

batch = [{"start_id": "12000001", "end_id": "10000001", "link": "test", "weight": 1.0}] * 1000

t0 = time.perf_counter()
res = rw(
    g,
    "UNWIND $batch AS row MATCH (src:Officer {node_id: row.start_id}) MATCH (dst:Entity {node_id: row.end_id}) RETURN count(*)",
    {"batch": batch},
)
t_labeled = time.perf_counter() - t0
print(f"Labeled MATCH 1000 rows: {t_labeled * 1000:.2f} ms")
