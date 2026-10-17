"""
agent/fallback.py — Deterministic fallback investigation path.

Used when:
- NO_LLM=1
- NVIDIA API key is missing
- LLM rate limits out or fails twice
Executes the standard investigation sequence using core.mcp_client (MCP in live path with direct fallback).
"""

from __future__ import annotations

import logging
from typing import Any

from core import tools
from core.mcp_client import invoke_tool
from core.rules import evaluate
from core.verifier import generate_template_memo

logger = logging.getLogger(__name__)


def run_deterministic_investigation(
    entity_name: str,
    watchlist: list[str] | None = None,
    depth: int = 2,
    graph_name: str | None = None,
) -> dict[str, Any]:
    """
    Executes a structured, deterministic graph investigation.
    Returns standard result dictionary including trace, evidence, evaluation, and memo.
    All tool calls route through MCP with direct fallback; each trace entry marks via: mcp|direct.
    """
    trace: list[dict[str, Any]] = []
    evidence: dict[str, Any] = {
        "resolved_entity": None,
        "ownership_chain": [],
        "shared_links": [],
        "paths_to_watchlist": [],
        "cluster_view": [],
        "recalled_cases": [],
    }

    kwargs = {"graph_name": graph_name} if graph_name else {}

    # Step 1: Resolve entity
    res_entity, via_res = invoke_tool("resolve_entity", {"name": entity_name}, **kwargs)
    trace.append(
        {
            "tool": "resolve_entity",
            "params": {"name": entity_name},
            "status": res_entity.status,
            "elapsed_ms": res_entity.elapsed_ms,
            "source": "deterministic",
            "via": via_res,
        }
    )

    if res_entity.status != "ok" or not res_entity.data:
        eval_insufficient = evaluate(evidence, max_depth=depth, watchlist=watchlist)
        memo = generate_template_memo(entity_name, eval_insufficient, depth=depth)
        return {
            "entity_name": entity_name,
            "resolved_id": None,
            "verdict": eval_insufficient.verdict,
            "evaluation": eval_insufficient.model_dump(),
            "memo": memo,
            "memo_source": "template",
            "trace": trace,
            "evidence": evidence,
            "candidates": res_entity.data if res_entity.status == "ambiguous" else [],
            "status": res_entity.status,
        }

    resolved_node = res_entity.data[0]
    entity_id = resolved_node["id"]
    evidence["resolved_entity"] = resolved_node

    # Step 2: Ownership chain
    res_chain, via_chain = invoke_tool("ownership_chain", {"entity_id": entity_id, "max_depth": depth}, **kwargs)
    evidence["ownership_chain"] = res_chain.data
    trace.append(
        {
            "tool": "ownership_chain",
            "params": {"entity_id": entity_id, "max_depth": depth},
            "status": res_chain.status,
            "elapsed_ms": res_chain.elapsed_ms,
            "source": "deterministic",
            "via": via_chain,
        }
    )

    # Step 3: Shared links
    res_links, via_links = invoke_tool("shared_links", {"entity_id": entity_id}, **kwargs)
    evidence["shared_links"] = res_links.data
    trace.append(
        {
            "tool": "shared_links",
            "params": {"entity_id": entity_id},
            "status": res_links.status,
            "elapsed_ms": res_links.elapsed_ms,
            "source": "deterministic",
            "via": via_links,
        }
    )

    # Step 4: Check paths to watchlist items
    watchlist = watchlist or []
    for w in watchlist:
        # Resolve watchlist target node id
        res_w, via_w = invoke_tool("resolve_entity", {"name": w}, **kwargs)
        if res_w.status == "ok" and res_w.data:
            target_id = res_w.data[0]["id"]
            res_path, via_path = invoke_tool(
                "path_between",
                {
                    "a_id": entity_id,
                    "b_id": target_id,
                    "max_depth": depth,
                    "is_watchlist": True,
                    "watchlist": watchlist,
                },
                **kwargs,
            )
            trace.append(
                {
                    "tool": "path_between",
                    "params": {"a_id": entity_id, "b_id": target_id, "max_depth": depth},
                    "status": res_path.status,
                    "elapsed_ms": res_path.elapsed_ms,
                    "source": "deterministic",
                    "via": via_path,
                }
            )
            if res_path.status == "ok" and res_path.data:
                evidence["paths_to_watchlist"].extend(res_path.data)

    # Step 5: Cluster view (runs on 2-hop neighborhood for depth >= 2)
    if depth >= 2:
        res_cluster, via_cluster = invoke_tool(
            "cluster_view",
            {
                "entity_id": entity_id,
                "max_depth": min(depth, 2),
                "watchlist": watchlist,
            },
            **kwargs,
        )
        evidence["cluster_view"] = res_cluster.data
        trace.append(
            {
                "tool": "cluster_view",
                "params": {"entity_id": entity_id, "max_depth": min(depth, 2)},
                "status": res_cluster.status,
                "elapsed_ms": res_cluster.elapsed_ms,
                "source": "deterministic",
                "via": via_cluster,
            }
        )

    # Step 6: Rules evaluation
    rules_eval = evaluate(evidence, max_depth=depth, watchlist=watchlist)

    # Step 7: Record decision (write back Case node)
    evidence_ids: list[str] = []
    for f in rules_eval.findings:
        evidence_ids.extend(f.evidence_ids)

    rule_ids = [f.rule_id for f in rules_eval.findings]
    memo = generate_template_memo(resolved_node["name"], rules_eval, depth=depth)

    try:
        tools.record_decision(
            entity_id=entity_id,
            verdict=rules_eval.verdict,
            depth=depth,
            evidence_ids=evidence_ids,
            rule_ids=rule_ids,
            memo=memo,
            **kwargs,
        )
    except Exception as exc:
        logger.warning("Failed to record Case node: %s", exc)

    # Step 8: Recall prior cases
    res_cases, via_cases = invoke_tool("recall_cases", {"entity_id": entity_id}, **kwargs)
    evidence["recalled_cases"] = res_cases.data
    trace.append(
        {
            "tool": "recall_cases",
            "params": {"entity_id": entity_id},
            "status": res_cases.status,
            "elapsed_ms": res_cases.elapsed_ms,
            "source": "deterministic",
            "via": via_cases,
        }
    )

    return {
        "entity_name": entity_name,
        "resolved_id": entity_id,
        "verdict": rules_eval.verdict,
        "evaluation": rules_eval.model_dump(),
        "memo": memo,
        "memo_source": "template",
        "trace": trace,
        "evidence": evidence,
        "candidates": [],
        "status": "ok",
    }
