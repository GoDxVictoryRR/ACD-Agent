"""Test Item 10: Remove FalkorDB and verify health + error handling."""
import subprocess
import time

import httpx

API = "http://localhost:8000"

print("=== 1. Health when DB is UP ===")
r = httpx.get(f"{API}/health", timeout=5)
print("Health:", r.status_code, r.json())
assert r.json()["db"] == "ok"
assert r.json()["mode"] == "live"

print("\n=== 2. Stopping FalkorDB service ===")
subprocess.run(["docker", "compose", "stop", "falkordb"], check=True)
time.sleep(2)

try:
    print("\n=== 3. Health when DB is DOWN ===")
    r = httpx.get(f"{API}/health", timeout=5)
    print("Health:", r.status_code, r.json())
    assert r.json()["db"] == "down"
    assert r.json()["mode"] == "replay-only"
    print("[PASS] /health shows db=down and mode=replay-only")

    print("\n=== 4. POST /investigate when DB is DOWN ===")
    r_inv = httpx.post(f"{API}/investigate", json={
        "entity": "Blue Star Maritime Holdings Ltd",
        "watchlist": [],
        "depth": 3
    }, timeout=5)
    print("Investigate response:", r_inv.status_code, r_inv.json())
    assert r_inv.status_code == 503
    print(f"[PASS] /investigate failed loudly with 503: {r_inv.json()['detail']}")

finally:
    print("\n=== 5. Restarting FalkorDB service ===")
    subprocess.run(["docker", "compose", "start", "falkordb"], check=True)
    time.sleep(3)
    r = httpx.get(f"{API}/health", timeout=5)
    print("Restored Health:", r.status_code, r.json())
    assert r.json()["db"] == "ok"
    assert r.json()["mode"] == "live"
    print("[PASS] FalkorDB successfully restored, health back to live.")

print("\nOVERALL: ITEM 10 (REMOVE FALKORDB) PASS")
