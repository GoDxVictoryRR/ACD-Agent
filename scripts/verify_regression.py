"""Verify all regression expected.json cases."""

import json
import sys

sys.path.insert(0, r"C:\Users\hardi\Downloads\ACD-agent")

from agent.fallback import run_deterministic_investigation

watchlist = ["Ironclad Sanctions Entity Inc", "Apex Nominees Ltd"]

with open(r"C:\Users\hardi\Downloads\ACD-agent\tests\regression\expected.json") as f:
    expected = json.load(f)

all_pass = True
print("=== Regression Expected.json Verification ===")
for entity, depths in expected.items():
    for depth_key, exp_verdict in depths.items():
        depth = int(depth_key.split("_")[1])
        r = run_deterministic_investigation(entity, watchlist=watchlist, depth=depth)
        got = r["verdict"]
        ok = got == exp_verdict
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        print(f"  {status} | d={depth} | exp={exp_verdict!r:25s} | got={got!r:25s} | {entity}")

print()
print("OVERALL:", "ALL PASS" if all_pass else "FAILURES FOUND")
