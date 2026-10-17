# STATE.md — Project Memory & Phase Tracker

## Current Phase: p6/p7 COMPLETE (Advanced Rules, MCP Live Path, Invariants & Ablation Done) / Ready for p7 (Cloud DB by Human) & p8 (Submission)

## Done (2026-10-17 session — real execution, all evidenced in docs/test_report.md)
- **Task 1: Raw ICIJ CSV Inspection**: Evaluated 5 raw node/rel CSVs in data/raw/; catalogued exact columns, row counts (814k entities, 771k officers, 26k intermediaries, 402k addresses, 3.33M edges), 14 distinct rel_types, and status values in `docs/data_notes.md`.
- **Task 2: Filtered Subset Extraction**: Extracted Panama Papers Samoa (SAM) & Seychelles (SEY) cluster into `data/seed/icij/` (51,940 nodes, 58,891 edges, total seed 5.8MB << 40MB limit, all files < 3.1MB). Created `data/seed/icij/ATTRIBUTION.md` (ODbL / CC BY-SA).
- **Task 3: Dual Idempotent Loader**: Added `DATA_SOURCE=icij|synthetic` to `data/load.py` with labeled batch loading. Load time: 2.91s; RAM: 40.91MB (<=60MB cap); 3-hop p95: 44.36ms; 125 Cypher round trips.
- **Task 4: Duplicate Name Disambiguation**: Updated `core/tools.py: resolve_entity` to return `ambiguous` with candidate list.
- **Task 5: Demo Cases & Depth Flip**: Discovered real ICIJ primary depth flip: `MOSSACK FONSECA & CO. (SAMOA) LIMITED.` (`10001171`) -> `TIANSHENG INDUSTRY AND TRADING CO., LTD.` (`10000001`) (d1: clear, d2: review, d3: escalate).
- **Task 6: Exposure Statistics & Disclaimers**: Vectorized reverse BFS in `scripts/exposure_stats.py`; updated UI, templates, and README.
- **Task 7: Primary Dataset Decision**: ICIJ set as default primary. Rebuilt container `ownership-lens-app` and verified health.
- **Task 8: Low-Link Threshold & "Clear" Display**: Enforced `MIN_LINKS = 2` (`< 2` returns `insufficient_evidence`, never `clear`); "clear" displays as `"No indicators found within depth N"`. Added isolated/unknown/ambiguous tests.
- **Task 9: check_invariants.py Expansion**: 6 invariants verified: forbidden imports, agent Cypher isolation, ro_query read enforcement, Case/ABOUT/CITED exclusion, tracked secrets, and data/raw/ gitignore.
- **Task 10: Path Tagging & Watchlist Isolation**: Every `path_between` result tags `target_id` and `is_watchlist`; rules count only watchlist targets. Non-watchlist path never escalates.
- **Task 11: Per-Case Scratch Graph Algorithms**: Executed `algo.pageRank`, `algo.betweenness`, `algo.WCC`, and `algo.labelPropagation` on scratch graph. Implemented `COMMUNITY_WATCHLIST` and `HUB_CENTRALITY` (calibrated at 99.5th percentile betweenness $\ge 50.0$). Demo entities verified.
- **Task 12: Node-Disjoint Path Redundancy**: Implemented `PATH_REDUNDANCY` ($\ge 2$ node-disjoint paths -> escalate "independent paths") and `PATH_DEPENDENCY` (single intermediate node -> review "exposure depends on <node>").
- **Task 13: MCP in Live Path & RSS Measurement**: Connected agent loop & fallback to `mcp.server.MCPServer` in-process (`via: mcp`); verified container RSS at 60.7 MiB / 512 MiB (11.85% utilization).
- **Task 14: Systematic Ablation Study**: `scripts/ablation.py` -> `docs/ablation.md` & `README.md` table across 5 conditions. Pytest suite expanded to **42/42 PASS**.

## Decisions (with reason)
- **Primary Dataset**: **ICIJ Offshore Leaks** (Panama Papers SAM/SEY subset). Fits in 40.91MB RAM (FalkorDB Cloud 100MB cap), loads in 2.91s, passes 100% of tests, provides real historical investigations and proved depth-3 contrast. Synthetic kept as tested fallback.
- **Labeled Batch Querying**: Used label-qualified `MATCH (src:Label {node_id}) MATCH (dst:Label {node_id})` during CSV edge import to avoid full table scans across labels, accelerating edge load from timeout to 1.16s for 58,891 edges.
- **Dynamic Regression Testing**: `tests/regression/test_regression.py` dynamically loads `expected_icij.json` when `DATA_SOURCE=icij` and `expected.json` when `synthetic`, guaranteeing continuous integration on both data sources.

## Open Issues
- Model benchmark (F6): `scripts/bench_models.py` requires live NVIDIA credits. Marked PROVISIONAL.
- Cloud DB instance: Human must provision free instance on app.falkordb.cloud (see docs/HUMAN_TODO.md).

## HUMAN ACTIONS Pending (See docs/HUMAN_TODO.md)
1. Approve PROVISIONAL choices in `docs/HUMAN_TODO.md` (ICIJ demo entities & negative controls).
2. Provision FalkorDB Cloud free instance and run `.\.venv\Scripts\python.exe data/load.py --reset --source icij`.
3. Connect repo to Render.com and deploy with `render.yaml`.
4. Record 2-minute demo video following `docs/demo_runbook.md`.
5. Submit project on WeMakeDevs before Sun 18 Oct 2026 23:59 IST.
