"""Verify determinism: each demo entity 3 times via deterministic path gives identical verdict and findings."""
import json
from pathlib import Path

from agent.fallback import run_deterministic_investigation

demo_path = Path("data/demo.json")
with open(demo_path, encoding="utf-8") as f:
    demo_data = json.load(f)

entities = demo_data["demo_entities"]
watchlist = demo_data.get("watchlist", [])

all_pass = True

for ent in entities:
    name = ent["name"]
    for depth in (1, 3):
        runs = []
        for i in range(3):
            res = run_deterministic_investigation(name, watchlist=watchlist, depth=depth)
            runs.append({
                "verdict": res.get("verdict"),
                "findings": [f["rule_id"] for f in res.get("evaluation", {}).get("findings", [])]
            })

        # Check equality
        v0 = runs[0]["verdict"]
        f0 = runs[0]["findings"]
        same = all(r["verdict"] == v0 and r["findings"] == f0 for r in runs)
        status = "PASS" if same else "FAIL"
        if not same:
            all_pass = False
        print(f"[{status}] {name} (d={depth}): verdict={v0}, findings={f0} across 3 runs")

if all_pass:
    print("\nOVERALL: ALL RUNS DETERMINISTIC (100% IDENTICAL)")
else:
    print("\nOVERALL: NON-DETERMINISM DETECTED")
    exit(1)
