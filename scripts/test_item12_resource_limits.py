"""Test Item 12: Resource limits and memory measurement.
Runs 10 investigations under 512MB RAM cap, checks for OOM, records RSS and FalkorDB graph memory with 200 Cases.
"""

import subprocess
import time

import httpx

from core.config import GRAPH_NAME
from core.db import ro, rw

API = "http://localhost:8000"

print("=== 1. Checking initial RSS and health ===")
r = httpx.get(f"{API}/health", timeout=5)
print("Health:", r.json())
rss_initial = r.json().get("rss_mb", 0.0)

print("\n=== 2. Running 10 investigations through API ===")
entities = [
    "GLAISDALE LIMITED",
    "Silverline Capital Management Ltd",
    "Orion Global Logistics Corp",
    "Solitary Enterprises Ltd",
]

t_start = time.time()
for i in range(10):
    ent = entities[i % len(entities)]
    depth = 3 if (i % 2 == 0) else 1
    resp = httpx.post(f"{API}/investigate", json={"entity": ent, "depth": depth, "no_llm": True}, timeout=10)
    assert resp.status_code == 200
    run_id = resp.json()["run_id"]
    # Wait for completion via stream
    with httpx.stream("GET", f"{API}/stream/{run_id}", timeout=30) as s:
        for line in s.iter_lines():
            if "event: done" in line or "event: error" in line:
                break
    print(f"  [{i + 1}/10] {ent} (d={depth}) complete")

duration = round(time.time() - t_start, 2)
print(f"10 investigations completed in {duration}s")

print("\n=== 3. Checking for OOM and final RSS ===")
oom_proc = subprocess.run(
    ["docker", "inspect", "-f", "{{.State.OOMKilled}}", "ownership-lens-app"],
    capture_output=True,
    text=True,
    check=True,
)
oom_killed = oom_proc.stdout.strip()
print(f"Docker OOMKilled: {oom_killed}")
assert oom_killed == "false", "App was killed by OOM!"

stats_proc = subprocess.run(
    ["docker", "stats", "--no-stream", "--format", "{{.MemUsage}}", "ownership-lens-app"],
    capture_output=True,
    text=True,
    check=True,
)
mem_usage = stats_proc.stdout.strip()
print(f"Container Memory Usage: {mem_usage}")

print("\n=== 4. Populating 200 Cases and measuring graph memory ===")
# Create up to 200 case nodes
for i in range(1, 201):
    q = "MERGE (c:Case {case_id: $cid}) SET c.verdict = 'clear', c.depth = 2, c.created_at = timestamp() RETURN count(c)"
    rw(GRAPH_NAME, q, {"cid": f"perf_case_{i:03d}"})

case_count_res = ro(GRAPH_NAME, "MATCH (c:Case) RETURN count(c) AS cnt")
total_cases = case_count_res["rows"][0][0]
print(f"Total Case nodes in graph: {total_cases}")

# Check Redis memory
import redis

r_client = redis.Redis(host="localhost", port=6379)
info_mem = r_client.info("memory")
used_memory_human = info_mem.get("used_memory_human")
used_memory_peak_human = info_mem.get("used_memory_peak_human")
print(f"FalkorDB used_memory: {used_memory_human} (peak: {used_memory_peak_human})")

print(f"\nOVERALL: ITEM 12 (RESOURCE LIMITS) PASS — Mem: {mem_usage}, FalkorDB: {used_memory_human}")
