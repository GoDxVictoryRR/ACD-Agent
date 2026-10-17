"""Verify LLM failure modes:
1. Invalid API key -> falls back to deterministic investigation cleanly
2. Simulated 429 -> retries and/or falls back gracefully
3. Malformed tool args -> handled cleanly, does not crash
4. LLM timeout -> caught and falls back to deterministic
All end with valid verdict and template memo.
"""

import os
import unittest.mock as mock

from agent.loop import run_investigation

ENTITY = "Blue Star Maritime Holdings Ltd"
WATCHLIST = ["Ironclad Sanctions Entity Inc", "Apex Nominees Ltd"]

print("=== 1. Testing Invalid API Key ===")
with mock.patch("agent.llm.NVIDIA_API_KEY", "dummy-invalid-key"):
    with mock.patch.dict(os.environ, {"NVIDIA_API_KEY": "dummy-invalid-key"}):
        res = run_investigation(ENTITY, watchlist=WATCHLIST, depth=3)
        assert res["verdict"] == "escalate"
        assert res["memo_source"] == "template"
        print(f"[PASS] Invalid key handled: verdict={res['verdict']}, memo_source={res['memo_source']}")

print("\n=== 2. Testing Simulated 429 Rate Limit ===")
import httpx
from openai import RateLimitError

fake_response = httpx.Response(429, request=httpx.Request("POST", "http://test"))
err_429 = RateLimitError("Rate limit exceeded", response=fake_response, body={"message": "Too many requests"})

with mock.patch("agent.llm.LLMClient.chat_completion", side_effect=err_429):
    res = run_investigation(ENTITY, watchlist=WATCHLIST, depth=3)
    assert res["verdict"] == "escalate"
    assert res["memo_source"] == "template"
    print(f"[PASS] Simulated 429 handled: verdict={res['verdict']}, memo_source={res['memo_source']}")

print("\n=== 3. Testing Malformed Tool Args from LLM ===")
# Simulate LLM returning a tool call with unparseable JSON arguments
fake_malformed_choice = {
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "ownership_chain", "arguments": "{invalid json: true, broken...}"},
                    }
                ],
            }
        }
    ]
}

with mock.patch("agent.llm.LLMClient.chat_completion", return_value=fake_malformed_choice):
    res = run_investigation(ENTITY, watchlist=WATCHLIST, depth=3)
    assert res["verdict"] in ("escalate", "clear", "review", "insufficient_evidence")
    print(f"[PASS] Malformed tool args handled gracefully: verdict={res['verdict']}")

print("\n=== 4. Testing LLM Timeout ===")
with mock.patch("agent.llm.LLMClient.chat_completion", side_effect=TimeoutError("API request timed out")):
    res = run_investigation(ENTITY, watchlist=WATCHLIST, depth=3)
    assert res["verdict"] == "escalate"
    assert res["memo_source"] == "template"
    print(f"[PASS] Timeout handled: verdict={res['verdict']}, memo_source={res['memo_source']}")

print("\nOVERALL: ALL LLM FAILURE MODES VERIFIED (PASS)")
