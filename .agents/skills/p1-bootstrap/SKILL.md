---
name: p1-bootstrap
description: "Creates the repo skeleton, lean dependency files, Docker Compose FalkorDB, the DB wrapper, a Cypher CLI and a passing smoke test. Use once after p0 group A."
---

# p1: bootstrap

Do in order. Commit after each numbered step.

1. **Skeleton.** Create the layout from `main.md` (empty packages with `__init__.py`). `.gitignore`: `.env`, `data/raw/`, `.venv/`, `__pycache__/`, `.falkordb-data/`, `cache/`. `.env.example`: `NVIDIA_API_KEY`, `NVIDIA_MODEL`, `FALKORDB_HOST=localhost`, `FALKORDB_PORT=6379`, `FALKORDB_USERNAME`, `FALKORDB_PASSWORD`, `FALKORDB_SSL=false`, `GRAPH_NAME=ownership`, `ALLOWED_ORIGINS`, `DAILY_LLM_CAP=300`.
2. **Dependencies.** `requirements.txt` (runtime only): `falkordb`, `mcp`, `openai`, `fastapi`, `uvicorn[standard]`, `pydantic>=2`, `python-dotenv`. `requirements-dev.txt`: `pytest`, `ruff`, `httpx`. Create `.venv`, install both. No pandas.
3. **FalkorDB.** `docker-compose.yml` with two services:
   - `falkordb`: image `falkordb/falkordb-server:latest`, port `6379:6379` only (server-only image, no Browser). Volume: `falkordb_data:/data` (verified path from https://docs.falkordb.com/operations/docker). Env: `REDIS_ARGS=--appendonly yes` for durability. Healthcheck: `redis-cli ping`.
   - `falkordb-browser` (optional, dev only): image `falkordb/falkordb-browser:latest`, port `3001:3000` (remapped to 3001 to avoid conflicts), env `FALKORDB_URL=redis://falkordb:6379`, `depends_on: falkordb`.
   - **Why server-only image for main service:** the combined `falkordb/falkordb:latest` also binds port 3000 inside the container, which conflicts if any other service (e.g. MCP HTTP mode or local dev tools) uses host port 3000. Always use the server-only image in the project stack.
   Run `docker compose up -d`.
4. **`core/db.py`.** Reads env; `get_db()`; `graph(name)`; `ro(graph_name, query, params, timeout_ms)` using `ro_query`, returning `{columns, rows, elapsed_ms}`; `rw(...)` for the few write paths. Support `FALKORDB_SSL` and username/password. Set a per-query timeout if the client supports it (check). Never log passwords.
5. **`scripts/q.py`.** Dev CLI: `python scripts/q.py "MATCH (n) RETURN count(n)" [--graph NAME] [--write]`. Prints rows and elapsed ms. Read-only by default.
6. **Smoke test `tests/test_smoke.py`.** Create graph `smoke`, add two nodes + an edge, read them back with `ro_query`, delete the graph. `pytest -q` must pass.
7. **Browser check.** Confirm http://localhost:3000 loads. If not, note it in `STATE.md`; not blocking.
8. **STATE.md.** Create with sections: current phase, done, decisions, open issues, HUMAN ACTIONS pending. Mark p1 done.

## Done when
`docker compose up -d` + `pytest -q` pass from a fresh clone and `.env.example` is complete.
