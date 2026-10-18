"""
scripts/measure_degree_distribution.py — Entity-Only Degree Distribution & Negative Controls (Z6).

Measures:
1. Entity-only degree distribution across the active FalkorDB dataset.
2. Share of entities that return insufficient_evidence under MIN_LINKS=2 (degree 0 and degree 1).
3. Evaluation of >= 4 negative controls against the primary watchlist ('DOM Limited').
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent.fallback import run_deterministic_investigation
from core.config import GRAPH_NAME, MIN_LINKS
from core.db import ro


def measure_distribution():
    print("=" * 70)
    print("1. ENTITY-ONLY DEGREE DISTRIBUTION & MIN_LINKS SHARE")
    print("=" * 70)

    # Query degree for every Entity in the database
    q = """
    MATCH (e:Entity)
    OPTIONAL MATCH (e)-[r]-()
    RETURN e.node_id, count(r) AS deg
    """
    rows = ro(GRAPH_NAME, q).get("rows", [])
    total_entities = len(rows)
    print(f"Total Entities in Dataset: {total_entities}")

    degrees = [r[1] for r in rows]
    counts = Counter(degrees)

    print("\n| Degree | Entity Count | Percentage of All Entities |")
    print("|---|---|---|")
    for d in range(1, 11):
        c = counts.get(d, 0)
        pct = (c / total_entities) * 100.0 if total_entities else 0.0
        print(f"| Degree {d:2d} | {c:8d} entities | {pct:6.2f}% |")

    # Grouped higher degrees
    d_11_20 = sum(counts.get(d, 0) for d in range(11, 21))
    d_21_50 = sum(counts.get(d, 0) for d in range(21, 51))
    d_gt_50 = sum(counts.get(d, 0) for d in counts if d > 50)
    d_0 = counts.get(0, 0)

    if d_0 > 0:
        print(f"| Degree  0 | {d_0:8d} entities | {(d_0/total_entities)*100.0:6.2f}% |")
    print(f"| Degree 11-20 | {d_11_20:8d} entities | {(d_11_20/total_entities)*100.0:6.2f}% |")
    print(f"| Degree 21-50 | {d_21_50:8d} entities | {(d_21_50/total_entities)*100.0:6.2f}% |")
    print(f"| Degree > 50  | {d_gt_50:8d} entities | {(d_gt_50/total_entities)*100.0:6.2f}% |")

    # Share of entities returning insufficient_evidence under MIN_LINKS = 2
    insufficient_count = sum(counts.get(d, 0) for d in range(0, MIN_LINKS))
    insufficient_share = (insufficient_count / total_entities) * 100.0 if total_entities else 0.0

    print("\n" + "-" * 70)
    print(f"MIN_LINKS Threshold: {MIN_LINKS}")
    print(f"Entities returning insufficient_evidence (degree < {MIN_LINKS}): {insufficient_count} / {total_entities} ({insufficient_share:.2f}%)")
    print("-" * 70)

    return {
        "total_entities": total_entities,
        "counts_per_degree": dict(counts),
        "insufficient_count": insufficient_count,
        "insufficient_share_pct": round(insufficient_share, 2),
    }


def evaluate_negative_controls():
    print("\n" + "=" * 70)
    print("2. NEGATIVE CONTROLS EVALUATED AGAINST REAL WATCHLIST ('DOM Limited')")
    print("=" * 70)

    watchlist = ["DOM Limited"]
    controls = [
        {"name": "OMNIA TECHNOLOGIES S.A.", "id": "10000280", "expected": "clear"},
        {"name": "GAO SHENG LIMITED", "id": "10000854", "expected": "clear"},
        {"name": "Dewburn Enterprises Inc.", "id": "10000290", "expected": "insufficient_evidence"},
        {"name": "Skytrack Investments Limited", "id": "10017419", "expected": "insufficient_evidence"},
        {"name": "KIRBY GARDENS LTD.", "id": "10000109", "expected": "insufficient_evidence"},
    ]

    print("| # | Entity Name | Node ID | Degree | Verdict (D1) | Verdict (D4) | Expected | Pass? |")
    print("|---|---|---|---|---|---|---|---|")

    results = []
    for idx, c in enumerate(controls, 1):
        name = c["name"]
        exp = c["expected"]
        node_id = c["id"]

        deg_q = f"MATCH (e:Entity {{node_id: '{node_id}'}})-[r]-() RETURN count(r)"
        deg = ro(GRAPH_NAME, deg_q).get("rows", [[0]])[0][0]

        r1 = run_deterministic_investigation(name, watchlist=watchlist, depth=1)
        r4 = run_deterministic_investigation(name, watchlist=watchlist, depth=4)

        v1 = r1["verdict"]
        v4 = r4["verdict"]
        passed = (v4 == exp)

        print(f"| {idx:2d} | {name[:24]:<24} | {node_id} | {deg:2d} | {v1:<12} | {v4:<12} | {exp:<12} | {str(passed):<5} |")

        results.append({
            "name": name,
            "id": node_id,
            "degree": deg,
            "verdict_d1": v1,
            "verdict_d4": v4,
            "expected": exp,
            "passed": passed,
            "findings_count_d4": len(r4["evaluation"]["findings"]),
        })

    return results


if __name__ == "__main__":
    dist = measure_distribution()
    neg = evaluate_negative_controls()
    with open(REPO_ROOT / "docs" / "degree_distribution.json", "w", encoding="utf-8") as f:
        json.dump({"distribution": dist, "negative_controls": neg}, f, indent=2)
    print("\nSaved degree distribution and negative controls to docs/degree_distribution.json")
