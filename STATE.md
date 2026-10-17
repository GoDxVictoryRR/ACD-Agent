# STATE.md — Project Memory & Phase Tracker

## Current Phase: p6 COMPLETE / Ready for p7 (Cloud Deploy by Human) & p8 (Submission Ready)

## Done
- **Verification Matrix (18/18 PASS)**: All 18 items in PART 5 verified with recorded command output in docs/test_report.md.
  - 31/31 pytest tests pass (0 skips).
  - Clean ruff check and all invariants pass.
  - Determinism across 3 runs verified.
  - Cross-surface consistency verified (CLI == API across all demo entities).
  - Case node pollution isolation verified (0 pollution after 20 investigations).
  - Depth contrast flip proven: Blue Star d=1 (CLEAR) -> d=3 (ESCALATE via WATCHLIST_PATH).
  - Entity edge cases verified: unknown, ambiguous, isolated entities.
  - Prompt injection resistance verified with poisoned node.
  - LLM failure modes verified: invalid key, 429, malformed args, timeout.
  - Remove FalkorDB failure mode verified: /health down, /investigate fails loudly with 503.
  - Self-healing startup seeding verified: restored 10,122 nodes, 13,208 edges in 44.8s.
  - Resource limits verified: 512MB RAM cap, 63.4MB container RAM, 10.32MB FalkorDB, 0 OOM kills.
  - API hardening verified: 201-char name (422), control chars, depth 9 (422), watchlist 50 (422), wrong origin (no CORS echo), burst of 50 requests (429).
  - SSE stream integrity verified: status -> step -> verdict -> memo -> done, disconnect safe.
  - Browser UI verified on Desktop and 390px Mobile via browser subagents; screenshots saved in docs/screens/.
  - Clean-clone smoke test passed from fresh git clone.
  - Secret scan passed: zero real nvapi keys in git log, .env uncommitted.
  - Docker image: 317MB lean production build.
- **Documentation & Deliverables**:
  - README.md updated with architecture, data model, depth contrast screenshot, Cypher queries, rules table, and AI disclosure.
  - docs/EXPLAIN.md updated with plain-language technical defense and 10 judge Q&A.
  - docs/demo_runbook.md updated with 3 beats, exact voice-over script, and backup plan.
  - docs/blog.md updated with comprehensive technical article.
  - docs/HUMAN_TODO.md updated with step-by-step cloud deployment guide and provisional approvals.
  - docs/final_report.md written with complete evidence and metrics.

## Decisions (with reason)
- **Primary Dataset**: Synthetic graph with 10,122 nodes and 13,208 edges. Takes 10.32MB RAM in FalkorDB (leaves ~90MB headroom on 100MB free tier), self-seeds in 44.8s, and guarantees the depth contrast flip without personal data.
- **Active NVIDIA Model**: meta/llama-3.2-11b-vision-instruct (replaces EOL model).
- **Provisional Choices**: Flagged in docs/HUMAN_TODO.md for human approval.

## HUMAN ACTIONS Pending (See docs/HUMAN_TODO.md)
1. Approve PROVISIONAL choices in docs/HUMAN_TODO.md.
2. Create FalkorDB Cloud free tier instance and load seed with data/load.py.
3. Connect repo to Render.com and deploy web service using 
ender.yaml.
4. Record 2-minute video following docs/demo_runbook.md and publish blog.
5. Submit form with Track 1 before Sun 18 Oct 2026 23:59 IST.
