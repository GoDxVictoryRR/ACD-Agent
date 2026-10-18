import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent.fallback import run_deterministic_investigation
from core.config import GRAPH_NAME
from core.db import ro
from core.tools import path_between, resolve_entity

print("=== Primary Demo Candidate Verification ===")
e1 = resolve_entity("GLAISDALE LIMITED").data[0]
e2 = resolve_entity("DOM Limited").data[0]
print(f"Target: {e1['name']} (node_id: {e1['node_id']}, jurisdiction: {e1.get('jurisdiction')}, status: {e1.get('status')})")
print(f"Watchlist: {e2['name']} (node_id: {e2['node_id']}, jurisdiction: {e2.get('jurisdiction')}, status: {e2.get('status')})")

pb = path_between(e1['node_id'], e2['node_id'], max_depth=4, is_watchlist=True)
print("\nPath Between Result:")
print("Status:", pb.status)
if pb.data:
    path = pb.data[0]
    print("Path Weight:", path.get("path_weight"))
    print("Path Text:", path.get("path_text"))
    print("Disjoint paths count:", path.get("disjoint_paths_count"))
    print("Exposure depends on:", path.get("exposure_depends_on"))
    print("Nodes on path:")
    for n in path.get("nodes", []):
        nid = n.get("id")
        deg = ro(GRAPH_NAME, f"MATCH (n {{node_id: '{nid}'}})-[r]-() RETURN count(r)").get("rows", [[0]])[0][0]
        print(f"  * [{n.get('label')}] {n.get('name')} (id: {nid}, degree: {deg})")
    print("Relationships on path:")
    for r in path.get("relationships", []):
        print(f"  * -[{r.get('type')}]-> weight: {r.get('weight')}")

print("\nDepth Step-by-Step Investigation (Depths 1 to 4):")
for d in [1, 2, 3, 4]:
    res = run_deterministic_investigation(e1['name'], watchlist=[e2['name']], depth=d)
    print(f"\n--- DEPTH {d} ---")
    print("Verdict:", res["verdict"])
    print("Total Links:", res["evaluation"]["total_links"])
    print("Rule Findings:", len(res["evaluation"]["findings"]))
    for f in res["evaluation"]["findings"]:
        print(f"  - [{f['rule_id']}] {f['text']}")
    print("Memo:")
    print(res["memo"].strip())
