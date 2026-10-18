"""
scripts/explore_demo.py — Finds candidate demo entities showing depth-1 vs depth-3 contrast.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.config import DATA_SOURCE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DOCS_DIR = REPO_ROOT / "docs"
DATA_DIR = REPO_ROOT / "data"


def generate_demo_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    demo_json_path = DATA_DIR / "demo.json"

    if DATA_SOURCE == "icij":
        demo_data = {
            "demo_entities": [
                {
                    "id": "10001171",
                    "name": "MOSSACK FONSECA & CO. (SAMOA) LIMITED.",
                    "expected_depth_1": "clear",
                    "expected_depth_3": "escalate",
                    "description": "At depth 1, appears clear. At depth 3, links through nominee officer MOSSFON SUBSCRIBERS LTD. to watchlist entity TIANSHENG INDUSTRY AND TRADING CO., LTD. — verdict flips to escalate.",
                },
                {
                    "id": "10014876",
                    "name": "Millex International Limited",
                    "expected_depth_1": "review",
                    "expected_depth_3": "review",
                    "description": "Connected to nominee officer hub and intermediary concentration; review verdict without escalating to watchlist.",
                },
                {
                    "id": "10017419",
                    "name": "Skytrack Investments Limited",
                    "expected_depth_1": "clear",
                    "expected_depth_3": "clear",
                    "description": "Connected entity with no high-risk hubs or watchlist connections; remains clear at depth 1 and depth 3.",
                },
                {
                    "id": "10000290",
                    "name": "Dewburn Enterprises Inc.",
                    "expected_depth_1": "clear",
                    "expected_depth_3": "clear",
                    "description": "Low-link entity (degree 1) with clean structure and zero watchlist exposure.",
                },
            ],
            "watchlist": ["TIANSHENG INDUSTRY AND TRADING CO., LTD."],
        }
    else:
        demo_data = {
            "demo_entities": [
                {
                    "id": "ENT_BLUESTAR_01",
                    "name": "GLAISDALE LIMITED",
                    "expected_depth_1": "clear",
                    "expected_depth_3": "escalate",
                    "description": "Appears minimal at depth 1. At depth 3, links through nominee director to DOM Limited.",
                },
                {
                    "id": "ENT_SILVERLINE_01",
                    "name": "Silverline Capital Management Ltd",
                    "expected_depth_1": "review",
                    "expected_depth_3": "review",
                    "description": "Exposed to high-degree nominee officer John Alexander Vance (officer in 50+ offshore shells).",
                },
                {
                    "id": "ENT_ORION_01",
                    "name": "Orion Global Logistics Corp",
                    "expected_depth_1": "review",
                    "expected_depth_3": "review",
                    "description": "Registered at mass incorporation address hub (Suite 301, St. James Court) shared by 60+ entities.",
                },
                {
                    "id": "ENT_SOLITARY_01",
                    "name": "Solitary Enterprises Ltd",
                    "expected_depth_1": "clear",
                    "expected_depth_3": "clear",
                    "description": "Clean entity with a single solitary address, zero hub overlap, zero watchlist connection.",
                },
            ],
            "watchlist": [
                "DOM Limited",
                "Beta Nominees Ltd",
            ],
        }

    with open(demo_json_path, "w", encoding="utf-8") as f:
        json.dump(demo_data, f, indent=2)

    logger.info("Saved demo.json to %s", demo_json_path)


if __name__ == "__main__":
    generate_demo_files()
    print("Demo files initialized successfully.")
