"""
scripts/report_h2_verifier.py — Complete H2 verifier diagnosis and audit.
Executes 5 cases x 3 runs = 15 runs.
Compares Old Strict Verifier vs Normalized Verifier.
Shows 3 sample accepted memos alongside their verified ground truth tool outputs.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from agent.fallback import run_deterministic_investigation
from agent.llm import LLMClient
from agent.prompts import MEMO_PROMPT_TEMPLATE, SYSTEM_PROMPT
from core.verifier import (
    extract_ground_truth_names,
    verify_memo,
)


def old_strict_extract_memo_names(text: str) -> set[str]:
    """Reconstruct the old overly strict name extractor without normalization or multi-line boundary defense."""
    raw_patterns = [
        r"\b([A-Z][A-Za-z0-9&.,' -]+(?:Inc\.?|Corp\.?|Corporation|Ltd\.?|Limited|LLC|S\.A\.|Holdings|Group|Trust|Bank|Fund))\b",
        r"\b([A-Z][a-z]+ [A-Z][a-z]+(?: [A-Z][a-z]+)?)\b",
        r"\b([A-Z]{2,}(?: [A-Z]{2,})+)\b",
    ]
    found = set()
    for p in raw_patterns:
        for m in re.finditer(p, text):
            cand = m.group(1).strip()
            if cand not in {
                "Target Entity",
                "Evidence Ledger",
                "Offshore Leaks",
                "The Bearer",
                "Compliance Review",
                "Decision Record",
            }:
                found.add(cand)
    return found


def old_strict_verify(memo: str, evidence: dict) -> tuple[bool, set[str]]:
    gt_names = extract_ground_truth_names(evidence)
    gt_lower = {n.lower().strip() for n in gt_names if n}
    extracted = old_strict_extract_memo_names(memo)
    unverified = set()
    for cand in extracted:
        if cand.lower().strip() not in gt_lower:
            unverified.add(cand)
    return (len(unverified) == 0, unverified)


def main():
    llm = LLMClient()
    if not llm.is_available():
        print("LLM is not available! Check NVIDIA_API_KEY.")
        sys.exit(1)

    test_cases = [
        {"name": "GLAISDALE LIMITED", "depth": 4, "watchlist": ["DOM Limited"]},
        {"name": "GLAISDALE LIMITED", "depth": 1, "watchlist": ["DOM Limited"]},
        {"name": "Millex International Limited", "depth": 2, "watchlist": []},
        {"name": "OMNIA TECHNOLOGIES S.A.", "depth": 2, "watchlist": ["DOM Limited"]},
        {"name": "Dewburn Enterprises Inc.", "depth": 1, "watchlist": ["DOM Limited"]},
    ]

    print("================================================================================")
    print("H2: MEMO VERIFIER DIAGNOSIS & GROUND TRUTH AUDIT (5 cases x 3 runs = 15 total)")
    print("================================================================================")

    accepted_old = 0
    accepted_new = 0
    samples_to_show = []

    for case in test_cases:
        name = case["name"]
        depth = case["depth"]
        watchlist = case["watchlist"]

        det_res = run_deterministic_investigation(name, depth=depth, watchlist=watchlist)
        evidence = det_res["evidence"]
        rules_eval = det_res["evaluation"]
        gt_names = extract_ground_truth_names(evidence)

        ledger_json = json.dumps(
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
            evidence_ledger_json=ledger_json,
        )

        for run_idx in range(1, 4):
            case_label = f"{name} (d={depth}, run {run_idx})"
            llm_inst = LLMClient()
            resp = llm_inst.chat_completion(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": memo_prompt},
                ],
            )
            candidate_memo = resp["choices"][0]["message"]["content"]

            old_valid, old_unverified = old_strict_verify(candidate_memo, evidence)
            new_valid, new_unverified = verify_memo(candidate_memo, evidence)

            if old_valid:
                accepted_old += 1
            if new_valid:
                accepted_new += 1

            old_str = "PASSED" if old_valid else f"REJECTED: {sorted(list(old_unverified))}"
            new_str = "PASSED" if new_valid else f"REJECTED: {sorted(list(new_unverified))}"
            print(f"[{case_label}]")
            print(f"  Old Verifier: {old_str}")
            print(f"  New Verifier: {new_str}")

            if run_idx == 1 and len(samples_to_show) < 3:
                samples_to_show.append(
                    {
                        "case": f"{name} (depth={depth})",
                        "memo": candidate_memo,
                        "gt_names": sorted(list(gt_names)),
                    }
                )

    print("\n================================================================================")
    print("VERIFIER ACCEPTANCE RATES")
    print("================================================================================")
    print(f"Old Strict Verifier Rate:     {accepted_old}/15 ({accepted_old/15*100:.1f}%)")
    print(f"New Normalized Verifier Rate: {accepted_new}/15 ({accepted_new/15*100:.1f}%)")

    print("\n================================================================================")
    print("HALLUCINATION GUARD TEST (Synthetic Poison Injection)")
    print("================================================================================")
    fake_memo = "Investigation of GLAISDALE LIMITED revealed money laundering links to Acme Laundering Corp and John Doe."
    poison_evidence = det_res["evidence"]
    is_valid, unverified = verify_memo(fake_memo, poison_evidence)
    print(f"Poisoned Memo: '{fake_memo}'")
    print(f"Verifier Result: Valid={is_valid}, Blocked Fabricated Names: {sorted(list(unverified))}")
    assert not is_valid, "Verifier must reject fabricated names!"
    assert any("Acme" in u for u in unverified), "Acme Laundering Corp must be flagged!"

    print("\n================================================================================")
    print("3 SAMPLES: ACCEPTED MEMO NEXT TO TOOL OUTPUT")
    print("================================================================================")
    for i, s in enumerate(samples_to_show, 1):
        print(f"\n--- SAMPLE {i}: {s['case']} ---")
        print("VERIFIED TOOL OUTPUT ENTITIES & PERSONS:")
        for gn in s["gt_names"]:
            print(f"  - {gn}")
        print("\nACCEPTED LLM MEMO:")
        print(s["memo"].strip())
        print("-" * 80)


if __name__ == "__main__":
    main()
