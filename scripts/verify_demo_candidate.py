"""
scripts/verify_demo_candidate.py — Test primary candidate 10000297 -> 10000230 on live FalkorDB graph.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.fallback import run_deterministic_investigation
from core.tools import path_between, resolve_entity

a_id = "10000297"
b_id = "10000230"
a_name = "DUNSTONE INCORPORATED"
b_name = "BLUE CREST CORPORATION"
watchlist = [b_name]

print(f"=== Testing Candidate: {a_name} ({a_id}) -> Watchlist: {b_name} ({b_id}) ===")

# Test resolve_entity
res_a = resolve_entity(a_id)
print("Resolve A:", res_a.status, res_a.data)

res_b = resolve_entity(b_name)
print("Resolve B:", res_b.status, res_b.data)

# Test SPpaths between A and B
sp_res = path_between(a_id, b_id, max_depth=4)
print("\npath_between result:")
print(f"Status: {sp_res.status}")
print(f"Data: {sp_res.data}")
print(f"Notes: {sp_res.notes}")

# Test investigations at depth 1, 2, 3
print("\n--- Running Investigations ---")
inv_d1 = run_deterministic_investigation(a_name, watchlist=watchlist, depth=1)
print(f"Depth 1: Verdict = {inv_d1['verdict']}, Findings = {len(inv_d1['evaluation']['findings'])}")

inv_d2 = run_deterministic_investigation(a_name, watchlist=watchlist, depth=2)
print(f"Depth 2: Verdict = {inv_d2['verdict']}, Findings = {len(inv_d2['evaluation']['findings'])}")

inv_d3 = run_deterministic_investigation(a_name, watchlist=watchlist, depth=3)
print(f"Depth 3: Verdict = {inv_d3['verdict']}, Findings = {len(inv_d3['evaluation']['findings'])}")
for f in inv_d3["evaluation"]["findings"]:
    print(f"   [{f['rule_id']}] {f['text']}")
