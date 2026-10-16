"""
agent/loop.py — Agent investigation loop.

Features:
- Translates core tools into OpenAI tool calling schemas (six read tools only).
- Runs multi-turn loop with LLM until stop or call cap (Invariant 11).
- Coverage check: runs any missing required tools deterministically (marked source: forced).
- Deterministic rules layer determines the verdict (Invariant 5).
- Calls record_decision after verdict, then recall_cases.
- Verifier checks the LLM memo; replaces with template if hallucinated (Invariant 6).
- Falls back to agent.fallback if LLM is unavailable or fails twice.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from agent.fallback import run_deterministic_investigation
from agent.llm import LLMClient
from agent.prompts import MEMO_PROMPT_TEMPLATE, SYSTEM_PROMPT
from core import tools
from core.rules import evaluate
from core.verifier import generate_template_memo, verify_memo

logger = logging.getLogger(__name__)

# The 6 read tools exposed to the LLM (record_decision is deliberately omitted per Invariant 1)
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "resolve_entity",
            "description": "Look up an entity by name to obtain its unique node_id. Must be called first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Entity name to resolve"},
                    "limit": {"type": "integer", "description": "Max candidates (1-5)", "default": 5},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ownership_chain",
            "description": "Traverse ownership, control, and shareholder connections from an entity up to depth 3.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {"type": "string", "description": "Node ID of the entity"},
                    "max_depth": {"type": "integer", "description": "Traversal depth (1-3)", "default": 2},
                },
                "required": ["entity_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "shared_links",
            "description": "Identify connected hubs (officers, addresses, intermediaries) and how many other entities they touch.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {"type": "string", "description": "Node ID of the entity"},
                    "limit": {"type": "integer", "description": "Max hubs to return", "default": 10},
                },
                "required": ["entity_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "path_between",
            "description": "Find shortest weighted path between two entities within max_depth.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a_id": {"type": "string", "description": "Source node ID"},
                    "b_id": {"type": "string", "description": "Target node ID"},
                    "max_depth": {"type": "integer", "description": "Max hops (1-3)", "default": 3},
                },
                "required": ["a_id", "b_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cluster_view",
            "description": "Compute network centrality metrics (PageRank, Betweenness, Communities) on the entity's neighborhood.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {"type": "string", "description": "Node ID of the entity"},
                    "max_depth": {"type": "integer", "description": "Neighborhood depth (1-2)", "default": 2},
                },
                "required": ["entity_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recall_cases",
            "description": "Retrieve previous case decisions connected to this entity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {"type": "string", "description": "Node ID of the entity"},
                },
                "required": ["entity_id"],
            },
        },
    },
]


def execute_tool_call(name: str, args: dict[str, Any], graph_name: str | None = None) -> tools.ToolResult:
    kwargs = {"graph_name": graph_name} if graph_name else {}

    # LLMs sometimes return int-typed schema args as strings; coerce defensively
    def _int(v: Any, default: int) -> int:
        try:
            return int(v)
        except (TypeError, ValueError):
            return default

    if name == "resolve_entity":
        return tools.resolve_entity(name=args.get("name", ""), limit=_int(args.get("limit"), 5), **kwargs)
    elif name == "ownership_chain":
        return tools.ownership_chain(entity_id=args.get("entity_id", ""), max_depth=_int(args.get("max_depth"), 2), **kwargs)
    elif name == "shared_links":
        return tools.shared_links(entity_id=args.get("entity_id", ""), limit=_int(args.get("limit"), 10), **kwargs)
    elif name == "path_between":
        return tools.path_between(a_id=args.get("a_id", ""), b_id=args.get("b_id", ""), max_depth=_int(args.get("max_depth"), 3), **kwargs)
    elif name == "cluster_view":
        return tools.cluster_view(entity_id=args.get("entity_id", ""), max_depth=_int(args.get("max_depth"), 2), **kwargs)
    elif name == "recall_cases":
        return tools.recall_cases(entity_id=args.get("entity_id", ""), limit=_int(args.get("limit"), 5), **kwargs)
    else:
        return tools.ToolResult(tool=name, status="error", notes=f"Unknown tool '{name}'")


def run_investigation(
    entity_name: str,
    watchlist: list[str] | None = None,
    depth: int = 2,
    graph_name: str | None = None,
    force_fallback: bool = False,
) -> dict[str, Any]:
    llm = LLMClient()
    watchlist = watchlist or []

    # If LLM disabled or not configured, use fallback immediately
    if force_fallback or not llm.is_available():
        logger.info("Running deterministic investigation (no LLM)")
        return run_deterministic_investigation(
            entity_name=entity_name,
            watchlist=watchlist,
            depth=depth,
            graph_name=graph_name,
        )

    trace: list[dict[str, Any]] = []
    evidence: dict[str, Any] = {
        "resolved_entity": None,
        "ownership_chain": [],
        "shared_links": [],
        "paths_to_watchlist": [],
        "cluster_view": [],
        "recalled_cases": [],
    }

    tools_called: set[str] = set()
    kwargs = {"graph_name": graph_name} if graph_name else {}

    # ── INVARIANT 4: resolve_entity always runs first, deterministically ──────
    # The LLM is NOT trusted to call this correctly — some smaller models
    # hallucinate entity_id values. We resolve here and inject the grounded
    # entity_id into the conversation context.
    res_entity = tools.resolve_entity(name=entity_name, **kwargs)
    trace.append({
        "tool": "resolve_entity",
        "params": {"name": entity_name},
        "status": res_entity.status,
        "elapsed_ms": res_entity.elapsed_ms,
        "source": "forced",  # always forced, per Invariant 4
    })

    if res_entity.status != "ok" or not res_entity.data:
        rules_eval = evaluate(evidence, max_depth=depth, watchlist=watchlist)
        memo = generate_template_memo(entity_name, rules_eval, depth=depth)
        return {
            "entity_name": entity_name,
            "resolved_id": None,
            "verdict": rules_eval.verdict,
            "evaluation": rules_eval.model_dump(),
            "memo": memo,
            "memo_source": "template",
            "trace": trace,
            "evidence": evidence,
        }

    resolved = res_entity.data[0]
    entity_id = resolved["id"]
    evidence["resolved_entity"] = resolved
    tools_called.add("resolve_entity")

    # Give the LLM full grounded context: entity_id, name, depth, watchlist
    user_msg = (
        f"Investigate entity '{entity_name}' (node_id: '{entity_id}') at depth {depth}.\n"
        f"Watchlist targets: {watchlist}.\n"
        f"resolve_entity already ran: entity_id='{entity_id}', name='{resolved.get('name', entity_name)}'. "
        f"Now use the other tools with entity_id='{entity_id}' to collect evidence."
    )

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]

    try:
        # Multi-turn tool calling loop (remaining exploration tools)
        for turn in range(7):  # max 7 more turns (resolve used 1 of 8 budget)
            resp = llm.chat_completion(messages=messages, tools=TOOL_DEFINITIONS)
            choice = resp["choices"][0]["message"]
            messages.append(choice)

            tool_calls = choice.get("tool_calls")
            if not tool_calls:
                break

            for tc in tool_calls:
                # Support both model_dump dict format and raw object format
                if hasattr(tc, "function"):
                    func_name = tc.function.name
                    raw_args_str = tc.function.arguments
                    tc_id = getattr(tc, "id", None) or "tc_unknown"
                else:
                    func_data = tc.get("function", {}) or {}
                    func_name = func_data.get("name", "")
                    raw_args_str = func_data.get("arguments")
                    tc_id = tc.get("id") or "tc_unknown"

                if not func_name:
                    continue

                # Parse args safely — LLMs sometimes skip arguments entirely
                if raw_args_str is None:
                    args: dict[str, Any] = {}
                elif isinstance(raw_args_str, dict):
                    args = raw_args_str
                else:
                    try:
                        args = json.loads(raw_args_str)
                    except Exception:
                        args = {}

                # Override entity_id if the LLM hallucinated it (Invariant 4 safety net)
                if func_name in ("ownership_chain", "shared_links", "cluster_view", "recall_cases"):
                    llm_entity_id = args.get("entity_id", "")
                    # Reject if entity_id is clearly wrong (a tool name or empty)
                    if not llm_entity_id or llm_entity_id in {t["function"]["name"] for t in TOOL_DEFINITIONS}:
                        logger.warning("LLM provided invalid entity_id %r for %s; overriding with %r",
                                       llm_entity_id, func_name, entity_id)
                        args["entity_id"] = entity_id
                elif func_name == "path_between":
                    if not args.get("a_id"):
                        args["a_id"] = entity_id

                # Skip if LLM re-calls resolve_entity (budget already used)
                if func_name == "resolve_entity":
                    logger.debug("LLM re-called resolve_entity; using cached result")
                    result = res_entity
                else:
                    result = execute_tool_call(func_name, args, graph_name=graph_name)
                tools_called.add(func_name)

                trace.append({
                    "tool": func_name,
                    "params": args,
                    "status": result.status,
                    "elapsed_ms": result.elapsed_ms,
                    "source": "llm",
                })

                # Ingest evidence
                if func_name == "resolve_entity" and result.status == "ok" and result.data:
                    evidence["resolved_entity"] = result.data[0]
                elif func_name == "ownership_chain" and result.status == "ok":
                    evidence["ownership_chain"].extend(result.data)
                elif func_name == "shared_links" and result.status == "ok":
                    evidence["shared_links"].extend(result.data)
                elif func_name == "path_between" and result.status == "ok":
                    evidence["paths_to_watchlist"].extend(result.data)
                elif func_name == "cluster_view" and result.status == "ok":
                    evidence["cluster_view"].extend(result.data)

                # Send tool output back inside <tool_output> tags per Invariant 7
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": f"<tool_output>\n{result.model_dump_json()}\n</tool_output>",
                })

    except Exception as exc:
        logger.warning("LLM agent loop error: %s. Switching to fallback.", exc)
        return run_deterministic_investigation(
            entity_name=entity_name,
            watchlist=watchlist,
            depth=depth,
            graph_name=graph_name,
        )

    # Coverage check: ensure all required tools were executed.
    # Note: resolve_entity + entity_id are always set above (Invariant 4).

    if "ownership_chain" not in tools_called:
        res_chain = tools.ownership_chain(entity_id=entity_id, max_depth=depth, **kwargs)
        evidence["ownership_chain"].extend(res_chain.data)
        trace.append({
            "tool": "ownership_chain",
            "params": {"entity_id": entity_id, "max_depth": depth},
            "status": res_chain.status,
            "elapsed_ms": res_chain.elapsed_ms,
            "source": "forced",
        })

    if "shared_links" not in tools_called:
        res_links = tools.shared_links(entity_id=entity_id, **kwargs)
        evidence["shared_links"].extend(res_links.data)
        trace.append({
            "tool": "shared_links",
            "params": {"entity_id": entity_id},
            "status": res_links.status,
            "elapsed_ms": res_links.elapsed_ms,
            "source": "forced",
        })

    # Ensure path_between was run for each watchlist target
    for w in watchlist:
        res_w = tools.resolve_entity(name=w, **kwargs)
        if res_w.status == "ok" and res_w.data:
            target_id = res_w.data[0]["id"]
            if not any(tc.get("params", {}).get("b_id") == target_id for tc in trace if tc["tool"] == "path_between"):
                res_path = tools.path_between(a_id=entity_id, b_id=target_id, max_depth=depth, **kwargs)
                trace.append({
                    "tool": "path_between",
                    "params": {"a_id": entity_id, "b_id": target_id, "max_depth": depth},
                    "status": res_path.status,
                    "elapsed_ms": res_path.elapsed_ms,
                    "source": "forced",
                })
                if res_path.status == "ok" and res_path.data:
                    evidence["paths_to_watchlist"].extend(res_path.data)

    if "cluster_view" not in tools_called:
        res_cluster = tools.cluster_view(entity_id=entity_id, max_depth=min(depth, 2), **kwargs)
        evidence["cluster_view"].extend(res_cluster.data)
        trace.append({
            "tool": "cluster_view",
            "params": {"entity_id": entity_id, "max_depth": min(depth, 2)},
            "status": res_cluster.status,
            "elapsed_ms": res_cluster.elapsed_ms,
            "source": "forced",
        })

    # Step: Rules evaluation (Deterministic verdict)
    rules_eval = evaluate(evidence, max_depth=depth, watchlist=watchlist)

    # Step: Generate Memo with LLM and verify with verifier
    evidence_ledger_json = json.dumps({
        "findings": [f.model_dump() for f in rules_eval.findings],
        "verdict": rules_eval.verdict,
        "total_links": rules_eval.total_links,
    }, indent=2)

    memo_prompt = MEMO_PROMPT_TEMPLATE.format(
        entity_name=resolved["name"],
        depth=depth,
        verdict=rules_eval.verdict.upper(),
        evidence_ledger_json=evidence_ledger_json,
    )

    memo = ""
    memo_source = "llm"
    try:
        memo_resp = llm.chat_completion(messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": memo_prompt},
        ])
        candidate_memo = memo_resp["choices"][0]["message"]["content"]
        is_valid, unverified = verify_memo(candidate_memo, evidence)
        if is_valid:
            memo = candidate_memo
        else:
            logger.warning("Memo verification failed (unverified: %s). Reverting to template.", unverified)
            memo = generate_template_memo(resolved["name"], rules_eval, depth=depth)
            memo_source = "template"
    except Exception as me:
        logger.warning("Memo generation failed: %s. Using template.", me)
        memo = generate_template_memo(resolved["name"], rules_eval, depth=depth)
        memo_source = "template"

    # Step: Record decision write-back
    evidence_ids: list[str] = []
    for f in rules_eval.findings:
        evidence_ids.extend(f.evidence_ids)

    rule_ids = [f.rule_id for f in rules_eval.findings]
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

    # Step: Recall prior cases
    res_cases = tools.recall_cases(entity_id=entity_id, **kwargs)
    evidence["recalled_cases"] = res_cases.data
    trace.append({
        "tool": "recall_cases",
        "params": {"entity_id": entity_id},
        "status": res_cases.status,
        "elapsed_ms": res_cases.elapsed_ms,
        "source": "forced",
    })

    return {
        "entity_name": resolved["name"],
        "resolved_id": entity_id,
        "verdict": rules_eval.verdict,
        "evaluation": rules_eval.model_dump(),
        "memo": memo,
        "memo_source": memo_source,
        "trace": trace,
        "evidence": evidence,
    }
