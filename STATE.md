# STATE.md — Project Memory & Phase Tracker

## Current Phase: FINAL PASS (H1–H5) VERIFICATION COMPLETE · 53/53 TESTS PASS · ZERO FORBIDDEN HITS · ALL INVARIANTS PASS

## Done (Final Pass H1–H5)
- **H1 Default Mode**: Web UI & API default to deterministic mode (~0.69s). Visible toggle "AI agent mode (LLM tool selection, ~1 min)" off by default with live elapsed-time timer. Tested via `tests/test_h1_default_mode.py` (3/3 pass).
- **H2 Verifier Diagnosis**: Diagnosed all 12 rejected runs: zero invented names. Rejections caused by multi-line header capture, trailing punctuation, and corporate abbreviation variants. Normalized matching without loosening hallucination detection. New acceptance rate across 5 cases x 3 runs: **15/15 (100.0%)**. Poisoned injection test strictly caught (`Valid=False`).
- **H3 Skip Live LLM Tests When Key Absent**: `tests/test_injection.py` skips when `NVIDIA_API_KEY` is absent. `pytest -q -rs` with key unset: 52 passed, 1 skipped in 30.11s; with key set: 53 passed in 138.38s.
- **H4 Honesty Paragraph & Heading Fix**: Added Section 3.1 to `README.md` documenting LLM tool choice, call distribution, verifier acceptance, and live latency numbers. Fixed heading in `docs/demo_cases.md` so `GLAISDALE LIMITED` is under active demo cases.
- **H5 Verification Suite**: `git grep -n -i -E "forbidden_terms_pattern"` returns 0 matches across the whole repository outside `data/make_synthetic.py` and `data/seed`. `pytest -q -rs` (53 passed), `ruff check .` (All checks passed), `python scripts/check_invariants.py` (All 6 invariants passed). Updated `docs/final_report.md`. Container rebuilt and verified healthy.
- **G1 Network Graph Redesign (`web/app.js`, `web/style.css`, `web/index.html`)**:
  - Replaced force-directed (cose) with deterministic preset coordinates: horizontal chain on desktop ($S=220$px $\ge 160$px), vertical chain on mobile $\le 600$px ($S=135$px $\ge 110$px).
  - Evidence path rendered by default with red edges (`#dc2626`, width 4, triangle arrowhead) and red-bordered path nodes.
  - SUBJECT styled with blue focus ring and `[SUBJECT]` tag; WATCHLIST target filled red with `[WATCHLIST (demo)]` tag. Neutral director styling.
  - Direct context nodes capped at 8 (opacity 0.35, no label except hover, hidden behind "Show context" toggle by default).
  - Service providers, address hubs, and placeholders excluded; badge shows `"N more links via service providers (hidden)"`.
  - Wrapped labels with text background (`#ffffff`, opacity 0.9, padding 3px), names >28 chars shortened with ellipsis (`...`). Edge labels only on path edges as pills.
  - `#hopChainBanner` rendered above graph. Node click opens `#nodeInspector` (name, type, jurisdiction, node_id, source, status). Fit and Reset buttons work.
  - Compare view renders side-by-side on desktop, stacked on mobile (`#cyD1` and `#cyD4`); canvas height $\ge 420$px desktop, $\ge 360$px mobile; zero horizontal scroll at 390px.
- **G2 Automated Visual Verification (`scripts/verify_graph_visual.py`, `tests/test_visual_graph.py`)**:
  - Tested 1280x800 desktop and 390x844 mobile viewports with Playwright:
    - 0 pairwise overlaps among rendered element bounding boxes.
    - 4 path edges styled red (`#dc2626`, width 4, triangle arrowhead).
    - 1 target node (`DOM Limited`) filled red with `[WATCHLIST (demo)]` tag.
    - No label truncated except via documented ellipsis (>28 chars).
    - 0 console errors. Zero horizontal scroll at 390px (scrollWidth=390, clientWidth=390).
    - Compare view displays Depth 1 clear and Depth 4 escalate side-by-side.
  - Saved screenshots to `docs/screens/` (`primary_demo_desktop.png`, `primary_demo_mobile.png`, `contrast_comparison_desktop.png`).
- **G3 Wording Exact Alignment**:
  - (1) `agent/run.py:5`: docstring example updated to `GLAISDALE LIMITED`.
  - (2) `docs/blog.md:7`: opening paragraph rewritten to describe active demo (`GLAISDALE LIMITED`, depth 1 clear, depth 4 reaches compliance watchlist via chained shared directors; hubs/service providers excluded; "compliance watchlist (demo list chosen by graph criteria)", no individual called nominee, no "serves on fifty boards", talks about companies and structures).
  - (3) `docs/demo_cases.md`: replaced previous entity row with `GLAISDALE LIMITED` and updated section heading.
  - (4) `docs/review.md:8`: replaced with "watchlisted entity".
  - Verified `git status --short data/seed/nodes-entities.csv` is empty (unmodified).
  - Verified 100% parity across `data/demo.json`, `README.md`, `docs/EXPLAIN.md`, `docs/demo_runbook.md`.
- **G4 Model Benchmark & Live Runs Analysis**:
  - Printed `docs/model_bench.md` and `docs/live_demo_runs.json`.
  - Reported per-case LLM vs forced calls, memo source, verifier result, and latency (62.4s for full live investigation on GLAISDALE LIMITED D4).
  - Explicitly recommended deterministic or replay mode (`?mode=replay`) for video recording due to latency >30s.
- **G5 Final Validation & Suite**:
  - `pytest -q -rs`: **50/50 PASS** in 106.20s (100% pass rate).
  - `ruff check .`: **0 errors**.
  - `scripts/check_invariants.py`: **6/6 PASS**.
  - Docker container rebuilt with `docker compose up -d --build app`; `/health` verified healthy (`rss_mb: 73.9`).
  - `docs/demo_runbook.md`, `docs/test_report.md`, and `docs/final_report.md` updated with G1–G5 raw outputs.

## Decisions (with reason)
- **Preset Layout**: Replaced force-directed Cytoscape cose layout with deterministic preset coordinates ($S=220$px desktop, $S=135$px mobile) to eliminate label overlap and guarantee readable presentation.
- **Video Recording Recommendation**: Replay or deterministic mode recommended for submission video because live LLM multi-turn investigations take ~62 seconds.

## Open Issues
- None in code.

## HUMAN ACTIONS Pending (See docs/HUMAN_TODO.md)
1. Record 2-3 minute demo video following `docs/demo_runbook.md` (GLAISDALE LIMITED depth 1 vs 4).
2. Publish blog post from `docs/blog.md`.
3. (Optional) Provision free FalkorDB Cloud + Render per `docs/HUMAN_TODO.md` (or submit local Docker instructions).
4. Submit WeMakeDevs Track 1 entry before Sun 18 Oct 2026, 23:59 IST.


