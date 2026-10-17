"""Verify cross-surface consistency: CLI vs API for demo entities at depth 1 and 3."""
import json

import httpx

from agent.loop import run_investigation

API_BASE = "http://localhost:8000"

with open("data/demo.json", encoding="utf-8") as f:
    demo = json.load(f)

entities = demo["demo_entities"]
watchlist = demo["watchlist"]

all_consistent = True

for ent in entities:
    name = ent["name"]
    for depth in (1, 3):
        # 1. CLI run
        cli_res = run_investigation(name, watchlist=watchlist, depth=depth, force_fallback=True)
        cli_verdict = cli_res.get("verdict")
        cli_findings = sorted([f["rule_id"] for f in cli_res.get("evaluation", {}).get("findings", [])])

        # 2. API run
        resp = httpx.post(f"{API_BASE}/investigate", json={
            "entity": name,
            "watchlist": watchlist,
            "depth": depth,
            "no_llm": True
        }, timeout=30)
        if resp.status_code != 200:
            print(f"API Error {resp.status_code}: {resp.text}")
            all_consistent = False
            continue
        run_id = resp.json()["run_id"]

        # Read API stream to get result
        api_verdict = None
        api_findings = None
        with httpx.stream("GET", f"{API_BASE}/stream/{run_id}", timeout=60) as r:
            current_event = "message"
            for line in r.iter_lines():
                if line.startswith("event:"):
                    current_event = line[6:].strip()
                elif line.startswith("data:"):
                    raw = line[5:].strip()
                    if current_event == "verdict":
                        data = json.loads(raw)
                        api_verdict = data.get("verdict")
                        api_findings = sorted([f["rule_id"] for f in data.get("evaluation", {}).get("findings", [])])
                    elif current_event in ("done", "error"):
                        break

        match = (cli_verdict == api_verdict) and (cli_findings == api_findings)
        status = "PASS" if match else "FAIL"
        if not match:
            all_consistent = False
        print(f"[{status}] {name} (d={depth}): CLI({cli_verdict}, {cli_findings}) == API({api_verdict}, {api_findings})")

if all_consistent:
    print("\nOVERALL: CROSS-SURFACE CONSISTENCY VERIFIED (CLI == API)")
else:
    print("\nOVERALL: INCONSISTENCY DETECTED")
    exit(1)
