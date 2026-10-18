"""Debug LLM investigation trace to find why evidence is not collected."""

import json
import logging
import sys

logging.basicConfig(level=logging.INFO)
sys.path.insert(0, r"C:\Users\hardi\Downloads\ACD-agent")

import os

os.environ["NO_LLM"] = "0"

# Monkey-patch loop to print trace
from agent import loop as loop_mod
from agent.llm import LLMClient
from core.rules import evaluate


def run_investigation_debug(entity_name, watchlist=None, depth=2):
    llm = LLMClient(enable_cache=False)
    watchlist = watchlist or []
    print(f"LLM available: {llm.is_available()}")

    evidence = {
        "resolved_entity": None,
        "ownership_chain": [],
        "shared_links": [],
        "paths_to_watchlist": [],
        "cluster_view": [],
        "recalled_cases": [],
    }
    tools_called = set()

    from agent.prompts import SYSTEM_PROMPT

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Investigate entity '{entity_name}' at depth {depth}. Watchlist: {watchlist}."},
    ]

    for turn in range(8):
        print(f"\n--- Turn {turn} ---")
        resp = llm.chat_completion(messages=messages, tools=loop_mod.TOOL_DEFINITIONS)
        choice = resp["choices"][0]["message"]
        tool_calls = choice.get("tool_calls")
        print(f"tool_calls present: {bool(tool_calls)}, count: {len(tool_calls) if tool_calls else 0}")
        print(f"content: {(choice.get('content') or '')[:100]!r}")

        messages.append(choice)

        if not tool_calls:
            print("No tool calls, stopping.")
            break

        for i, tc in enumerate(tool_calls):
            if hasattr(tc, "function"):
                func_name = tc.function.name
                raw_args = tc.function.arguments
                tc_id = getattr(tc, "id", None) or "tc_unknown"
            else:
                func_data = tc.get("function", {}) or {}
                func_name = func_data.get("name", "")
                raw_args = func_data.get("arguments")
                tc_id = tc.get("id") or "tc_unknown"

            print(f"  Tool call {i}: func_name={func_name!r}, raw_args={raw_args!r}")

            if not func_name:
                print("  Skipping empty func_name")
                continue

            # Parse args safely
            if raw_args is None:
                args = {}
            elif isinstance(raw_args, dict):
                args = raw_args
            else:
                try:
                    args = json.loads(raw_args)
                except Exception as e:
                    print(f"  Failed to parse args: {e}")
                    args = {}

            print(f"  Parsed args: {args}")

            result = loop_mod.execute_tool_call(func_name, args)
            tools_called.add(func_name)
            print(f"  Result status: {result.status}, data_len: {len(result.data) if result.data else 0}")

            if func_name == "resolve_entity" and result.status == "ok" and result.data:
                evidence["resolved_entity"] = result.data[0]
                print(f"  SET resolved_entity: {evidence['resolved_entity']}")
            elif func_name == "ownership_chain" and result.status == "ok":
                evidence["ownership_chain"].extend(result.data)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": f"<tool_output>\n{result.model_dump_json()}\n</tool_output>",
                }
            )

    print(f"\nFinal evidence['resolved_entity']: {evidence['resolved_entity']}")
    rules_eval = evaluate(evidence, max_depth=depth, watchlist=watchlist)
    print(f"Verdict: {rules_eval.verdict}")


watchlist = ["DOM Limited", "Beta Nominees Ltd"]
run_investigation_debug("GLAISDALE LIMITED", watchlist=watchlist, depth=3)
