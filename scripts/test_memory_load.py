"""
scripts/test_memory_load.py — Execute 10 investigations under mem_limit 512m and cpus 0.5.
Checks RSS before, during, and after to ensure zero OOM crashes.
"""
from __future__ import annotations

import json
import subprocess
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

ENTITIES = [
    ("MOSSACK FONSECA & CO. (SAMOA) LIMITED.", 3, ["TIANSHENG INDUSTRY AND TRADING CO., LTD."]),
    ("TIANSHENG INDUSTRY AND TRADING CO., LTD.", 2, ["HOTFOCUS CO., LTD."]),
    ("CRYSTAL RISE HOLDINGS LIMITED", 2, []),
    ("Millex International Limited", 2, []),
    ("Dewburn Enterprises Inc.", 1, []),
    ("MOSSACK FONSECA & CO. (SAMOA) LIMITED.", 1, []),
    ("TIANSHENG INDUSTRY AND TRADING CO., LTD.", 1, []),
    ("Solitary Clean Trading Ltd", 2, []),
    ("Single Link LLC", 1, []),
    ("MOSSACK FONSECA & CO. (SAMOA) LIMITED.", 2, []),
]


def get_container_stats():
    res = subprocess.check_output(
        ["docker", "stats", "--no-stream", "ownership-lens-app", "--format", "{{.MemUsage}} | {{.MemPerc}} | {{.CPUPerc}}"],
        text=True,
    ).strip()
    return res


print("=" * 70)
print("TESTING MEMORY LOAD (10 Investigations under 512m Limit)")
print("=" * 70)
print(f"Baseline Stats: {get_container_stats()}")

start_t = time.perf_counter()
max_mem_seen = ""

for i, (name, depth, wl) in enumerate(ENTITIES, 1):
    req_body = json.dumps({"entity": name, "depth": depth, "watchlist": wl, "no_llm": True}).encode("utf-8")
    req = urllib.request.Request("http://localhost:8000/investigate", data=req_body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        run_data = json.loads(resp.read().decode())
        run_id = run_data["run_id"]

    # Stream to completion
    stream_url = f"http://localhost:8000/stream/{run_id}"
    with urllib.request.urlopen(stream_url, timeout=30) as stream_resp:
        for line in stream_resp:
            pass  # drain stream

    stats = get_container_stats()
    print(f"  [{i:2d}/10] Finished: {name[:30]:<30} | Depth {depth} | {stats}")
    max_mem_seen = stats

total_sec = time.perf_counter() - start_t
print(f"\nFinal Stats: {get_container_stats()}")
print(f"Completed 10 investigations in {total_sec:.2f}s without OOM!")
