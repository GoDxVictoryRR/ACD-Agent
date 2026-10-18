"""
core/verifier.py — Hallucination Verifier and Template Memo Generator.

Invariant 6:
Every entity, officer, address, and intermediary name mentioned in the LLM memo
must appear in this run's tool output data; otherwise discard the LLM memo
and fall back to the deterministic template memo built from the evidence ledger.
"""

from __future__ import annotations

import re
from typing import Any

from core.rules import RulesEvaluation


def extract_ground_truth_names(evidence: dict[str, Any]) -> set[str]:
    """Collect all known entity, officer, address, and intermediary names from tool output."""
    names: set[str] = set()

    # 1. Resolved entity
    resolved = evidence.get("resolved_entity")
    if resolved and isinstance(resolved, dict):
        if resolved.get("name"):
            names.add(resolved["name"].strip().lower())

    # 2. Ownership chain paths
    for path in evidence.get("ownership_chain", []):
        for node in path.get("nodes", []):
            if node.get("name"):
                names.add(node["name"].strip().lower())

    # 3. Shared links hubs
    for hub in evidence.get("shared_links", []):
        if hub.get("hub_name"):
            names.add(hub["hub_name"].strip().lower())

    # 4. Watchlist paths
    for p in evidence.get("paths_to_watchlist", []):
        for node in p.get("nodes", []):
            if node.get("name"):
                names.add(node["name"].strip().lower())

    # 5. Cluster view metrics
    cluster = evidence.get("cluster_view", {})
    if isinstance(cluster, list) and cluster:
        cluster = cluster[0]
    if isinstance(cluster, dict):
        for item in cluster.get("top_pagerank", []):
            if item.get("name"):
                names.add(item["name"].strip().lower())
        for item in cluster.get("top_betweenness", []):
            if item.get("name"):
                names.add(item["name"].strip().lower())

    return names


def normalize_name(s: str) -> str:
    """Normalize company name variants, suffixes, and punctuation for fair comparison."""
    norm = re.sub(r"[^\w\s]", " ", s.lower())
    words = norm.split()
    suffix_map = {
        "ltd": "limited",
        "corp": "corporation",
        "inc": "incorporated",
        "co": "company",
        "sa": "sa",
    }
    return " ".join(suffix_map.get(w, w) for w in words)


def verify_memo(
    memo: str,
    evidence: dict[str, Any],
) -> tuple[bool, list[str]]:
    """
    Verify that capitalized proper nouns in the memo match names in the tool output.
    Returns (is_valid, unverified_mentions).
    """
    if not memo or not memo.strip():
        return False, ["Empty memo"]

    ground_truth = extract_ground_truth_names(evidence)
    norm_gt = {normalize_name(gt) for gt in ground_truth}

    # Standard legal/financial stopwords and report headers to ignore
    stopwords = {
        "the",
        "a",
        "an",
        "this",
        "that",
        "these",
        "those",
        "no",
        "not",
        "none",
        "target",
        "compliance",
        "memorandum",
        "memo",
        "word",
        "words",
        "count",
        "based",
        "findings",
        "finding",
        "total",
        "links",
        "path",
        "weight",
        "rule",
        "rules",
        "status",
        "result",
        "results",
        "determination",
        "report",
        "review",
        "clear",
        "escalate",
        "insufficient_evidence",
        "falkordb",
        "cypher",
        "solely",
        "examination",
        "warrant",
        "further",
        "assessment",
        "conclusion",
        "note",
        "notes",
        "identified",
        "provided",
        "indicated",
        "indicates",
        "suggesting",
        "exhibits",
        "yielded",
        "returned",
        "associated",
        "implied",
        "active",
        "defaulted",
        "samoa",
        "seychelles",
        "entity",
        "officer",
        "address",
        "jurisdiction",
        "director",
        "shareholder",
        "intermediary",
        "verdict",
        "evidence",
        "ledger",
        "exposure",
        "indicators",
        "graph",
        "depth",
        "panama",
        "papers",
        "paradise",
        "bvi",
        "holding",
        "holdings",
        "corp",
        "corporation",
        "ltd",
        "limited",
        "inc",
        "incorporated",
        "llc",
        "sa",
        "company",
        "network",
        "investigation",
        "hub",
        "degree",
        "centrality",
        "community",
        "cost",
        "risk",
        "level",
        "analysis",
        "case",
    }

    # Extract capitalized phrases on single lines (no matching across newlines)
    candidate_tokens = re.findall(r"\b[A-Z][a-zA-Z0-9\.\-']*(?:[ \t]+[A-Z][a-zA-Z0-9\.\-']*)*\b", memo)

    unverified: list[str] = []
    for token in candidate_tokens:
        clean = token.strip()
        lower = clean.lower()
        words = lower.split()

        # If it's a common English word or stopword, ignore
        if len(words) == 1 and lower in stopwords:
            continue
        if all(w in stopwords for w in words):
            continue

        # Check raw substring matches or normalized suffix matches
        norm_candidate = normalize_name(clean)
        matches = (
            any(lower in gt or gt in lower for gt in ground_truth)
            or any(norm_candidate in ngt or ngt in norm_candidate for ngt in norm_gt)
        )
        if not matches:
            unverified.append(clean)

    is_valid = len(unverified) == 0
    return is_valid, unverified


def generate_template_memo(
    entity_name: str,
    evaluation: RulesEvaluation,
    depth: int = 2,
) -> str:
    """Build a deterministic, unhallucinated compliance memo from the evidence ledger."""
    verdict = evaluation.verdict
    findings = evaluation.findings

    verdict_label = f"NO INDICATORS FOUND WITHIN DEPTH {depth}" if verdict == "clear" else verdict.upper()
    lines = [
        "INVESTIGATION MEMORANDUM (Template Generated)",
        f"Target Entity: {entity_name}",
        f"Investigation Depth: {depth}",
        f"Verdict: {verdict_label} (Exposure indicators requiring human review)",
        "",
        "Summary:",
    ]

    if verdict == "insufficient_evidence":
        lines.append(
            f"The entity '{entity_name}' does not have sufficient verified graph connections "
            f"within depth {depth} to establish exposure indicators. Further documentation required."
        )
    elif verdict == "clear":
        lines.append(
            f"Investigation of '{entity_name}' across {evaluation.total_links} recorded relationship(s) "
            f"at depth {depth} identified zero high-degree hubs and no exposure links to watchlisted entities."
        )
    else:
        lines.append(
            f"Automated graph analysis revealed {len(findings)} key exposure indicator(s) "
            f"warranting human review at depth {depth}:"
        )
        for i, f in enumerate(findings, 1):
            lines.append(f"{i}. [{f.severity.upper()}] {f.text}")

    lines.append("")
    lines.append(
        "Disclaimer: Inclusion in ICIJ data is not evidence of wrongdoing. "
        "Demo watchlist items were chosen by graph criteria for demonstration only. They are not accusations. "
        "All findings are exposure indicators requiring human review."
    )
    return "\n".join(lines)
