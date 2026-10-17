import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.fallback import run_deterministic_investigation
from core.db import ro
from core.tools import ownership_chain, path_between

clean_candidates = [
    ("10000005", "FORTUNEMAKER INVESTMENTS CORPORATION"),
    ("10000029", "NECY CONSULTANTS LIMITED"),
    ("10000043", "DAFORD INTERNATIONAL CORP."),
    ("10000062", "CADELL INVESTMENTS LIMITED"),
    ("10000065", "ADVANTAGE DUTY-FREE INC."),
    ("10000089", "SYREN LIMITED"),
    ("10000099", "MOROCCAN PROPERTIES LTD."),
    ("10000100", "CORPORATE CONSULTING SERVICES LTD."),
    ("10000097", "DYNASTY HOLDINGS LTD."),
    ("10000107", "FortuneHubs Limited"),
]

for src_id, src_name in clean_candidates:
    oc = ownership_chain(src_id, max_depth=3)
    if oc.status != "ok" or not oc.data:
        continue
    # Find paths of length 3 where end node is Entity
    hop3_entities = []
    for p in oc.data:
        nodes = p.get("nodes", [])
        if len(nodes) - 1 == 3 and nodes[-1].get("label") == "Entity":
            hop3_entities.append(nodes[-1])

    print(f"{src_name} ({src_id}) has {len(hop3_entities)} 3-hop entity endpoints.")
    for tgt in hop3_entities[:5]:
        tgt_id = tgt["id"]
        tgt_name = tgt["name"]
        # Check uniqueness
        q_u = "MATCH (e:Entity) WHERE toLower(e.name) = toLower($name) RETURN count(e)"
        if ro("ownership", q_u, {"name": tgt_name})["rows"][0][0] != 1:
            continue
        sp = path_between(src_id, tgt_id, max_depth=4)
        if sp.status != "ok" or not sp.data:
            continue
        p = sp.data[0]
        cost = p.get("path_weight", 999.0)
        hops = len(p.get("nodes", [])) - 1
        print(f"  -> {tgt_name} ({tgt_id}): hops={hops}, cost={cost}")
        if hops == 3 and cost <= 8.0:
            inv1 = run_deterministic_investigation(src_name, watchlist=[tgt_name], depth=1)
            inv2 = run_deterministic_investigation(src_name, watchlist=[tgt_name], depth=2)
            inv3 = run_deterministic_investigation(src_name, watchlist=[tgt_name], depth=3)
            print(
                f"     Verdicts: d1={inv1['verdict']} (f={len(inv1['evaluation']['findings'])}), d2={inv2['verdict']} (f={len(inv2['evaluation']['findings'])}), d3={inv3['verdict']} (f={len(inv3['evaluation']['findings'])})"
            )
            if inv1["verdict"] == "clear" and inv2["verdict"] == "clear" and inv3["verdict"] == "escalate":
                print("\n=================== WINNER FOUND! ===================")
                print(f"Source: {src_name} ({src_id})")
                print(f"Target: {tgt_name} ({tgt_id})")
                print(f"Path: {p['path_text']}")
                print(f"Cost: {cost:.1f}")
                print(f"d1: {inv1['verdict']}, d2: {inv2['verdict']}, d3: {inv3['verdict']}")
                print("=====================================================\n")
                sys.exit(0)
