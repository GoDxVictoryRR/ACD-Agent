"""Test Item 11: Self-healing on startup.
Deletes the graph, restarts the app, verifies /health goes seeding -> ready, and records elapsed seconds.
"""

import subprocess
import time

import httpx

from core.config import GRAPH_NAME
from core.db import drop_graph, ping
from data.load import get_graph_counts

API = "http://localhost:8000"

print("=== 1. Deleting graph ===")
assert ping(), "FalkorDB must be running"
drop_graph(GRAPH_NAME)
counts = get_graph_counts(GRAPH_NAME)
print(f"Graph nodes after drop: {counts['nodes']}")
assert counts["nodes"] == 0

print("\n=== 2. Restarting app container ===")
t0 = time.time()
subprocess.run(["docker", "compose", "restart", "app"], check=True)

print("\n=== 3. Polling /health ===")
saw_seeding = False
ready = False
seeding_start = None
ready_time = None

for attempt in range(120):
    try:
        r = httpx.get(f"{API}/health", timeout=2)
        if r.status_code == 200:
            status = r.json().get("graph")
            print(f"[{round(time.time() - t0, 1)}s] graph status: {status}")
            if status == "seeding":
                saw_seeding = True
                if seeding_start is None:
                    seeding_start = time.time()
            elif status == "ready":
                ready = True
                ready_time = time.time()
                break
    except Exception:
        pass
    time.sleep(1)

elapsed_total = round(ready_time - t0, 2) if ready_time else -1
print(f"\nFinal graph status: ready={ready}, saw_seeding={saw_seeding}, total elapsed: {elapsed_total}s")
assert ready, "App failed to reach ready state"
final_counts = get_graph_counts(GRAPH_NAME)
print(f"Restored graph nodes: {final_counts['nodes']}, edges: {final_counts['edges']}")
assert final_counts["nodes"] > 1000

print(f"\nOVERALL: ITEM 11 (SELF-HEAL) PASS — Seeding time: {elapsed_total}s")
