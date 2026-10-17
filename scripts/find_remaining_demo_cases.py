import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.fallback import run_deterministic_investigation
from core.db import ro
from core.tools import recall_cases, record_decision

watchlist = ["TIANSHENG INDUSTRY AND TRADING CO., LTD."]

# 1. Primary entity
primary_src = "MOSSACK FONSECA & CO. (SAMOA) LIMITED."
primary_id = "10001171"
primary_tgt = "TIANSHENG INDUSTRY AND TRADING CO., LTD."
primary_tgt_id = "10000001"

print("=== 1. Primary Case ===")
inv1 = run_deterministic_investigation(primary_src, watchlist=watchlist, depth=1)
inv2 = run_deterministic_investigation(primary_src, watchlist=watchlist, depth=2)
inv3 = run_deterministic_investigation(primary_src, watchlist=watchlist, depth=3)
print(f"Primary {primary_src}: d1={inv1['verdict']}, d2={inv2['verdict']}, d3={inv3['verdict']}")

# 2. Find an isolated / low-link entity (0 links -> insufficient_evidence, or 1 link -> clear)
print("\n=== 2. Finding Isolated / Low-link Entity ===")
q_iso = """
MATCH (e:Entity)
WHERE NOT e:Case
OPTIONAL MATCH (e)-[r]-()
WITH e, count(r) AS deg
WHERE deg = 0 OR deg = 1
RETURN e.node_id, e.name, deg
LIMIT 10
"""
res_iso = ro("ownership", q_iso)
isolated_candidates = []
for nid, name, deg in res_iso.get("rows", []):
    # Verify uniqueness
    q_u = "MATCH (e:Entity) WHERE toLower(e.name) = toLower($name) RETURN count(e)"
    if ro("ownership", q_u, {"name": name})["rows"][0][0] != 1:
        continue
    inv = run_deterministic_investigation(name, watchlist=watchlist, depth=2)
    isolated_candidates.append((nid, name, deg, inv["verdict"]))
    print(f"Isolated candidate: {name} ({nid}), deg={deg}, verdict={inv['verdict']}")

# 3. Find Related Entity for Case Recall
print("\n=== 3. Finding Related Entity for Case Recall ===")
# Primary entity 10001171 is connected to intermediary or officer or address
q_related = """
MATCH (src:Entity {node_id: $src_id})-[r1]-(shared)-[r2]-(rel:Entity)
WHERE rel.node_id <> $src_id AND NOT rel:Case
RETURN rel.node_id, rel.name, labels(shared)[0], coalesce(shared.name, shared.address)
LIMIT 10
"""
res_rel = ro("ownership", q_related, {"src_id": primary_id})
related_case = None
for rel_id, rel_name, s_label, s_name in res_rel.get("rows", []):
    q_u = "MATCH (e:Entity) WHERE toLower(e.name) = toLower($name) RETURN count(e)"
    if ro("ownership", q_u, {"name": rel_name})["rows"][0][0] != 1:
        continue

    # Record decision on primary entity with shared node as evidence_id
    shared_res = ro(
        "ownership", "MATCH (src:Entity {node_id: $src_id})-[r1]-(s) RETURN s.node_id LIMIT 1", {"src_id": primary_id}
    )
    evidence_id = shared_res["rows"][0][0]
    rec = record_decision(
        entity_id=primary_id,
        verdict="escalate",
        depth=3,
        evidence_ids=[primary_id, evidence_id],
        rule_ids=["WATCHLIST_PATH"],
        memo=f"Test case for {primary_src}",
    )
    # Check recall from rel_id
    rec_res = recall_cases(entity_id=rel_id)
    if rec_res.status == "ok" and len(rec_res.data) > 0:
        related_case = (rel_id, rel_name, s_label, s_name, rec_res.data[0])
        print(f"Found related entity for recall: {rel_name} ({rel_id})")
        print(f"  Shared {s_label}: {s_name}")
        print(f"  Recalled Case: {rec_res.data[0]}")
        break

# 4. Find >= 4 Negative Controls (Real structures that look similar but must not escalate)
print("\n=== 4. Finding >= 4 Negative Controls ===")
# Entities with degree >= 2 that do NOT connect to watchlist, verdicts clear or review
q_neg = """
MATCH (e:Entity)-[r]-(nbr)
WHERE NOT e:Case
WITH e, count(r) AS deg
WHERE deg >= 2 AND deg <= 5
RETURN e.node_id, e.name, deg
LIMIT 50
"""
res_neg = ro("ownership", q_neg)
neg_controls = []
for nid, name, deg in res_neg.get("rows", []):
    if name in [primary_src, primary_tgt]:
        continue
    q_u = "MATCH (e:Entity) WHERE toLower(e.name) = toLower($name) RETURN count(e)"
    if ro("ownership", q_u, {"name": name})["rows"][0][0] != 1:
        continue
    inv1 = run_deterministic_investigation(name, watchlist=watchlist, depth=1)
    inv3 = run_deterministic_investigation(name, watchlist=watchlist, depth=3)
    if inv3["verdict"] in ["clear", "review"] and inv1["verdict"] in ["clear", "review"]:
        neg_controls.append(
            {
                "id": nid,
                "name": name,
                "deg": deg,
                "d1": inv1["verdict"],
                "d3": inv3["verdict"],
                "rules": inv3["rules_fired"],
            }
        )
        print(
            f"Negative control: {name} ({nid}), deg={deg}, d1={inv1['verdict']}, d3={inv3['verdict']}, rules={inv3['rules_fired']}"
        )
        if len(neg_controls) >= 6:
            break

print(f"\nTotal negative controls found: {len(neg_controls)}")
