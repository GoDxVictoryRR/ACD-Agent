import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.fallback import run_deterministic_investigation
from core.tools import path_between, resolve_entity

s_name = "MOSSACK FONSECA & CO. (SAMOA) LIMITED."
t_name = "TIANSHENG INDUSTRY AND TRADING CO., LTD."

r1 = resolve_entity(s_name)
r2 = resolve_entity(t_name)
print(f"Resolve '{s_name}': status={r1.status}, data={r1.data}")
print(f"Resolve '{t_name}': status={r2.status}, data={r2.data}")

# Let's check verdicts at depths 1, 2, 3
inv1 = run_deterministic_investigation(s_name, watchlist=[t_name], depth=1)
inv2 = run_deterministic_investigation(s_name, watchlist=[t_name], depth=2)
inv3 = run_deterministic_investigation(s_name, watchlist=[t_name], depth=3)

print(f"d1 verdict: {inv1['verdict']}, rules: {inv1['rules_fired']}")
print(f"d2 verdict: {inv2['verdict']}, rules: {inv2['rules_fired']}")
print(f"d3 verdict: {inv3['verdict']}, rules: {inv3['rules_fired']}")
for f in inv3["evaluation"]["findings"]:
    print(f"  Finding: {f['text']}")

# SPpaths check
sp = path_between("10001171", "10000001", max_depth=4)
print(f"SPpaths: status={sp.status}, weight={sp.data[0]['path_weight']}, hops={len(sp.data[0]['nodes']) - 1}")
print(f"Path text: {sp.data[0]['path_text']}")
