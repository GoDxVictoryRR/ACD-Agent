"""Test the full investigate + SSE stream flow."""

import json

import httpx

API = "http://localhost:8000"

# 1. POST /investigate
print("=== POST /investigate ===")
resp = httpx.post(
    f"{API}/investigate",
    json={
        "entity": "GLAISDALE LIMITED",
        "watchlist": ["DOM Limited", "Beta Nominees Ltd"],
        "depth": 3,
        "no_llm": True,
    },
    timeout=30,
)
data = resp.json()
run_id = data["run_id"]
print(f"run_id: {run_id}")
print(f"Status: {resp.status_code}")

# 2. GET /stream/{run_id} — SSE
print(f"\n=== GET /stream/{run_id} ===")
events = []
current_event = "message"

with httpx.stream("GET", f"{API}/stream/{run_id}", timeout=60) as r:
    for line in r.iter_lines():
        if line.startswith("event:"):
            current_event = line[6:].strip()
        elif line.startswith("data:"):
            raw = line[5:].strip()
            if raw == "[DONE]":
                break
            try:
                payload = json.loads(raw)
            except Exception:
                payload = raw

            ev_record = {"event": current_event, "data": payload}
            events.append(ev_record)
            print(f"  [{current_event}] {str(payload)[:80]}")

            if current_event in ("done", "error"):
                break
            current_event = "message"

print(f"\nTotal events: {len(events)}")
types = [e["event"] for e in events]
print(f"Event types received: {set(types)}")

# 3. Verdict check
verdict_events = [e for e in events if e["event"] == "verdict"]
if verdict_events:
    v = verdict_events[0]["data"].get("verdict")
    print(f"\nFinal verdict: {v!r}")
    if v in ("escalate", "review", "clear", "insufficient_evidence"):
        print("PASS: SSE stream returned valid verdict")
    else:
        print(f"FAIL: unexpected verdict {v!r}")
else:
    print("FAIL: no verdict event in stream")
