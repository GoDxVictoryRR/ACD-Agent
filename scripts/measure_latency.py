"""
scripts/measure_latency.py — Measure p50, p95, p99 latency across 50 runs for Depth 1, 2, 3, 4.
Ensures p95 < 2s for Depth 4.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent.fallback import run_deterministic_investigation

ENTITY_NAME = "GLAISDALE LIMITED"
WATCHLIST = ["DOM Limited"]
RUNS = 50


def measure():
    print("=" * 75)
    print(f"MEASURING LATENCY ACROSS {RUNS} RUNS PER DEPTH: {ENTITY_NAME}")
    print("=" * 75)

    results = {}

    for depth in [1, 2, 3, 4]:
        latencies = []
        # Warmup
        run_deterministic_investigation(ENTITY_NAME, watchlist=WATCHLIST, depth=depth)

        for _ in range(RUNS):
            t0 = time.perf_counter()
            run_deterministic_investigation(ENTITY_NAME, watchlist=WATCHLIST, depth=depth)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            latencies.append(elapsed_ms)

        latencies.sort()
        p50 = statistics.median(latencies)
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]
        mean = statistics.mean(latencies)
        min_v = min(latencies)
        max_v = max(latencies)

        results[f"depth_{depth}"] = {
            "depth": depth,
            "runs": RUNS,
            "min_ms": round(min_v, 2),
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2),
            "max_ms": round(max_v, 2),
            "mean_ms": round(mean, 2),
            "p95_under_2s": p95 < 2000.0,
        }

        print(
            f"Depth {depth}: p50={p50:6.2f} ms | p95={p95:6.2f} ms | p99={p99:6.2f} ms | "
            f"mean={mean:6.2f} ms | (p95 < 2000ms: {p95 < 2000.0})"
        )

    out_file = REPO_ROOT / "docs" / "latency_stats.json"
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSaved latency stats to {out_file}")
    return results


if __name__ == "__main__":
    measure()
