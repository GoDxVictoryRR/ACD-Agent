"""Benchmark NVIDIA models for tool calling quality."""
import sys
import time

sys.path.insert(0, r"C:\Users\hardi\Downloads\ACD-agent")

from openai import OpenAI

from core.config import NVIDIA_API_KEY, NVIDIA_BASE_URL

client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_API_KEY)

# Simple tool calling test
tools = [
    {
        "type": "function",
        "function": {
            "name": "resolve_entity",
            "description": "Resolve entity name to node_id",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Entity name to resolve"}
                },
                "required": ["name"]
            }
        }
    }
]

messages = [
    {"role": "system", "content": "You are an investigation agent. Use tools to investigate entities. Start by resolving the entity."},
    {"role": "user", "content": "Investigate: Blue Star Maritime Holdings Ltd"}
]

candidates = [
    "nvidia/llama-3.1-nemotron-70b-instruct",
    "nvidia/llama-3.1-nemotron-51b-instruct",
    "mistralai/mistral-large",
    "mistralai/mistral-large-2-instruct",
    "meta/llama-3.2-11b-vision-instruct",
]

print("=== Model Benchmark: Tool Calling ===")
results = []
for model in candidates:
    t0 = time.perf_counter()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=256,
        )
        elapsed = (time.perf_counter() - t0) * 1000
        choice = resp.choices[0]
        msg = choice.message
        tool_calls = getattr(msg, "tool_calls", None) or []
        has_tool_call = bool(tool_calls)
        tool_name = tool_calls[0].function.name if tool_calls else None
        tool_args = tool_calls[0].function.arguments if tool_calls else None
        content = msg.content or ""
        status = "PASS" if has_tool_call else "PARTIAL"
        results.append((model, elapsed, status, tool_name, tool_args, content[:80]))
        print(f"  {status} | {elapsed:6.0f}ms | {model}")
        if has_tool_call:
            print(f"    tool_call: {tool_name}({tool_args})")
        else:
            print(f"    no tool call, content: {content[:80]!r}")
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"  FAIL   | {elapsed:6.0f}ms | {model}: {e}")
        results.append((model, elapsed, "FAIL", None, None, str(e)[:80]))

print()
print("=== Results Summary ===")
for model, elapsed, status, tool_name, args, _ in results:
    print(f"  {status:7s} | {elapsed:6.0f}ms | {model}")

# Best model = first PASS, then PARTIAL
best = next((r for r in results if r[2] == "PASS"), None)
if not best:
    best = next((r for r in results if r[2] == "PARTIAL"), None)
print()
if best:
    print(f"RECOMMENDED: {best[0]}")
else:
    print("No suitable model found")
