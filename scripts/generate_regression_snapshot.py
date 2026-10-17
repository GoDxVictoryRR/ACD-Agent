import json

from agent.fallback import run_deterministic_investigation

with open("tests/regression/expected_icij.json") as f:
    orig = json.load(f)

watchlist = ["TIANSHENG INDUSTRY AND TRADING CO., LTD."]
live_verdicts = {}

for name in orig:
    if name == "MOSSACK FONSECA & CO. (SAMOA) LIMITED.":
        d1 = run_deterministic_investigation(name, watchlist=watchlist, depth=1)
        d3 = run_deterministic_investigation(name, watchlist=watchlist, depth=3)
        live_verdicts[name] = {"depth_1": d1["verdict"], "depth_3": d3["verdict"]}
        print(f"{name}: depth_1={d1['verdict']}, depth_3={d3['verdict']}")
    else:
        d2 = run_deterministic_investigation(name, watchlist=watchlist, depth=2)
        live_verdicts[name] = {"depth_2": d2["verdict"]}
        print(f"{name}: depth_2={d2['verdict']}")

print("\nFull live verdicts JSON:")
print(json.dumps(live_verdicts, indent=2))

# Write snapshot from real run per Rule 2: 'Snapshots (expected json, demo.json, replay files) come from real runs, never manual edits.'
with open("tests/regression/expected_icij.json", "w", encoding="utf-8") as f:
    json.dump(live_verdicts, f, indent=2)
print("Updated tests/regression/expected_icij.json from live run.")
