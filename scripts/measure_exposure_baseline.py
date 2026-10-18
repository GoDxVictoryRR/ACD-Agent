"""
scripts/measure_exposure_baseline.py — Exposure Statistics with Degree-Matched Baseline (Z5).

Definitions:
- Exact-Depth k: Nodes whose shortest hub-aware path from the source is exactly k hops.
- Cumulative Depth k: All distinct nodes reachable within <= k hops from the source (sum of exact-depth 1..k).

Evaluation:
- Target Entity: GLAISDALE LIMITED (node_id: 10024477, degree: 5)
- Real Watchlist Target: DOM Limited (node_id: 10189122, degree: 5)
- Baseline: 30 randomly sampled Entities in the same degree band (degree 4-6), seeded with random.seed(42).
- Metric: Hub-aware path reachability and cost (max_depth=4) excluding service providers, intermediaries, and placeholders.
"""

from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.config import GRAPH_NAME
from core.db import ro
from core.tools import path_between

SOURCE_ID = "10024477"
SOURCE_NAME = "GLAISDALE LIMITED"
REAL_TARGET_ID = "10189122"
REAL_TARGET_NAME = "DOM Limited"


def get_exact_and_cumulative_reachability():
    print("=" * 70)
    print("1. EXACT-DEPTH VS CUMULATIVE REACHABILITY FROM GLAISDALE LIMITED")
    print("=" * 70)

    # Let's count corporate nodes reachable at depth 1, 2, 3, 4
    # Using clean corporate ownership/control edges
    cypher_depths = {}
    for d in range(1, 5):
        q = f"""
        MATCH path = (e:Entity {{node_id: $src}})-[:OFFICER_OF|SHAREHOLDER_OF|DIRECTOR_OF|BENEFICIARY_OF|CONNECTED_TO|RELATED_ENTITY|SAME_AS|SAME_COMPANY_AS*1..{d}]-(nbr)
        WHERE NOT nbr:Case
          AND NOT nbr:Intermediary
          AND NOT nbr:Address
          AND ALL(n in nodes(path) WHERE NOT n:Case AND NOT n:Intermediary AND NOT n:Address)
        RETURN count(distinct nbr)
        """
        cum_count = ro(GRAPH_NAME, q, {"src": SOURCE_ID}).get("rows", [[0]])[0][0]
        cypher_depths[d] = cum_count

    print(f"Origin Entity: {SOURCE_NAME} (ID: {SOURCE_ID})")
    print("\n| Depth (k) | Cumulative Reachable Nodes (<= k) | Exact-Depth Nodes (== k) |")
    print("|---|---|---|")
    prev_cum = 0
    stats = {}
    for d in range(1, 5):
        cum = cypher_depths[d]
        exact = cum - prev_cum
        prev_cum = cum
        stats[d] = {"cumulative": cum, "exact": exact}
        print(f"| Depth {d} | {cum:8d} nodes | {exact:8d} nodes |")

    return stats


