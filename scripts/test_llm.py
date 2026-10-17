"""Test NVIDIA LLM API with a real call."""

import json
import sys
import time

sys.path.insert(0, r"C:\Users\hardi\Downloads\ACD-agent")

from agent.llm import NVIDIA_MODEL, LLMClient

print(f"Testing NVIDIA LLM model: {NVIDIA_MODEL}")
client = LLMClient(enable_cache=False)
print(f"Client available: {client.is_available()}")

messages = [
    {"role": "system", "content": "You are a brief assistant. Reply with exactly 3 words."},
    {"role": "user", "content": "Say: LLM test passed"},
]

t0 = time.perf_counter()
try:
    resp = client.chat_completion(messages=messages, tools=None)
    elapsed = (time.perf_counter() - t0) * 1000
    choices = resp.get("choices", [])
    if choices:
        content = choices[0].get("message", {}).get("content", "")
        print(f"Response ({elapsed:.0f}ms): {content!r}")
        print("PASS: LLM call succeeded")
    else:
        print("FAIL: No choices in response")
        print(json.dumps(resp, indent=2)[:500])
except Exception as e:
    elapsed = (time.perf_counter() - t0) * 1000
    print(f"FAIL: LLM call raised after {elapsed:.0f}ms: {e}")
