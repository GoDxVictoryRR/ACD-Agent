"""Verify depth contrast for demo cases after graph reload."""

import sys

sys.path.insert(0, r"C:\Users\hardi\Downloads\ACD-agent")

from agent.fallback import run_deterministic_investigation

watchlist = ["Ironclad Sanctions Entity Inc", "Apex Nominees Ltd"]
cases = [
    ("Blue Star Maritime Holdings Ltd", 1, None),
    ("Blue Star Maritime Holdings Ltd", 2, None),
    ("Blue Star Maritime Holdings Ltd", 3, None),
    ("Blue Star Maritime Holdings Ltd", 4, None),
    ("Silverline Capital Management Ltd", 2, None),
    ("Orion Global Logistics Corp", 2, None),
    ("Solitary Enterprises Ltd", 2, None),
    ("Unknown Entity XYZ999", 2, None),
]

print("=== Demo Case Depth Verification ===")
print()
for name, depth, _ in cases:
    r = run_deterministic_investigation(name, watchlist=watchlist, depth=depth)
    print(f"d={depth} | {r['verdict']:25s} | rules={r.get('rules_fired', [])} | {name}")
    # Print path text if available
    if r.get("evidence", {}).get("paths_to_watchlist"):
        for p in r["evidence"]["paths_to_watchlist"][:1]:
            pt = p.get("path_text", "")
            print(f"       path: {pt[:100]}")
print()

# Verify depth flip: should be clear at d=1 and d=2, escalate at d=3
r1 = run_deterministic_investigation("Blue Star Maritime Holdings Ltd", watchlist=watchlist, depth=1)
r3 = run_deterministic_investigation("Blue Star Maritime Holdings Ltd", watchlist=watchlist, depth=3)
flip_ok = r1["verdict"] != r3["verdict"] and r1["verdict"] == "clear" and r3["verdict"] == "escalate"
print(f"Depth flip test: d=1={r1['verdict']!r} d=3={r3['verdict']!r} -> {'PASS' if flip_ok else 'FAIL'}")
