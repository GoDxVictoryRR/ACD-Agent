"""
scripts/bench_models.py — Benchmark NVIDIA models for tool-calling accuracy.
Evaluates 10 canned tool-call prompts across 6 read-tool schemas.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from openai import OpenAI

from core.config import NVIDIA_API_KEY, NVIDIA_BASE_URL

# The 6 read-tool schemas
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

# 10 canned tool-call prompts
TEST_PROMPTS = [
    {
        "id": 1,
        "prompt": "Investigate entity GLAISDALE LIMITED.",
        "expected_tool": "resolve_entity",
        "expected_arg": "name",
    },
    {
        "id": 2,
        "prompt": "Find the node identifier for DOM Limited.",
        "expected_tool": "resolve_entity",
        "expected_arg": "name",
    },
    {
        "id": 3,
        "prompt": "Trace ownership and shareholder connections for entity node 10001171 at depth 2.",
        "expected_tool": "ownership_chain",
        "expected_arg": "entity_id",
    },
    {
        "id": 4,
        "prompt": "Retrieve corporate control chain for entity 10005699 up to depth 3.",
        "expected_tool": "ownership_chain",
        "expected_arg": "entity_id",
    },
    {
        "id": 5,
        "prompt": "Identify shared officers and intermediaries connected to entity 10001171.",
        "expected_tool": "shared_links",
        "expected_arg": "entity_id",
    },
    {
        "id": 6,
        "prompt": "Check hub addresses and nominee officers for node 10000001.",
        "expected_tool": "shared_links",
        "expected_arg": "entity_id",
    },
    {
        "id": 7,
        "prompt": "Find the shortest control path between node 10001171 and node 10000001.",
        "expected_tool": "path_between",
        "expected_arg": "a_id",
    },
    {
        "id": 8,
        "prompt": "Is there an ownership path from source 10005699 to target 10000001?",
        "expected_tool": "path_between",
        "expected_arg": "a_id",
    },
    {
        "id": 9,
        "prompt": "Compute centrality metrics, PageRank and betweenness for the neighborhood around entity 10001171.",
        "expected_tool": "cluster_view",
        "expected_arg": "entity_id",
    },
    {
        "id": 10,
        "prompt": "Recall previous compliance case verdicts and historical decisions for entity 10001171.",
        "expected_tool": "recall_cases",
        "expected_arg": "entity_id",
    },
]

CANDIDATE_MODELS = [
    "nvidia/llama-3.3-nemotron-super-49b-v1.5",
    "nvidia/nemotron-3-super-120b-a12b",
    "poolside/laguna-xs-2.1",
]


def run_benchmark():
    if not NVIDIA_API_KEY:
        print("ERROR: NVIDIA_API_KEY is not set.")
        sys.exit(1)

    client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_API_KEY, timeout=15.0, max_retries=0)
    results = {}

    print("=" * 70)
    print("NVIDIA MODEL TOOL-CALLING BENCHMARK (10 Prompts x 6 Schemas)")
    print("=" * 70)

    for model in CANDIDATE_MODELS:
        print(f"\nBenchmarking Model: {model}")
        model_results = []
        correct_count = 0

        for item in TEST_PROMPTS:
            pid = item["id"]
            user_msg = item["prompt"]
            exp_tool = item["expected_tool"]
            exp_arg = item["expected_arg"]

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an offshore network investigator. Use the available tools "
                        "to inspect nodes, ownership chains, shared hubs, paths, clusters, and prior cases."
                    ),
                },
                {"role": "user", "content": user_msg},
            ]

            t0 = time.perf_counter()
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto",
                    max_tokens=256,
                    temperature=0.1,
                )
                elapsed_ms = (time.perf_counter() - t0) * 1000
                msg = resp.choices[0].message
                tool_calls = getattr(msg, "tool_calls", None) or []

                if tool_calls:
                    tc = tool_calls[0]
                    t_name = tc.function.name
                    raw_args = tc.function.arguments
                    try:
                        parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                    except Exception:
                        parsed_args = {}

                    tool_match = t_name == exp_tool
                    arg_match = exp_arg in parsed_args if isinstance(parsed_args, dict) else False
                    is_correct = tool_match and arg_match

                    if is_correct:
                        correct_count += 1
                        status = "PASS"
                    else:
                        status = "PARTIAL"

                    model_results.append(
                        {
                            "prompt_id": pid,
                            "prompt": user_msg,
                            "status": status,
                            "latency_ms": round(elapsed_ms, 1),
                            "tool_called": t_name,
                            "expected_tool": exp_tool,
                            "args": parsed_args,
                            "correct": is_correct,
                        }
                    )
                    print(
                        f"  [{pid:2d}/10] {status:7s} | {elapsed_ms:6.0f}ms | called {t_name}({list(parsed_args.keys())})"
                    )
                else:
                    content_snippet = (msg.content or "").strip().replace("\n", " ")[:60]
                    model_results.append(
                        {
                            "prompt_id": pid,
                            "prompt": user_msg,
                            "status": "NO_TOOL",
                            "latency_ms": round(elapsed_ms, 1),
                            "tool_called": None,
                            "expected_tool": exp_tool,
                            "args": None,
                            "correct": False,
                            "content": content_snippet,
                        }
                    )
                    print(f"  [{pid:2d}/10] NO_TOOL | {elapsed_ms:6.0f}ms | content: {content_snippet}")

            except Exception as e:
                elapsed_ms = (time.perf_counter() - t0) * 1000
                err_str = str(e)
                model_results.append(
                    {
                        "prompt_id": pid,
                        "prompt": user_msg,
                        "status": "FAIL",
                        "latency_ms": round(elapsed_ms, 1),
                        "tool_called": None,
                        "expected_tool": exp_tool,
                        "args": None,
                        "correct": False,
                        "error": err_str,
                    }
                )
                print(f"  [{pid:2d}/10] FAIL    | {elapsed_ms:6.0f}ms | {err_str[:60]}")
                time.sleep(0.5)

        results[model] = {
            "correct_count": correct_count,
            "total": len(TEST_PROMPTS),
            "accuracy": f"{correct_count}/{len(TEST_PROMPTS)}",
            "details": model_results,
        }

    # Generate Markdown Report
    md = [
        "# Model Benchmark: Tool Calling Accuracy",
        "",
        "Evaluation of candidate NVIDIA-hosted text models on 10 canned corporate investigation prompts "
        "using 6 typed read-tool schemas from `core/tools.py`.",
        "",
        "## Summary Table",
        "",
        "| Model Name | Type | Tool Calls Correct | Accuracy | Mean Latency | Status |",
        "|---|---|:---:|:---:|:---:|---|",
    ]

    best_model = None
    max_correct = -1

    for model, data in results.items():
        details = data["details"]
        valid_latencies = [d["latency_ms"] for d in details if d["status"] != "FAIL"]
        mean_lat = f"{sum(valid_latencies) / len(valid_latencies):.0f} ms" if valid_latencies else "N/A"
        c = data["correct_count"]
        tot = data["total"]
        pct = (c / tot) * 100

        if "410" in str(details[0].get("error", "")):
            stat = "FAIL (410 Gone / EOL)"
        elif c >= 7:
            stat = "**PASS** (Meets >= 7/10 Threshold)"
            if c > max_correct:
                max_correct = c
                best_model = model
        else:
            stat = "PARTIAL (Below 7/10)"

        md.append(f"| `{model}` | Text | {c}/{tot} | {pct:.1f}% | {mean_lat} | {stat} |")

    md.extend(
        [
            "",
            "## Detailed Evaluation Per Prompt",
            "",
        ]
    )

    for model, data in results.items():
        md.append(f"### Model: `{model}`")
        md.append(f"**Score**: {data['correct_count']}/10 correct")
        md.append("")
        md.append("| # | Prompt | Expected Tool | Result | Called Tool | Latency |")
        md.append("|---|---|---|---|---|:---:|")
        for d in data["details"]:
            tc = d.get("tool_called") or "None"
            st = d["status"]
            lat = f"{d['latency_ms']:.0f} ms"
            md.append(f"| {d['prompt_id']} | {d['prompt'][:45]}... | `{d['expected_tool']}` | {st} | `{tc}` | {lat} |")
        md.append("")

    md.extend(
        [
            "## Recommendation & Decision",
            "",
            f"- **Selected Primary Text Model**: `{best_model if best_model else 'None (Fallback Mode)'}`",
            f"- **Vision Model Replacement**: Replaced deprecated `meta/llama-3.2-11b-vision-instruct` with dedicated text model `{best_model if best_model else 'deepseek-ai/deepseek-v4.1-flash'}`.",
            "- **Fallback Guarantee**: Invariant 11 fallback to `agent/fallback.py` operates deterministically if NVIDIA API returns 429, timeout, or invalid format.",
            "",
            f"*Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}*",
        ]
    )

    report_content = "\n".join(md)
    out_path = REPO_ROOT / "docs" / "model_bench.md"
    out_path.write_text(report_content, encoding="utf-8")
    print(f"\nSaved model benchmark to {out_path}")

    return best_model, results


if __name__ == "__main__":
    run_benchmark()
