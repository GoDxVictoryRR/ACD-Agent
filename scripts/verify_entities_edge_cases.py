"""Verify unknown, ambiguous, and isolated entities handling."""
from agent.fallback import run_deterministic_investigation
from core import tools

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

# 3. Isolated / clean entity
res_clean = run_deterministic_investigation("Solitary Enterprises Ltd", depth=2)
assert res_clean["verdict"] == "clear", f"Expected clear, got {res_clean['verdict']}"
assert len(res_clean["evaluation"]["findings"]) == 0
print(f"[PASS] Isolated/clean entity -> verdict={res_clean['verdict']}, 0 findings")

print("\nOVERALL: ALL ENTITY EDGE CASES PASS")
