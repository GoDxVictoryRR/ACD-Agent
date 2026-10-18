"""Probe actual verdicts for all regression entities."""

from agent.fallback import run_deterministic_investigation

watchlist = ["DOM Limited", "Beta Nominees Ltd"]
tests = [
    ("GLAISDALE LIMITED", 1),
    ("GLAISDALE LIMITED", 3),
    ("Silverline Capital Management Ltd", 2),
    ("Orion Global Logistics Corp", 2),
    ("Solitary Enterprises Ltd", 2),
    ("Vance Shell Entity 001 Ltd", 2),
    ("St James Resident 001 Corp", 2),
    ("Beta Nominees Ltd", 2),
    ("DOM Limited", 2),
    ("Unknown Entity Alpha", 2),
    ("Unknown Entity Beta", 2),
]
for name, depth in tests:
    r = run_deterministic_investigation(name, watchlist=watchlist, depth=depth)
    rules = r.get("rules_fired", [])
    print(f"d={depth} | {r['verdict']:25s} | rules={rules} | {name}")
