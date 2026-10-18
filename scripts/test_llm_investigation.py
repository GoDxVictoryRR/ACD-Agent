"""Test full LLM investigation pipeline (not NO_LLM)."""

import sys

sys.path.insert(0, r"C:\Users\hardi\Downloads\ACD-agent")

# Override env before imports
import os

os.environ["NO_LLM"] = "0"

from agent.loop import run_investigation

print("=== Full LLM Investigation: GLAISDALE LIMITED ===")
print()

watchlist = ["DOM Limited", "Beta Nominees Ltd"]

try:
    result = run_investigation(
        entity_name="GLAISDALE LIMITED",
        watchlist=watchlist,
        depth=3,
        force_fallback=False,
    )
    print(f"Verdict: {result['verdict']!r}")
    print(f"Memo source: {result.get('memo_source')!r}")
    rules = [f["rule_id"] for f in result.get("evaluation", {}).get("findings", [])]
    print(f"Rules fired: {rules}")
    print(f"Trace steps: {len(result.get('trace', []))}")
    print()
    print("Memo:")
    print(result.get("memo", "")[:400])
    print()
    print("PASS: LLM investigation completed")
except Exception as e:
    print(f"FAIL: {e}")
    import traceback

    traceback.print_exc()
