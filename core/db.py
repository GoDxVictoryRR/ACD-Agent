"""
core/db.py — FalkorDB connection wrapper.

Uses the official falkordb Python client.
Reads connection params from core.config (which reads .env).
Provides ro() for read-only queries and rw() for writes.
Never logs passwords.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import falkordb  # type: ignore

from core.config import (
    FALKORDB_HOST,
    FALKORDB_PASSWORD,
    FALKORDB_PORT,
    FALKORDB_SSL,
    FALKORDB_USERNAME,
    QUERY_TIMEOUT_MS,
)

logger = logging.getLogger(__name__)

# Module-level client — created once; re-used across requests.
_client: falkordb.FalkorDB | None = None


def get_db() -> falkordb.FalkorDB:
    """Return the module-level FalkorDB client, creating it if needed."""
    global _client
    if _client is None:
        kwargs: dict[str, Any] = {
            "host": FALKORDB_HOST,
            "port": FALKORDB_PORT,
            "socket_connect_timeout": 2.0,
            "socket_timeout": 5.0,
        }
        if FALKORDB_USERNAME:
            kwargs["username"] = FALKORDB_USERNAME
        if FALKORDB_PASSWORD:
            kwargs["password"] = FALKORDB_PASSWORD
        if FALKORDB_SSL:
            kwargs["ssl"] = True
        # falkordb client constructor — check SDK for exact param names on install
        _client = falkordb.FalkorDB(**kwargs)
        logger.info("FalkorDB client created (host=%s port=%s ssl=%s)", FALKORDB_HOST, FALKORDB_PORT, FALKORDB_SSL)
    return _client


def graph(name: str) -> falkordb.Graph:
    """Return a Graph handle for the given graph name."""
    return get_db().select_graph(name)


def ro(
    graph_name: str,
    query: str,
    params: dict[str, Any] | None = None,
    timeout_ms: int = QUERY_TIMEOUT_MS,
) -> dict[str, Any]:
    """
    Execute a read-only query via GRAPH.RO_QUERY.
    Returns {"columns": [...], "rows": [...], "elapsed_ms": float}.
    Raises on error — callers must handle.
    """
    g = graph(graph_name)
    params = params or {}
    t0 = time.perf_counter()
    # ro_query is the safe read-only method; prevents writes
    result = g.ro_query(query, params, timeout=timeout_ms)
    elapsed = (time.perf_counter() - t0) * 1000

    columns: list[str] = result.header if hasattr(result, "header") else []
    rows: list[list[Any]] = [list(r) for r in result.result_set] if result.result_set else []

    return {"columns": columns, "rows": rows, "elapsed_ms": round(elapsed, 2)}


def rw(
    graph_name: str,
    query: str,
    params: dict[str, Any] | None = None,
    timeout_ms: int = QUERY_TIMEOUT_MS,
) -> dict[str, Any]:
    """
    Execute a read-write query via GRAPH.QUERY.
    Only use for record_decision and cluster_view scratch graph.
    Reads must use ro() instead.
    """
    g = graph(graph_name)
    params = params or {}
    t0 = time.perf_counter()
    result = g.query(query, params, timeout=timeout_ms)
    elapsed = (time.perf_counter() - t0) * 1000

    columns: list[str] = result.header if hasattr(result, "header") else []
    rows: list[list[Any]] = [list(r) for r in result.result_set] if result.result_set else []

    return {"columns": columns, "rows": rows, "elapsed_ms": round(elapsed, 2)}


def graph_exists(graph_name: str) -> bool:
    """Return True if the named graph exists in FalkorDB."""
    try:
        db = get_db()
        existing: list[str] = db.list_graphs()
        return graph_name in existing
    except Exception:
        return False


def drop_graph(graph_name: str) -> None:
    """Delete a graph. Used for scratch graphs and test teardown."""
    try:
        g = graph(graph_name)
        g.delete()
    except Exception as exc:
        logger.warning("drop_graph(%s) failed: %s", graph_name, exc)


def ping() -> bool:
    """Return True if FalkorDB is reachable."""
    global _client
    try:
        db = get_db()
        db.list_graphs()
        return True
    except Exception:
        _client = None
        return False
