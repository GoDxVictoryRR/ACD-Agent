"""
agent/run.py — CLI entrypoint for running an entity investigation.

Usage:
    python -m agent.run --entity "Blue Star Maritime Holdings Ltd" --depth 3
    python -m agent.run --entity "Silverline Capital Management Ltd" --no-llm
    python -m agent.run --entity "Orion Global Logistics Corp" --watchlist data/demo.json --save-replay
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent.loop import run_investigation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPLAY_DIR = REPO_ROOT / "data" / "replay"


def load_watchlist(path_or_str: str | None) -> list[str]:
    if not path_or_str:
        return []
    path = Path(path_or_str)
    if path.exists() and path.suffix == ".json":
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "watchlist" in data:
                return data["watchlist"]
            elif isinstance(data, list):
                return data
        except Exception as exc:
            logger.warning("Could not parse watchlist file %s: %s", path, exc)
    # Comma-separated string
    return [w.strip() for w in path_or_str.split(",") if w.strip()]


def slugify(text: str) -> str:
    return re.sub(r"[^\w\-]+", "_", text.strip().lower())


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an offshore network investigation")
    parser.add_argument("--entity", required=True, help="Entity name to investigate")
    parser.add_argument("--depth", type=int, default=2, help="Investigation depth (1-3, default 2)")
    parser.add_argument("--watchlist", default="data/demo.json", help="Path to watchlist JSON or comma-separated names")
    parser.add_argument("--no-llm", action="store_true", help="Force deterministic execution without LLM")
    parser.add_argument("--save-replay", action="store_true", help="Save result to data/replay/<slug>.json")
    parser.add_argument("--graph", default=None, help="Target graph name override")

    args = parser.parse_args()

    wl = load_watchlist(args.watchlist)
    logger.info("Starting investigation of '%s' at depth %d (watchlist: %d items)...", args.entity, args.depth, len(wl))

    result = run_investigation(
        entity_name=args.entity,
        watchlist=wl,
        depth=args.depth,
        graph_name=args.graph,
        force_fallback=args.no_llm,
    )

    print("\n" + "=" * 60)
    print(f"ENTITY:  {result.get('entity_name')}")
    print(f"VERDICT: {result.get('verdict', '').upper()}")
    print(f"MEMO SOURCE: {result.get('memo_source')}")
    print("=" * 60)
    print(f"\nMEMO:\n{result.get('memo')}\n")

    findings = result.get("evaluation", {}).get("findings", [])
    if findings:
        print(f"FINDINGS ({len(findings)}):")
        for f in findings:
            print(f"  • [{f.get('severity').upper()}] {f.get('text')}")
    print("\n" + "=" * 60)

    if args.save_replay:
        REPLAY_DIR.mkdir(parents=True, exist_ok=True)
        slug = f"{slugify(args.entity)}_depth{args.depth}"
        replay_file = REPLAY_DIR / f"{slug}.json"
        with open(replay_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"Replay saved to: {replay_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
