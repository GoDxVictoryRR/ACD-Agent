import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.fallback import run_deterministic_investigation

watchlist = ["TIANSHENG INDUSTRY AND TRADING CO., LTD."]
entities = [
    ("MOSSACK FONSECA & CO. (SAMOA) LIMITED.", 1, 3),
    ("Millex International Limited", 2, None),
    ("Skytrack Investments Limited", 2, None),
    ("OMNIA TECHNOLOGIES S.A.", 2, None),
    ("GAO SHENG LIMITED", 2, None),
    ("KIRBY GARDENS LTD.", 2, None),
    ("Dewburn Enterprises Inc.", 2, None),
    ("TIANSHENG INDUSTRY AND TRADING CO., LTD.", 2, None),
    ("Unknown Entity Alpha", 2, None),
    ("Unknown Entity Beta", 2, None),
]

results = {}
for name, d1, d3 in entities:
    if d3 is not None:
        r1 = run_deterministic_investigation(name, watchlist=watchlist, depth=d1)
        r3 = run_deterministic_investigation(name, watchlist=watchlist, depth=d3)
        results[name] = {"depth_1": r1["verdict"], "depth_3": r3["verdict"]}
        print(f"{name}: d1={r1['verdict']}, d3={r3['verdict']}")
    else:
        r = run_deterministic_investigation(name, watchlist=watchlist, depth=d1)
        results[name] = {"depth_2": r["verdict"]}
        print(f"{name}: d2={r['verdict']}")

out_file = REPO_ROOT / "tests" / "regression" / "expected_icij.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"\nSaved real ICIJ regression snapshot to {out_file}:")
print(json.dumps(results, indent=2))
