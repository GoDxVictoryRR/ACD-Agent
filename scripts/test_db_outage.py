"""
scripts/test_db_outage.py — Test stopping falkordb-server:
- /health returns db: down, mode: replay-only
- /investigate fails loudly with 503
- Restart falkordb-server and measure self-heal time
"""
from __future__ import annotations

import json
import subprocess
import time
import urllib.request
import urllib.error

print("=" * 70)
print("TESTING FALKORDB SERVICE OUTAGE & SELF-HEALING RESILIENCE")
print("=" * 70)

# Step 1: Initial health
req = urllib.request.Request("http://localhost:8000/health")
with urllib.request.urlopen(req, timeout=5) as r:
    h0 = json.loads(r.read().decode())
print(f"[STEP 1] Initial Health: db={h0['db']}, graph={h0['graph']}, mode={h0['mode']}")
assert h0["db"] == "ok"

# Step 2: Stop falkordb-server
print("\n[STEP 2] Stopping falkordb-server container...")
subprocess.run(["docker", "stop", "falkordb-server"], check=True)

try:
    # Step 3: Verify /health is red
    time.sleep(1)
    req = urllib.request.Request("http://localhost:8000/health")
    with urllib.request.urlopen(req, timeout=5) as r:
        h_down = json.loads(r.read().decode())
    print(f"[STEP 3] Outage Health: db={h_down['db']}, graph={h_down['graph']}, mode={h_down['mode']}")
    assert h_down["db"] == "down", f"Expected db: down, got {h_down['db']}"
    assert h_down["mode"] == "replay-only", f"Expected mode: replay-only, got {h_down['mode']}"
    print("  PASS: /health correctly reported red (db: down, mode: replay-only).")

    # Step 4: Verify /investigate fails loudly with 503
    print("\n[STEP 4] Sending /investigate during outage...")
    req_body = json.dumps({"entity": "MOSSACK FONSECA & CO. (SAMOA) LIMITED.", "depth": 1}).encode("utf-8")
    req_inv = urllib.request.Request("http://localhost:8000/investigate", data=req_body, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req_inv, timeout=5)
        assert False, "/investigate should have failed with 503 during outage"
    except urllib.error.HTTPError as e:
        print(f"  PASS: /investigate failed loudly with HTTP {e.code} Service Unavailable: {e.reason}")
        assert e.code == 503, f"Expected 503, got {e.code}"
finally:
    # Step 5: Restart falkordb-server and measure self-heal timing
    print("\n[STEP 5] Restarting falkordb-server...")
    t_start = time.perf_counter()
    subprocess.run(["docker", "start", "falkordb-server"], check=True)

    healed = False
    for attempt in range(30):
        try:
            req = urllib.request.Request("http://localhost:8000/health")
            with urllib.request.urlopen(req, timeout=2) as r:
                h_healed = json.loads(r.read().decode())
                if h_healed["db"] == "ok" and h_healed["graph"] == "ready":
                    heal_elapsed = time.perf_counter() - t_start
                    print(f"[STEP 6] Self-healed in {heal_elapsed:.2f}s! Health: db={h_healed['db']}, graph={h_healed['graph']}")
                    healed = True
                    break
        except Exception:
            pass
        time.sleep(0.5)

assert healed, "Database did not self-heal within timeout"
print("\nALL OUTAGE & SELF-HEAL TESTS PASSED!")
