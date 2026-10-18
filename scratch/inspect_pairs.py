import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent.fallback import run_deterministic_investigation

pairs = [
    ('Skye Window Systems Ltd.', 'Related Supply Ltd.'),
    ('Skye Holdings Ltd.', 'Related Supply Ltd.'),
    ('Related Wall Systems Ltd.', 'Related Supply Ltd.'),
    ('Related Supply Ltd.', 'Skye Holdings Ltd.'),
]

for e1, e3 in pairs:
    r1 = run_deterministic_investigation(e1, watchlist=[e3], depth=1)
    r2 = run_deterministic_investigation(e1, watchlist=[e3], depth=2)
    f1 = [f['rule_id'] for f in r1['evaluation']['findings']]
    f2 = [f['rule_id'] for f in r2['evaluation']['findings']]
    print(f"{e1} -> {e3}: d1={r1['verdict']} {f1} | d2={r2['verdict']} {f2}")
