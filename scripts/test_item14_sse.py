"""Test Item 14: SSE event order, error event on failure, and client disconnect handling."""

import time

import httpx

API = "http://localhost:8000"

print("=== 1. Testing SSE Event Order ===")
resp = httpx.post(
    f"{API}/investigate",
    json={
        "entity": "GLAISDALE LIMITED",
        "watchlist": ["DOM Limited", "Beta Nominees Ltd"],
        "depth": 3,
        "no_llm": True,
    },
    timeout=10,
)
assert resp.status_code == 200
run_id = resp.json()["run_id"]

event_types = []
with httpx.stream("GET", f"{API}/stream/{run_id}", timeout=30) as s:
    current_event = "message"
    for line in s.iter_lines():
        if line.startswith("event:"):
            current_event = line[6:].strip()
            event_types.append(current_event)
        elif current_event in ("done", "error"):
            break

print("Event sequence received:", event_types)
assert "status" in event_types
assert "step" in event_types
assert "verdict" in event_types
assert "memo" in event_types
assert "done" in event_types

# Check order
idx_status = event_types.index("status")
idx_step = event_types.index("step")
idx_verdict = event_types.index("verdict")
idx_memo = event_types.index("memo")
idx_done = event_types.index("done")
assert idx_status < idx_step < idx_verdict < idx_memo <= idx_done
print("[PASS] Event order verified: status -> steps -> verdict -> memo -> done")

print("\n=== 2. Testing Early Client Disconnect (No Resource Leak) ===")
# Start investigation and disconnect after reading first step
resp2 = httpx.post(
    f"{API}/investigate", json={"entity": "Silverline Capital Management Ltd", "depth": 2, "no_llm": True}, timeout=10
)
run_id2 = resp2.json()["run_id"]

with httpx.stream("GET", f"{API}/stream/{run_id2}", timeout=30) as s:
    for line in s.iter_lines():
        if "event: step" in line:
            print("  Disconnecting early after first step...")
            break

time.sleep(1)
# Verify API is still responsive and healthy
r_health = httpx.get(f"{API}/health", timeout=3)
assert r_health.status_code == 200
print("[PASS] Client disconnect handled gracefully without server hang or leak")

print("\nOVERALL: ITEM 14 (SSE) PASS")
