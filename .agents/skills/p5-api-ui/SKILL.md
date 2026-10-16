---
name: p5-api-ui
description: "Builds the FastAPI backend with self-seeding, rate limits and SSE trace streaming, plus the minimal static UI with verdict card, evidence ledger, trace, depth toggle and Cytoscape subgraph. Use after p4."
---

# p5: API and UI

## API `api/main.py`
| Endpoint | Behaviour |
|---|---|
| `GET /health` | `{db: ok/down, graph: ready/seeding/missing, llm_key: bool, mode: live/replay-only, rss_mb}`. Never return secrets. |
| `GET /entities/search?q=` | `resolve_entity`, <= 5 candidates (autocomplete). |
| `POST /investigate` | Body `{entity_id or name, watchlist: [names], depth: 1..3}`. Returns `{run_id}`; runs in background. |
| `GET /stream/{run_id}` | SSE: `step` (tool, params, rows, ms, source), `verdict`, `memo`, `done`, `error`. |
| `GET /case/{id}` | Stored Case + ledger. |
| `GET /replay/{slug}` | Saved trace from `data/replay/`, response marked `mode: "replay"`. |

Required behaviour:
- **Self-seed:** on startup, if the graph is missing/empty, call `ensure_seed()` in the background; `/health` reports `seeding`; investigations return 503 with a clear message until ready.
- **Limits:** per-IP token bucket (e.g. 6 investigations/hour), global semaphore (2 concurrent), daily LLM cap. On cap or 429: serve replay for demo entities, otherwise a clear "demo limit reached" error. Replay is always labelled.
- **Validation:** name <= 120 chars, watchlist <= 10 items, depth 1-3, reject control characters.
- **CORS:** only origins in `ALLOWED_ORIGINS`.
- **Errors:** no stack traces to clients; log server-side without secrets.
- If FalkorDB is down: `/health` red and investigations fail loudly. Never degrade into an LLM-only answer.
- Keep RSS < 350MB (log it in `/health`).

## UI `web/` (no build step; plain HTML/JS/CSS; Cytoscape from cdnjs, pinned version)
`config.js` exports `API_BASE` (edited at deploy). On load: ping `/health`; if slow, show "Waking the agent (about a minute)" with retry.
Panels:
1. Input: entity search (autocomplete), watchlist field (prefilled from demo set), depth selector, Run.
2. Verdict card: badge (`clear / review / escalate / insufficient evidence`), memo, `memo_source`, `replay` label when applicable.
3. **Depth contrast:** a "Compare depth 1 vs 3" button runs both and shows two verdict cards side by side. This is the demo's main beat.
4. Evidence ledger: table of rule, severity, text, and the path as a hop chain.
5. Trace: each tool call with args, rows, ms, `llm`/`forced` tag, streaming live.
6. Subgraph: Cytoscape of nodes/edges in the evidence paths; colour by label; highlight the watchlist path.
7. Prior cases: from `recall_cases`.
8. Footer: ICIJ attribution (ODbL / CC BY-SA), "Indicators requiring human review. Inclusion in ICIJ data is not evidence of wrongdoing."
Keep it plain and legible. No frameworks, no animations. Verify visually with the Antigravity browser tool and attach screenshots to the walkthrough.

## Tests
API tests with `httpx` against a test app (validation, limits, SSE event order, health states, CORS) · UI smoke through the browser tool: search, run, compare, view subgraph.

## Done when
Full local flow works at http://localhost:8000 (API serving `web/` too for local use) and via the separate static page; STATE.md updated.
