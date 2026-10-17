"""Verify unknown, ambiguous, isolated/clean, and zero-link entity handling.

Test cases:
1. Unknown entity -> insufficient_evidence (resolve fails)
2. Ambiguous entity search -> multiple candidates returned
3. Clean entity (has links but no suspicious findings) -> clear
4. Zero-link entity (resolved but no ownership paths or hubs) -> insufficient_evidence
"""
from __future__ import annotations

from agent.fallback import run_deterministic_investigation
from core import tools
from core.rules import evaluate

# 1. Unknown entity
res_unk = run_deterministic_investigation("Nonexistent Phantom Corporation 9999")
assert res_unk["verdict"] == "insufficient_evidence", f"Expected insufficient_evidence, got {res_unk['verdict']}"
assert res_unk["resolved_id"] is None
print("[PASS] Unknown entity -> verdict=insufficient_evidence, resolved_id=None")

# 2. Ambiguous entity search
# Search query that returns multiple candidates
resolve_res = tools.resolve_entity("Holdings", limit=5)
print(f"Resolve 'Holdings': status={resolve_res.status}, candidates={len(resolve_res.data)}")
assert len(resolve_res.data) > 1, "Expected multiple candidates for 'Holdings'"
print(f"[PASS] Ambiguous entity search -> returned {len(resolve_res.data)} candidates for user selection")

# 3. Isolated / clean entity (has a link but no suspicious findings)
res_clean = run_deterministic_investigation("Solitary Enterprises Ltd", depth=2)
assert res_clean["verdict"] == "clear", f"Expected clear, got {res_clean['verdict']}"
assert len(res_clean["evaluation"]["findings"]) == 0
print(f"[PASS] Isolated/clean entity -> verdict={res_clean['verdict']}, 0 findings")

# 4. Zero-link entity: rules.evaluate with no ownership_chain or shared_links returns insufficient_evidence
# This tests the MIN_LINKS guard in core/rules.py (Invariant: empty traversal is never 'safe')
evidence_zero = {
    "resolved_entity": {"id": "fake_id", "name": "Fake Zero-Link Entity"},
    "ownership_chain": [],
    "shared_links": [],
    "paths_to_watchlist": [],
    "cluster_view": {},
}
zero_result = evaluate(evidence_zero)
assert zero_result.verdict == "insufficient_evidence", (
    f"Zero-link entity must yield insufficient_evidence, got {zero_result.verdict}"
)
assert zero_result.total_links == 0
print(
    f"[PASS] Zero-link entity (rules.evaluate) -> verdict={zero_result.verdict}, "
    f"total_links={zero_result.total_links} (MIN_LINKS guard confirmed)"
)

print("\nOVERALL: ALL ENTITY EDGE CASES PASS")
