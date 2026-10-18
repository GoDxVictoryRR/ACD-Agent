"""End-to-end demo case verification."""

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ["NO_LLM"] = "1"

from agent.fallback import run_deterministic_investigation  # noqa: E402
from core.config import DATA_SOURCE  # noqa: E402

if DATA_SOURCE == "icij":
    demo_path = Path("data/demo.json")
    with open(demo_path, encoding="utf-8") as f:
        demo_data = json.load(f)
    watchlist = demo_data.get("watchlist", ["TIANSHENG INDUSTRY AND TRADING CO., LTD."])
    cases = [
        ("MOSSACK FONSECA & CO. (SAMOA) LIMITED.", 1, "clear"),
        ("MOSSACK FONSECA & CO. (SAMOA) LIMITED.", 3, "escalate"),
        ("Millex International Limited", 2, "review"),
        ("OMNIA TECHNOLOGIES S.A.", 2, "clear"),
        ("Dewburn Enterprises Inc.", 2, "insufficient_evidence"),
    ]
else:
    watchlist = ["Ironclad Watchlist Entity Inc", "Apex Nominees Ltd"]
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
    rule_findings = r["evaluation"].get("findings", [])
    rules_str = [f.rule_id if hasattr(f, "rule_id") else f.get("rule_id") for f in rule_findings]
    print(f"[{status_str}] d={depth} got={r['verdict']!r:25s} exp={expected!r:25s} rules={rules_str} | {name}")

print()
print("ALL PASS" if all_pass else "FAILURES FOUND")
