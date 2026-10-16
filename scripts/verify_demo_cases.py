"""End-to-end demo case verification."""
import os

os.environ["NO_LLM"] = "1"

from agent.fallback import run_deterministic_investigation  # noqa: E402

watchlist = ["Ironclad Sanctions Entity Inc", "Apex Nominees Ltd"]
cases = [
    ("Blue Star Maritime Holdings Ltd", 1, "clear"),
    ("Blue Star Maritime Holdings Ltd", 3, "escalate"),
    ("Silverline Capital Management Ltd", 2, "review"),
    ("Orion Global Logistics Corp", 2, "review"),
    ("Solitary Enterprises Ltd", 2, "clear"),
]

all_pass = True
for name, depth, expected in cases:
    r = run_deterministic_investigation(name, watchlist=watchlist, depth=depth)
    ok = r["verdict"] == expected
    all_pass = all_pass and ok
    status_str = "PASS" if ok else "FAIL"
    print(f"[{status_str}] d={depth} got={r['verdict']!r:25s} exp={expected!r:25s} rules={r['rules_fired']} | {name}")

print()
print("ALL PASS" if all_pass else "FAILURES FOUND")
