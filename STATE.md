# STATE.md — Project Memory & Phase Tracker

## Current Phase: CONTEST READINESS AUDIT COMPLETE · LIVE RENDER VERIFIED · 6/6 INVARIANTS PASS

## Done (Contest Readiness Audit & Deployment Upgrade)
- **API Input Validation & Replay Resilience (`api/main.py`)**:
  - Request validation placed before DB ping check: empty entity returns 400 Bad Request, invalid depth returns 422 Unprocessable Entity.
  - Added `find_replay_dossier` and `execute_replay_run`: when FalkorDB is sleeping/in standby on Render, `/investigate` automatically and cleanly streams verified evidentiary replay data (`mode: "replay"`).
  - `/entities/search?q=...` includes fallback search across `data/demo.json` for seamless autocomplete during DB standby.
- **Offline Replay Dossiers (`data/replay/`)**:
  - Built complete, verified graph replays for all benchmark cases: `glaisdale-limited.json` (D4 escalate), `glaisdale-limited-d1.json` (D1 clear), `millex-international-limited.json` (D2 review), `omnia-technologies-sa.json` (D2 clear), `dewburn-enterprises-inc.json` (D1 insufficient_evidence).
- **Web UI Standby & Replay Styling (`web/app.js`, `web/style.css`, `web/index.html`)**:
  - `checkHealth()` accurately reflects standby vs live: `FalkorDB: Standby (Replay Active)` with amber `.health-dot.standby` indicator.
  - Verdict badge displays dedicated `.badge-replay` pill when rendering replay dossiers; memo source labeled `Source: VERIFIED REPLAY DOSSIER`.
  - Cache buster updated to `v=20261019_win` to prevent stale browser assets.
- **Test Suite & Invariants**:
  - `tests/test_api.py`: 8/8 tests pass (including `test_investigate_replay_fallback`, `test_entities_search_standby`, and `test_all_demo_replays_exist`).
  - `scripts/check_invariants.py`: 6/6 non-negotiable architectural invariants verified passing.
  - `ruff check .`: 0 errors.
- **Live Render Verification (`https://acd-agent-3hz7.onrender.com/`)**:
  - Verified `/health`, `/demo`, `/entities/search?q=GLAISDALE`, and all 5 `/replay/{slug}` endpoints return HTTP 200.
  - Verified `POST /investigate` and SSE `/stream/{run_id}` stream live tool execution trace, verdict (`clear` at D1, `escalate` at D4), memo, and Cytoscape graph nodes.

## Decisions (with reason)
- **High-Availability Replay Fallback**: Free-tier cloud databases sleep after idle periods. Enabling `/investigate` to stream verified offline graph replays guarantees judges testing the live URL will never see a 503 error or empty state, while strictly honoring Invariant 11 (`mode: "replay"` clearly labeled).
- **Preset Layout**: Deterministic preset coordinates eliminate node and label overlap on both desktop and mobile viewports.

## Open Issues
- None in code or deployment.

## HUMAN ACTIONS Pending (See docs/HUMAN_TODO.md)
1. **Start Local Docker Desktop** (for local testing): Double-click Docker Desktop icon from Windows Desktop or Start Menu, then run `docker compose up -d`.
2. **Submit WeMakeDevs Track 1 entry** with:
   - Live URL: `https://acd-agent-3hz7.onrender.com/`
   - GitHub Repo: `https://github.com/GoDxVictoryRR/ACD-Agent`
   - Track: Track 1 — Agents That Act on Connected Data



