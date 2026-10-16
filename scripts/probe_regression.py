"""Probe actual verdicts for all regression entities."""
from agent.fallback import run_deterministic_investigation

watchlist = ["Ironclad Sanctions Entity Inc", "Apex Nominees Ltd"]
tests = [
    ("Blue Star Maritime Holdings Ltd", 1),
    ("Blue Star Maritime Holdings Ltd", 3),
    ("Silverline Capital Management Ltd", 2),
    ("Orion Global Logistics Corp", 2),
    ("Solitary Enterprises Ltd", 2),
    ("Vance Shell Entity 001 Ltd", 2),
    ("St James Resident 001 Corp", 2),
    ("Apex Nominees Ltd", 2),
    ("Ironclad Sanctions Entity Inc", 2),
    ("Unknown Entity Alpha", 2),
    ("Unknown Entity Beta", 2),
]
for name, depth in tests:
    r = run_deterministic_investigation(name, watchlist=watchlist, depth=depth)
    rules = r.get("rules_fired", [])
    print(f"d={depth} | {r['verdict']:25s} | rules={rules} | {name}")