def run_random_baseline():
    print("\n" + "=" * 70)
    print("2. WATCHLIST TARGET VS 30 DEGREE-MATCHED RANDOM BASELINE TARGETS")
    print("=" * 70)

    # Find candidate entities in degree band 4 to 6
    deg_q = """
    MATCH (e:Entity)-[r]-()
    WHERE NOT e.name IS NULL AND trim(e.name) <> ''
    WITH e, count(r) AS deg
    WHERE deg >= 4 AND deg <= 6 AND e.node_id <> $src AND e.node_id <> $tgt
    RETURN e.node_id, e.name, deg
    ORDER BY e.node_id
    """
    candidates = ro(GRAPH_NAME, deg_q, {"src": SOURCE_ID, "tgt": REAL_TARGET_ID}).get("rows", [])
    print(f"Total entities in degree band [4, 6] (excluding source and target): {len(candidates)}")

    rng = random.Random(42)
    sample_30 = rng.sample(candidates, 30)

    # 1. Evaluate Real Watchlist Target
    t0 = time.perf_counter()
    real_res = path_between(SOURCE_ID, REAL_TARGET_ID, max_depth=4, is_watchlist=True)
    real_elapsed = (time.perf_counter() - t0) * 1000
    real_reachable = real_res.status == "ok" and bool(real_res.data)
    real_cost = real_res.data[0].get("path_weight") if real_reachable else None
    real_hops = len(real_res.data[0].get("nodes", [])) - 1 if real_reachable else None

    print(f"\nREAL WATCHLIST TARGET: {REAL_TARGET_NAME} (ID: {REAL_TARGET_ID}, degree: 5)")
    print(f"  * Reachable within Depth 4: {real_reachable}")
    print(f"  * Hub-Aware Path Cost: {real_cost}")
    print(f"  * Hops: {real_hops}")
    print(f"  * Query Latency: {real_elapsed:.2f}ms")

    # 2. Evaluate 30 Random Targets
    baseline_results = []
    reachable_count = 0
    costs = []

    print("\nEVALUATING 30 RANDOM DEGREE-MATCHED TARGETS:")
    print("| # | Target Entity Name | ID | Degree | Reachable (<=4) | Cost | Hops | Latency |")
    print("|---|---|---|---|---|---|---|---|")

    for idx, (cand_id, cand_name, cand_deg) in enumerate(sample_30, 1):
        t_i = time.perf_counter()
        res_i = path_between(SOURCE_ID, str(cand_id), max_depth=4, is_watchlist=True)
        lat_i = (time.perf_counter() - t_i) * 1000
        is_reach = res_i.status == "ok" and bool(res_i.data)
        cost_i = res_i.data[0].get("path_weight") if is_reach else None
        hops_i = len(res_i.data[0].get("nodes", [])) - 1 if is_reach else None

        if is_reach:
            reachable_count += 1
            costs.append(cost_i)

        cost_str = f"{cost_i:.1f}" if cost_i is not None else "N/A (inf)"
        hops_str = str(hops_i) if hops_i is not None else "unreachable"
        print(f"| {idx:2d} | {cand_name[:32]:<32} | {cand_id} | {cand_deg} | {str(is_reach):<5} | {cost_str:<8} | {hops_str:<11} | {lat_i:6.1f}ms |")

        baseline_results.append({
            "id": cand_id,
            "name": cand_name,
            "degree": cand_deg,
            "reachable": is_reach,
            "cost": cost_i,
            "hops": hops_i,
            "latency_ms": round(lat_i, 2),
        })

    # Summary Statistics
    reach_pct = (reachable_count / 30.0) * 100.0
    print("\n" + "=" * 70)
    print("3. STATISTICAL COMPARISON & BASELINE FINDINGS")
    print("=" * 70)
    print(f"Real Watchlist Target Reachability: {real_reachable} (Cost: {real_cost}, Hops: {real_hops})")
    print(f"Random Baseline Reachability: {reachable_count}/30 ({reach_pct:.1f}%)")
    if costs:
        avg_cost = sum(costs) / len(costs)
        print(f"Average Path Cost for Reachable Random Targets: {avg_cost:.2f}")
    else:
        print("Random targets reachable: 0/30 (0.0%) — Target is completely isolated from random network nodes!")

    summary = {
        "source": {"id": SOURCE_ID, "name": SOURCE_NAME},
        "real_target": {
            "id": REAL_TARGET_ID,
            "name": REAL_TARGET_NAME,
            "reachable": real_reachable,
            "cost": real_cost,
            "hops": real_hops,
            "latency_ms": round(real_elapsed, 2),
        },
        "baseline_30": {
            "sample_size": 30,
            "degree_band": "4-6",
            "seed": 42,
            "reachable_count": reachable_count,
            "reachability_pct": reach_pct,
            "results": baseline_results,
        }
    }

    out_file = REPO_ROOT / "docs" / "exposure_stats.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved raw exposure baseline stats to {out_file}")
    return summary


if __name__ == "__main__":
    get_exact_and_cumulative_reachability()
    run_random_baseline()
