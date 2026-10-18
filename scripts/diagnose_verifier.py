"""Diagnose memo verifier rejections across demo cases."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.stdout.reconfigure(encoding="utf-8")

import json

from agent.fallback import run_deterministic_investigation
from agent.llm import LLMClient
from agent.prompts import MEMO_PROMPT_TEMPLATE, SYSTEM_PROMPT
from core.verifier import extract_ground_truth_names, verify_memo

cases = [
    {"name": "GLAISDALE LIMITED", "depth": 4, "watchlist": ["DOM Limited"]},
    {"name": "GLAISDALE LIMITED", "depth": 1, "watchlist": ["DOM Limited"]},
    {"name": "Millex International Limited", "depth": 2, "watchlist": []},
    {"name": "OMNIA TECHNOLOGIES S.A.", "depth": 2, "watchlist": ["DOM Limited"]},
    {"name": "Dewburn Enterprises Inc.", "depth": 1, "watchlist": ["DOM Limited"]},
]

llm = LLMClient()
if not llm.is_available():
    print("LLM is not available! Check NVIDIA_API_KEY.")
    sys.exit(1)

print("Running verifier diagnosis on 5 cases...")
for case in cases:
    name = case["name"]
    depth = case["depth"]
    watchlist = case["watchlist"]
    print("\n==========================================")
    print(f"CASE: {name} (depth={depth})")

    # Run deterministic to get ground truth evidence
    res = run_deterministic_investigation(name, depth=depth, watchlist=watchlist)
    evidence = res["evidence"]
    rules_eval = res["evaluation"]

    gt_names = extract_ground_truth_names(evidence)
    print(f"Ground truth names ({len(gt_names)}): {sorted(list(gt_names))}")

    evidence_ledger_json = json.dumps(
        {
            "findings": rules_eval["findings"],
            "verdict": rules_eval["verdict"],
            "total_links": rules_eval["total_links"],
        },
        indent=2,
    )

    memo_prompt = MEMO_PROMPT_TEMPLATE.format(
        entity_name=name,
        depth=depth,
        verdict=rules_eval["verdict"].upper(),
        evidence_ledger_json=evidence_ledger_json,
    )

    try:
        resp = llm.chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": memo_prompt},
            ],
        )
        candidate_memo = resp["choices"][0]["message"]["content"]
        print(f"\nLLM Candidate Memo:\n{candidate_memo}")

        is_valid, unverified = verify_memo(candidate_memo, evidence)
        print(f"\nVerifier result: valid={is_valid}")
        if not is_valid:
            print(f"Unverified tokens rejected by verifier: {unverified}")
    except Exception as e:
        print(f"Error calling LLM: {e}")
