# STATE.md — Project Memory & Phase Tracker

## Current Phase: p6 COMPLETE / Ready for p7 (Cloud Deploy)

## Done
- **p0/p1 (Bootstrap)**: Repo skeleton, Docker Compose (falkordb-server + browser 3001:3000 + app), core/db.py, core/config.py, scripts/q.py, tests/test_smoke.py. Verified live 2026-10-16.
- **p2 (Data & Graph)**: Schema with range & full-text indexes. Synthetic seed (5,116 entities, 3,002 officers, 1,503 addresses, 501 intermediaries, 13,208 edges). Idempotent loader. Demo cases (data/demo.json). Raw ICIJ filter script.
- **p3 (Tools & MCP)**: 7 typed graph tools in core/tools.py. MCP Server wrapper (official Python SDK). Tests pass.
- **p4 (Rules & Agent Loop)**: Deterministic rules engine (core/rules.py). Memo verifier (core/verifier.py). NVIDIA client (agent/llm.py) + fallback (agent/fallback.py). Agent loop (agent/loop.py). Regression suite.
- **p5 (API & UI)**: FastAPI with SSE, self-seeding, rate limits (api/main.py). Dark mode UI with Cytoscape.js graph, depth toggle, ICIJ disclaimer (web/).
- **p6 (Test & Review) — VERIFIED 2026-10-16 session 2**:
  - 31/31 pytest tests PASS (evidence: pytest run output).
  - `scripts/check_invariants.py` → ALL PASSED (evidence: command output).
  - `ruff check .` → All checks passed (evidence: command output).
  - 5 demo cases PASS with depth 1→3 flip proven: Blue Star clear→escalate via WATCHLIST_PATH (evidence: scripts/verify_demo_cases.py output).
  - SSE end-to-end flow: POST /investigate → stream shows step×6 → verdict(escalate) → done (evidence: curl output).
  - Browser UI verified at http://localhost:8000: dark mode, status bar, Cytoscape, ICIJ footer.
  - Docker: all 3 containers healthy (falkordb-server, falkordb-browser, ownership-lens-app).

## Decisions (with reason)
- **FalkorDB Docker Image**: `falkordb/falkordb-server:latest` for DB service; browser remapped to 3001:3000.
- **Algorithm Procedure Names**: Verified live docs: `algo.pageRank` positional args; `algo.betweenness` config map; `algo.labelPropagation` for communities; `algo.SPpaths`.
- **Fulltext Indexing**: `CALL db.idx.fulltext.createNodeIndex('Entity', 'name')`.
- **Deterministic Verdicts**: Invariant 5 enforced — core/rules.py alone computes verdict.
- **expected.json fix (2026-10-16)**: Blue Star d=1 corrected from `insufficient_evidence` → `clear`. Entity is resolved and has links ≥ MIN_LINKS=1; no high/medium rules fire. `insufficient_evidence` only for unresolved or too-sparse entities. Did NOT weaken code — wrong expected was fixed with graph evidence.
- **demo.json fix (2026-10-16)**: Matching correction to data/demo.json Blue Star expected_depth_1.
- **rules_fired added to fallback return (2026-10-16)**: Added `rules_fired` key to run_deterministic_investigation return dict for traceability.

## Open Issues
- LLM live path not tested: NVIDIA API key not configured (`llm_key: false`). Fallback runs 100% without it.
- ICIJ real CSV not loaded: using synthetic data. Human must download if desired.

## HUMAN ACTIONS Pending
1. **NVIDIA API Key** (optional for LLM mode): Add `nvapi-...` key from https://build.nvidia.com to `.env` as `NVIDIA_API_KEY`. Then `docker compose up -d --build app` to apply.
2. **Record Video**: Follow `docs/demo_runbook.md`. Show Blue Star d=1 vs d=3 flip live in UI. 2 min max.
3. **Submit**: Before Sun 18 Oct 2026 23:59 IST — public repo + README + video link + track selection.
4. **(Optional) ICIJ Data**: Download from https://offshoreleaks-data.icij.org/offshoreleaks/csv/full-oldb.LATEST.zip, run `data/make_seed.py` to create subset, reload with `data/load.py`. Improves demo authenticity.
