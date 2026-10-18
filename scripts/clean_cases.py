#!/usr/bin/env python3
"""
scripts/clean_cases.py — Reads Case nodes from FalkorDB, reports count, and removes them.
Ensures clean graph state before and after demo recordings.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.db import rw, ro
from core.config import GRAPH_NAME

def clean_cases(graph_name: str = GRAPH_NAME) -> int:
    # 1. Read existing Case count
    res = ro(graph_name, "MATCH (c:Case) RETURN count(c) AS count")
    rows = res.get("rows", [])
    initial_count = rows[0][0] if rows else 0
    print(f"[clean_cases] Found {initial_count} Case node(s) in graph '{graph_name}'.")

    if initial_count == 0:
        print("[clean_cases] Graph is already clean. 0 Case nodes removed.")
        return 0

    # 2. Delete relationships and Case nodes
    # Delete incident edges first, then Case nodes
    rw(graph_name, "MATCH (c:Case)-[r]-() DELETE r")
    rw(graph_name, "MATCH (c:Case) DELETE c")

    # 3. Verify clean state
    res_after = ro(graph_name, "MATCH (c:Case) RETURN count(c) AS count")
    rows_after = res_after.get("rows", [])
    after_count = rows_after[0][0] if rows_after else 0
    removed = initial_count - after_count
    print(f"[clean_cases] Successfully removed {removed} Case node(s). Remaining: {after_count}.")
    return removed

if __name__ == "__main__":
    clean_cases()
