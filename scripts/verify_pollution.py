"""Pollution test: verify Case nodes and ABOUT/CITED edges do not pollute traversals."""
import json

from agent.fallback import run_deterministic_investigation

with open("data/demo.json", encoding="utf-8") as f:
    demo = json.load(f)

entities = demo["demo_entities"]
watchlist = demo["watchlist"]

print("=== Recording initial state for all demo entities ===")
baseline = {}
for ent in entities:
    name = ent["name"]
    for depth in (1, 3):
        res = run_deterministic_investigation(name, watchlist=watchlist, depth=depth)
        key = (name, depth)
        baseline[key] = {
            "verdict": res["verdict"],
            "findings": [f["rule_id"] for f in res["evaluation"]["findings"]],
            "total_links": res["evaluation"]["total_links"],
        }
        print(f"Baseline {name} (d={depth}): verdict={baseline[key]['verdict']}, links={baseline[key]['total_links']}")

print("\n=== Running 20 investigations to generate Case nodes ===")
for i in range(20):
    ent = entities[i % len(entities)]
    depth = 1 if (i % 2 == 0) else 3
    run_deterministic_investigation(ent["name"], watchlist=watchlist, depth=depth)

print("20 investigations completed.")

print("\n=== Verifying state after Case generation ===")
all_clean = True
for ent in entities:
    name = ent["name"]
    for depth in (1, 3):
        res = run_deterministic_investigation(name, watchlist=watchlist, depth=depth)
        key = (name, depth)
        after = {
            "verdict": res["verdict"],
            "findings": [f["rule_id"] for f in res["evaluation"]["findings"]],
            "total_links": res["evaluation"]["total_links"],
        }
        b = baseline[key]
        match = (after == b)
        status = "PASS" if match else "FAIL"
        if not match:
            all_clean = False
            print(f"[{status}] {name} (d={depth}): baseline={b} vs after={after}")
        else:
            print(f"[{status}] {name} (d={depth}): links={after['total_links']}, verdict={after['verdict']} (unpolluted)")

if all_clean:
    print("\nOVERALL: POLLUTION TEST PASS (Zero Case node pollution)")
else:
    print("\nOVERALL: POLLUTION DETECTED")
    exit(1)
