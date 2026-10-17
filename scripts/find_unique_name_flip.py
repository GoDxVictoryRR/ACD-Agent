"""
scripts/find_unique_name_flip.py — Find entity pairs with unique names showing d1/d2 clear -> d3 escalate.
"""

import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.fallback import run_deterministic_investigation
from core.db import ro
from core.tools import path_between

# Load entity names and check uniqueness
print("Loading all entities from graph...")
res_all = ro("ownership", "MATCH (e:Entity) RETURN e.node_id, e.name")
name_counts = defaultdict(int)
id_to_name = {}
for r in res_all.get("rows", []):
    nid, name = r[0], r[1]
    name_counts[name.strip().lower()] += 1
    id_to_name[nid] = name

unique_entities = {nid: name for nid, name in id_to_name.items() if name_counts[name.strip().lower()] == 1}
print(f"Total entities: {len(id_to_name):,}, Unique-name entities: {len(unique_entities):,}")

# Query candidates with degree between 1 and 3
q_cands = """
MATCH (e:Entity)
WHERE size([(e)-[r]-() WHERE NOT endNode(r):Case AND NOT startNode(r):Case | r]) >= 1
  AND size([(e)-[r]-() WHERE NOT endNode(r):Case AND NOT startNode(r):Case | r]) <= 3
RETURN e.node_id, e.name
LIMIT 200
"""
res_cands = ro("ownership", q_cands)
cand_rows = [r for r in res_cands.get("rows", []) if r[0] in unique_entities]
print(f"Unique candidates with 1-3 links: {len(cand_rows)}")

perfect_flips = []
for a_id, a_name in cand_rows:
    # Fetch 3-hop neighborhood
    q_nbrs = """
    MATCH path = (e:Entity {node_id: $aid})-[:OFFICER_OF|SHAREHOLDER_OF|INTERMEDIARY_OF|REGISTERED_ADDRESS|CONNECTED_TO|BENEFICIARY_OF|DIRECTOR_OF|UNDERLYING|SAME_NAME_AS|SAME_ADDRESS_AS|RELATED_ENTITY|ADDRESS_OF|SAME_AS|SAME_COMPANY_AS|SIMILAR*3..3]-(target:Entity)
    WHERE NOT target:Case AND target.node_id <> $aid
    RETURN target.node_id, target.name, [r in relationships(path) | r.weight] AS weights
    LIMIT 10
    """
    res_nbrs = ro("ownership", q_nbrs, {"aid": a_id})
    for b_id, b_name, w_list in res_nbrs.get("rows", []):
        if b_id in unique_entities and b_id != a_id:
            # Check SPpaths
            sp = path_between(a_id, b_id, max_depth=4)
            if sp.status == "ok" and sp.data:
                cost = sp.data[0].get("path_weight", 999)
                nodes = sp.data[0].get("nodes", [])
                hops = len(nodes) - 1
                if hops == 3 and cost <= 8.0:
                    # Test investigation
                    inv1 = run_deterministic_investigation(a_name, watchlist=[b_name], depth=1)
                    inv2 = run_deterministic_investigation(a_name, watchlist=[b_name], depth=2)
                    inv3 = run_deterministic_investigation(a_name, watchlist=[b_name], depth=3)
                    if inv1["verdict"] == "clear" and inv2["verdict"] == "clear" and inv3["verdict"] == "escalate":
                        print("PERFECT FLIP FOUND!")
                        print(f"  Source: {a_name} ({a_id})")
                        print(f"  Watchlist Target: {b_name} ({b_id})")
                        print(f"  Shortest Path: {sp.data[0].get('path_text')}")
                        print(f"  Path Cost: {cost}")
                        print(f"  d1={inv1['verdict']} | d2={inv2['verdict']} | d3={inv3['verdict']}")
                        perfect_flips.append(
                            {
                                "source_id": a_id,
                                "source_name": a_name,
                                "target_id": b_id,
                                "target_name": b_name,
                                "path_text": sp.data[0].get("path_text"),
                                "cost": cost,
                            }
                        )
                        if len(perfect_flips) >= 5:
                            break
    if len(perfect_flips) >= 5:
        break

print(f"\nTotal perfect flips found: {len(perfect_flips)}")
