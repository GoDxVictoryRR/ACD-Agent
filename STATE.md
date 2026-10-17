# STATE.md — Project Memory & Phase Tracker

## Current Phase: p6 COMPLETE (re-verified 2026-10-17) / Ready for p7 (Cloud Deploy by Human) & p8 (Submission Ready)

## Done (2026-10-17 session — commands run, real evidence)
- **21-item verification matrix**: All verified with command output in docs/test_report.md.
  - 31/31 pytest tests pass.
  - ruff check: 0 errors (17 auto-fixed in scripts/).
  - 4/4 invariants pass (Invariant 4 added this session: data/raw gitignore check).
  - Determinism: 8 pairs × 3 runs = 100% identical.
  - Cross-surface: CLI == API (8/8 entity-depth pairs).
  - Pollution: 0 Case node pollution after 20 investigations.
  - Depth flip: Blue Star d=1 (clear) → d=3 (escalate via WATCHLIST_PATH). Proven.
  - Edge cases: unknown/ambiguous/clean/zero-link all correctly handled.
  - Prompt injection: treated strictly as data.
  - LLM failure modes: invalid key/429/malformed/timeout all fall back gracefully.
  - API hardening: 6/6 (201-char name/ctrl chars/depth9/wl50/wrong-CORS/burst).
  - SSE: event order correct, disconnect safe.
  - Resource limits: 62.16MB / 512MB, 0 OOM kills, FalkorDB 10.92MB.
  - DB removal: /health db=down, /investigate 503 loudly. Restored.
  - Self-heal: 42.96s to reseed 10122 nodes, 13208 edges from scratch.
  - Secret scan: 0 nvapi keys in tracked files, .env untracked.
  - data/raw: 7 ICIJ CSVs gitignored, not tracked.
- **F1 fix**: zero-link entity test added to verify_entities_edge_cases.py (test case 4).
- **F2 fix**: 4th invariant (data/raw gitignore) added to check_invariants.py.
- **F8 fix**: desc.md (40KB chat dump) deleted from git (commit df23ebd). scratch_prompt.txt untracked (in .gitignore).
- **Linter fix**: 17 import/whitespace issues in scripts/ auto-fixed.
- **Commit**: df23ebd — "fix: F2 add 4th invariant; F1 add zero-link test; F8 delete desc.md; fix script lint"

## Decisions (with reason)
- **Primary Dataset**: Synthetic graph (10,122 nodes, 13,208 edges). Fits in 10.92MB FalkorDB RAM (100MB free tier). Self-seeds in 42.96s. Guarantees depth contrast flip. No personal data risk.
- **Active NVIDIA Model**: meta/llama-3.2-11b-vision-instruct. Previous model (nvidia/llama-3.3-nemotron-super-49b-v1.5) EOL 2026-08-26.
- **PROVISIONAL choices**: Flagged in docs/HUMAN_TODO.md.

## Open Issues
- Model benchmark (F6): `scripts/bench_models.py` written but NOT RUN (requires valid NVIDIA API key with trial credits). Mark as PROVISIONAL.
- Browser UI: prior session screenshots in docs/screens/ — not re-taken this session due to network instability.
- Clean-clone smoke test: NOT RUN this session — must be done manually by human before submission.

## HUMAN ACTIONS Pending (See docs/HUMAN_TODO.md)
1. Approve PROVISIONAL choices in docs/HUMAN_TODO.md.
2. Run model benchmark: `.venv\Scripts\python.exe scripts/bench_models.py` (needs valid NVIDIA key).
3. Run clean-clone smoke test: `git clone <repo> <tmpdir> && cd <tmpdir> && python data/load.py && pytest tests/ -q`
4. Create FalkorDB Cloud free tier instance and load seed with `data/load.py --reset`.
5. Connect repo to Render.com and deploy web service using render.yaml.
6. Record 2-minute demo video following docs/demo_runbook.md (depth flip is the key beat).
7. Publish blog post from docs/blog.md.
8. Submit form with Track 1 before Sun 18 Oct 2026 23:59 IST.
