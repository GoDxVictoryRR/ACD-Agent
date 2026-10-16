"""
api/main.py — FastAPI backend for ACD-Agent.

Features:
- Health check with RSS memory tracking and DB ping.
- Entity search autocomplete.
- SSE trace streaming of live investigations (/stream/{run_id}).
- Stored Case node retrieval.
- Saved replay retrieval.
- Startup self-seeding in background.
- In-memory rate limiting and concurrency throttling.
- Static web UI serving.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sys
import threading
import time
import uuid
from collections import defaultdict
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from agent.loop import run_investigation
from core import tools
from core.config import (
    ALLOWED_ORIGINS,
    CONCURRENT_INVESTIGATIONS,
    DATA_SOURCE,
    GRAPH_NAME,
    NVIDIA_API_KEY,
    RATE_LIMIT_INVESTIGATIONS_PER_HOUR,
)
from core.db import graph_exists, ping, ro
from data.load import ensure_seed, get_graph_counts

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# State flags
_seeding_in_progress = False
_runs_store: dict[str, dict[str, Any]] = {}
_runs_events: dict[str, list[dict[str, Any]]] = defaultdict(list)
_semaphore = asyncio.Semaphore(CONCURRENT_INVESTIGATIONS)

# Rate limiter: ip -> list of timestamps
_ip_rate_limits: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(client_ip: str) -> bool:
    now = time.time()
    one_hour_ago = now - 3600
    timestamps = [t for t in _ip_rate_limits[client_ip] if t > one_hour_ago]
    if len(timestamps) >= RATE_LIMIT_INVESTIGATIONS_PER_HOUR:
        return False
    timestamps.append(now)
    _ip_rate_limits[client_ip] = timestamps
    return True


def get_rss_mb() -> float:
    try:
        import psutil  # type: ignore
        proc = psutil.Process(os.getpid())
        return round(proc.memory_info().rss / (1024 * 1024), 1)
    except Exception:
        # Fallback without psutil
        return 0.0


def background_seed():
    global _seeding_in_progress
    _seeding_in_progress = True
    try:
        logger.info("Background self-seed started...")
        ensure_seed()
        logger.info("Background self-seed complete.")
    except Exception as exc:
        logger.warning("Background self-seed failed: %s", exc)
    finally:
        _seeding_in_progress = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: check if seeding is needed
    if ping():
        counts = get_graph_counts()
        if counts["nodes"] < 100:
            threading.Thread(target=background_seed, daemon=True).start()
    yield


app = FastAPI(
    title="Ownership Lens API",
    description="FalkorDB Offshore Ownership Graph Investigation API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — fix operator precedence
_origins = ALLOWED_ORIGINS[:]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InvestigateRequest(BaseModel):
    entity: str = Field(..., max_length=200)
    watchlist: list[str] = Field(default_factory=list, max_length=10)
    depth: int = Field(default=3, ge=1, le=4)  # default=3 matches demo depth
    no_llm: bool = False


@app.get("/health")
def health_check():
    db_ok = ping()
    graph_status = "missing"
    if db_ok:
        if _seeding_in_progress:
            graph_status = "seeding"
        elif graph_exists(GRAPH_NAME):
            counts = get_graph_counts(GRAPH_NAME)
            graph_status = "ready" if counts["nodes"] > 0 else "empty"

    has_llm = bool(NVIDIA_API_KEY and NVIDIA_API_KEY != "nvapi-...")
    # Data source disclaimer wording
    if DATA_SOURCE == "icij":
        data_disclaimer = "ICIJ Offshore Leaks (ODbL/CC BY-SA). Inclusion is not evidence of wrongdoing."
    else:
        data_disclaimer = "Synthetic demonstration data. No real persons or companies."
    return {
        "db": "ok" if db_ok else "down",
        "graph": graph_status,
        "llm_key": has_llm,
        "mode": "live" if db_ok else "replay-only",
        "data_source": DATA_SOURCE,
        "data_disclaimer": data_disclaimer,
        "rss_mb": get_rss_mb(),
    }


@app.get("/entities/search")
def search_entities(q: str = ""):
    query = q.strip()
    if not query:
        return []

    # Sanitize input: no control characters
    query = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", query)
    res = tools.resolve_entity(name=query, limit=5)
    return res.data


@app.get("/demo")
def get_demo_config():
    demo_file = REPO_ROOT / "data" / "demo.json"
    if demo_file.exists():
        with open(demo_file, encoding="utf-8") as f:
            return json.load(f)
    return {"demo_entities": [], "watchlist": []}


def execute_run(run_id: str, req: InvestigateRequest):
    # Store initial status
    _runs_events[run_id].append({"event": "status", "data": "Starting investigation..."})

    try:
        res = run_investigation(
            entity_name=req.entity,
            watchlist=req.watchlist,
            depth=req.depth,
            force_fallback=req.no_llm,
        )
        _runs_store[run_id] = res

        # Stream out trace steps
        for step in res.get("trace", []):
            _runs_events[run_id].append({"event": "step", "data": json.dumps(step)})

        # Stream out findings and verdict
        _runs_events[run_id].append({
            "event": "verdict",
            "data": json.dumps({
                "verdict": res.get("verdict"),
                "evaluation": res.get("evaluation"),
                "resolved_id": res.get("resolved_id"),
            }),
        })

        # Stream out memo
        _runs_events[run_id].append({
            "event": "memo",
            "data": json.dumps({
                "memo": res.get("memo"),
                "memo_source": res.get("memo_source"),
            }),
        })

        _runs_events[run_id].append({"event": "done", "data": json.dumps(res)})
    except Exception as exc:
        logger.exception("Investigation run failed: %s", exc)
        _runs_events[run_id].append({"event": "error", "data": str(exc)})


@app.post("/investigate")
async def start_investigation(
    req: InvestigateRequest,
    background_tasks: BackgroundTasks,
    request: Request,
):
    client_ip = request.client.host if request.client else "127.0.0.1"
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded (max {RATE_LIMIT_INVESTIGATIONS_PER_HOUR} per hour).",
        )

    if not ping():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="FalkorDB is unreachable. Cannot run graph investigation without primary database.",
        )

    # Sanitize entity name
    entity_name = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", req.entity).strip()
    if not entity_name:
        raise HTTPException(status_code=400, detail="Entity name cannot be empty.")

    run_id = f"run_{uuid.uuid4().hex[:12]}"
    background_tasks.add_task(execute_run, run_id, req)
    return {"run_id": run_id, "entity": entity_name, "depth": req.depth}


@app.get("/stream/{run_id}")
async def stream_investigation(run_id: str):
    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        sent_count = 0
        timeout_seconds = 60
        start_time = time.time()

        while True:
            events = _runs_events.get(run_id, [])
            while sent_count < len(events):
                ev = events[sent_count]
                yield {"event": ev["event"], "data": ev["data"]}
                sent_count += 1
                if ev["event"] in ("done", "error"):
                    return

            if time.time() - start_time > timeout_seconds:
                yield {"event": "error", "data": "Stream timeout."}
                return

            await asyncio.sleep(0.2)

    return EventSourceResponse(event_generator())


@app.get("/case/{case_id}")
def get_case(case_id: str):
    clean_id = re.sub(r"[^\w\-]+", "", case_id)
    q = """
    MATCH (c:Case {case_id: $case_id})
    OPTIONAL MATCH (c)-[:ABOUT]->(e:Entity)
    OPTIONAL MATCH (c)-[:CITED]->(cited)
    RETURN c.case_id AS id,
           c.verdict AS verdict,
           c.depth AS depth,
           c.memo AS memo,
           c.created_at AS created_at,
           e.name AS entity_name,
           collect(DISTINCT coalesce(cited.name, cited.address)) AS cited_nodes
    """
    try:
        res = ro(GRAPH_NAME, q, {"case_id": clean_id})
        rows = res.get("rows", [])
        if not rows:
            raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
        r = rows[0]
        return {
            "case_id": r[0],
            "verdict": r[1],
            "depth": r[2],
            "memo": r[3],
            "created_at": r[4],
            "entity_name": r[5],
            "cited_nodes": r[6],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/replay/{slug}")
def get_replay(slug: str):
    clean_slug = re.sub(r"[^\w\-]+", "", slug)
    replay_path = REPO_ROOT / "data" / "replay" / f"{clean_slug}.json"
    if not replay_path.exists():
        raise HTTPException(status_code=404, detail=f"Replay '{slug}' not found.")
    try:
        with open(replay_path, encoding="utf-8") as f:
            data = json.load(f)
        data["mode"] = "replay"
        return data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# Mount static web directory
WEB_DIR = REPO_ROOT / "web"
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
