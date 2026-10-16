"""
scripts/q.py — Developer CLI for running Cypher queries against FalkorDB.
Usage:
    python scripts/q.py "MATCH (n) RETURN count(n)"
    python scripts/q.py "MATCH (n) RETURN count(n)" --graph ownership
    python scripts/q.py "CREATE (n:Test {name: 'demo'})" --write
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.config import GRAPH_NAME
from core.db import ro, rw


def main() -> int:
    parser = argparse.ArgumentParser(description="Query FalkorDB via CLI")
    parser.add_argument("query", help="Cypher query string to execute")
    parser.add_argument(
        "--graph",
        default=GRAPH_NAME,
        help=f"Target graph name (default: {GRAPH_NAME})",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Execute query as read-write (rw). Default is read-only (ro).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Format output as JSON",
    )

    args = parser.parse_args()

    try:
        if args.write:
            res = rw(args.graph, args.query)
        else:
            res = ro(args.graph, args.query)
    except Exception as exc:
        print(f"Query error: {exc}", file=sys.stderr)
        return 1

    if args.json_output:
        print(json.dumps(res, indent=2, default=str))
        return 0

    columns = res.get("columns", [])
    rows = res.get("rows", [])
    elapsed_ms = res.get("elapsed_ms", 0)

    if columns:
        print(" | ".join(str(c) for c in columns))
        print("-" * max(40, len(" | ".join(str(c) for c in columns))))
        for r in rows:
            print(" | ".join(str(cell) for cell in r))
    else:
        for r in rows:
            print(r)

    print(f"\n({len(rows)} rows, {elapsed_ms} ms)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
