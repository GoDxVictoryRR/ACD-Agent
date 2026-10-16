---
name: p7-deploy
description: "Containerises the backend and deploys it free: FalkorDB Cloud free tier, Render free web service, static UI on Vercel or Netlify, then verifies the live system. Use after p6 passes."
---

# p7: deploy ($0)

Topology: `web/` static on Vercel (or Netlify) -> FastAPI container on Render free -> FalkorDB Cloud free. The backend sits on Render, not on Vercel: the agent loop makes several sequential LLM and DB calls per request, which is a poor fit for short-lived serverless functions.
Limits that shape this: Render free = 512MB RAM, 0.1 CPU, sleeps after 15 min idle, ~1 min wake. FalkorDB Cloud free = 100MB, no persistence, no TLS, stopped after 1 idle day, deleted after 7. Re-check these on the providers' pages; they change.

## 1. Container (you)
- `Dockerfile`: `python:3.12-slim`, install `requirements.txt` only, copy `core agent mcp_server api web data/seed data/replay data/demo.json`, non-root user, `CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}`. No dev deps, no raw data.
- Add an `app` service to `docker-compose.yml` (depends on `falkordb`, env from `.env`) so `docker compose up` runs the whole stack locally. This is also the guaranteed fallback submission path (the rules accept local setup + video).
- Test: `docker compose up --build`; open http://localhost:8000; run a demo case; check RSS in `/health`.
- `render.yaml` blueprint: web service, `runtime: docker`, `plan: free`, `healthCheckPath: /health`, env vars declared with `sync: false` for secrets.

## 2. FalkorDB Cloud (human + you)
> **HUMAN REQUIRED:** create the free instance (p0 item 8) and put `FALKORDB_HOST/PORT/USERNAME/PASSWORD` in local `.env`. Check the dashboard for the real memory limit.
You: `python data/load.py --reset` against Cloud (`FALKORDB_SSL=false`). Verify counts and that memory stays under the cap with room for Cases. Then test self-heal: delete the graph, start the API, confirm `/health` goes `seeding` -> `ready`.

## 3. Render (human + you)
> **HUMAN REQUIRED:** Render dashboard -> New -> Web Service (or Blueprint from `render.yaml`) -> connect the GitHub repo -> Docker runtime -> Instance type **Free** -> set env vars: `NVIDIA_API_KEY`, `NVIDIA_MODEL`, `FALKORDB_HOST`, `FALKORDB_PORT`, `FALKORDB_USERNAME`, `FALKORDB_PASSWORD`, `FALKORDB_SSL=false`, `GRAPH_NAME`, `DAILY_LLM_CAP`, `ALLOWED_ORIGINS` (set after step 4). Deploy. Give you the service URL.
You: `curl https://<service>/health` until `graph: ready`.

## 4. Static UI (human + you)
You: set `API_BASE` in `web/config.js` to the Render URL; commit; push.
> **HUMAN REQUIRED:** Vercel (or Netlify): import the repo; root/publish directory `web`; framework "Other"; no build command. Deploy; give you the URL. Then add that URL to Render `ALLOWED_ORIGINS` and redeploy the backend.

## 5. Verify live (record in `docs/test_report.md`)
- `/health` green; UI loads in an incognito window and on a phone.
- All 3 demo cases and the depth-compare run live. The replay path works and is labelled.
- Cold start: after 16+ minutes idle, the UI shows the "waking" banner and recovers by itself.
- Force a 429 (temporarily set `DAILY_LLM_CAP=0`) -> replay or clear error, no crash.
- Browser devtools: no secrets in JS, no CORS errors.
- Re-run `scripts/check_invariants.py` on the deployed commit.

## 6. Keep it alive (optional)
Cloud DB is wiped after idle; the backend self-seeds, so a judge's first request after a long gap costs ~1-2 minutes. During the judging window the human may point a free uptime pinger at `/health` (check the service's current free terms). One always-on free Render service fits within the monthly free instance hours; two do not.

## 7. Fallback (take it early, not at the deadline)
If any step above is still blocked after ~1 hour: stop, ship `docker compose up` instructions + the demo video, and say in the README that the live demo is replay-only or absent. Never fake a URL.

## Done when
Live URL passes step 5, or the fallback is documented. STATE.md has the URLs and the date they were verified.
