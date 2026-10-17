# STATE.md — Project Memory & Phase Tracker

## Current Phase: p6/p7/p8 CODE & VERIFICATION COMPLETE (Ablation, Model Benchmark, Failure Modes, Invariants & Verification Matrix Done) / Ready for p7 (Cloud DB by Human) & p8 (Human Video & Submission)

## Done (2026-10-17 session — real execution, all evidenced in docs/test_report.md)
- **Cohesive Forensic UI Redesign**: Fully redesigned interface using coordinated design skills (`frontend-design`, `ui-ux-pro-max`, `impeccable`, `design-taste-frontend`, `web-design-guidelines`). Implemented dark institutional obsidian/navy canvas, 3-tier CSS token hierarchy, Plus Jakarta Sans + JetBrains Mono typography, Cytoscape graph canvas toolbar (zoom/fit/reset), interactive Node Inspector, bounded Evidence Ledger with sticky table header, accessible keyboard skip link, ARIA landmarks/labels, and live regions. Verified visually on Desktop (1280x900) and Mobile (390x844) with zero backend breakage.
- **Model Benchmark & Live Demo Runs**: `scripts/bench_models.py` evaluated 3 models; selected `nvidia/nemotron-3-super-120b-a12b` (7/10 tool accuracy, mean latency 3779ms, replacing legacy vision model). Ran 3 live runs per demo entity with 100% deterministic verdict parity.
- **Failure Modes Resilience**: Tested invalid key, simulated 429, malformed args, and timeouts; all fell back gracefully to deterministic rule engine without crashing. 4 new unit tests added in `tests/test_agent.py` (total 46 tests).
- **Verification Matrix**: Pytest 46/46 PASS (0 skips, 0 failures); `ruff check .` 0 errors in core/agent/api/tests/scripts; `scripts/check_invariants.py` 6/6 pass; Git secret scan clean (zero nvapi keys in tracked files or commit history).
- **Hardening & Stability**: Memory under 10 concurrent investigations capped at 92.54 MiB / 512 MiB limit (peak 18.07%); DB outage self-heals in 0.92s; clean clone test from git archive in temporary directory passed 100%; desktop and mobile (390px) Cytoscape UI verified in browser.
- **Documentation**: Updated `README.md` (user story, depth contrast screenshot, Mermaid diagrams, rules, consistency matrix, AI disclosure), `docs/EXPLAIN.md`, `docs/blog.md`, `docs/demo_runbook.md`, `docs/HUMAN_TODO.md`, and created `docs/manual_check.md` (8 standalone PowerShell verification commands).

## Decisions (with reason)
- **Primary Model**: `nvidia/nemotron-3-super-120b-a12b` selected after hosted benchmarking against EOL models (49b returned 410) and small models (laguna scored 4/10). Achieved 7/10 tool accuracy and fast execution.
- **Primary Dataset**: **ICIJ Offshore Leaks** (Panama Papers SAM/SEY subset). Fits in 40.91MB RAM (FalkorDB Cloud 100MB cap), loads in 2.91s, passes 100% of tests, provides real historical investigations and proved depth-3 contrast.
- **Safe Fallback**: Agent loop implements automatic fallback to deterministic rules engine whenever LLM encounters 429 rate limits or invalid responses, ensuring 0% runtime crash rate.

## Open Issues
- None in code. Cloud DB and Render hosting await human free account creation.

## HUMAN ACTIONS Pending (See docs/HUMAN_TODO.md)
1. Approve PROVISIONAL choices in `docs/HUMAN_TODO.md` (ICIJ demo entities & negative controls).
2. Provision FalkorDB Cloud free instance and run `.\.venv\Scripts\python.exe data/load.py --reset --source icij`.
3. Connect repo to Render.com and deploy with `render.yaml`.
4. Record 2-minute demo video following `docs/demo_runbook.md` (update README.md with link).
5. Submit project on WeMakeDevs before Sun 18 Oct 2026 23:59 IST.

