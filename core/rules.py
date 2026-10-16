"""
core/rules.py — Deterministic rules engine for ACD-Agent.

Invariants:
- Pure functions: evaluate(evidence, max_depth, watchlist) -> {"verdict": ..., "findings": [...]}.
- No LLM and no DB access inside this module.
- Verdict is determined SOLELY by these rules; LLM can never alter it.
- Wording: "exposure indicators requiring human review" (never guilty/fraud).
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from core.config import (
    ADDRESS_HUB_MIN,
    INTERMEDIARY_MIN,
    MIN_LINKS,
    OFFICER_HUB_MIN,
    PATH_COST_MAX,
    VERDICTS,
)


class Finding(BaseModel):
    rule_id: str
    severity: Literal["high", "medium", "low"]
    text: str
    evidence_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RulesEvaluation(BaseModel):
    verdict: Literal["clear", "review", "escalate", "insufficient_evidence"]
    findings: list[Finding] = Field(default_factory=list)
    total_links: int = 0
    resolved: bool = True
    notes: str = ""


def evaluate(
    evidence: dict[str, Any],
    max_depth: int = 2,
    watchlist: list[str] | None = None,
) -> RulesEvaluation:
    """
    Evaluate collected evidence against deterministic rules.
    Evidence structure expects keys from tool results:
      - 'resolved_entity': dict or None
      - 'ownership_chain': list of paths
      - 'shared_links': list of hub dicts
      - 'paths_to_watchlist': list of path_between dicts
      - 'cluster_view': dict with community info
    """
    findings: list[Finding] = []
    watchlist_lower = [w.strip().lower() for w in (watchlist or []) if w.strip()]

    # Check 1: Resolution check
    resolved = evidence.get("resolved_entity")
    if not resolved:
        return RulesEvaluation(
            verdict="insufficient_evidence",
            findings=[],
            total_links=0,
            resolved=False,
            notes="Entity could not be resolved to a unique graph node.",
        )

    # Count total observed links / paths
    chain_paths = evidence.get("ownership_chain", [])
    hubs = evidence.get("shared_links", [])
    total_links = len(chain_paths) + len(hubs)

    if total_links < MIN_LINKS:
        return RulesEvaluation(
            verdict="insufficient_evidence",
            findings=[],
            total_links=total_links,
            resolved=True,
            notes=f"Insufficient graph connections (total links {total_links} < min {MIN_LINKS}).",
        )

    # Rule 1: WATCHLIST_PATH (Severity: high)
    watchlist_paths = evidence.get("paths_to_watchlist", [])
    for p in watchlist_paths:
        cost = float(p.get("path_weight", 999.0))
        nodes = p.get("nodes", [])
        if cost <= PATH_COST_MAX and len(nodes) > 1:
            target_name = nodes[-1].get("name", "Unknown Watchlist Entity")
            target_id = nodes[-1].get("id", "")
            path_str = " -> ".join([n.get("name", "") for n in nodes])
            findings.append(
                Finding(
                    rule_id="WATCHLIST_PATH",
                    severity="high",
                    text=f"Exposure indicator: Direct or indirect path to watchlist entity '{target_name}' at cost {cost:.1f} (within depth {max_depth}): {path_str}",
                    evidence_ids=[n.get("id") for n in nodes if n.get("id")],
                    metadata={"path_weight": cost, "target_id": target_id, "depth": len(nodes) - 1},
                )
            )

    # Check for watchlist entities directly in ownership chain up to max_depth
    if watchlist_lower:
        for path in chain_paths:
            p_nodes = path.get("nodes", [])
            for n in p_nodes[1:]:  # skip source entity itself
                n_name = n.get("name", "").lower()
                if any(w in n_name or n_name in w for w in watchlist_lower):
                    # Check if already added
                    if not any(f.rule_id == "WATCHLIST_PATH" and n.get("id") in f.evidence_ids for f in findings):
                        findings.append(
                            Finding(
                                rule_id="WATCHLIST_PATH",
                                severity="high",
                                text=f"Exposure indicator: Watchlist entity '{n.get('name')}' encountered in ownership chain within depth {max_depth}.",
                                evidence_ids=[n.get("id", "")],
                                metadata={"target_id": n.get("id"), "name": n.get("name")},
                            )
                        )

    # Rule 2: ADDRESS_HUB (Severity: medium)
    for h in hubs:
        hub_type = h.get("hub_type", "")
        linked = int(h.get("linked_count", 0))
        hub_name = h.get("hub_name", "")
        hub_id = h.get("hub_id", "")

        if hub_type == "Address" and linked >= ADDRESS_HUB_MIN:
            findings.append(
                Finding(
                    rule_id="ADDRESS_HUB",
                    severity="medium",
                    text=f"Mass incorporation indicator: Registered address '{hub_name}' is shared by {linked} other offshore entities (threshold: {ADDRESS_HUB_MIN}).",
                    evidence_ids=[hub_id],
                    metadata={"linked_count": linked, "address": hub_name},
                )
            )

        # Rule 3: NOMINEE_OFFICER_HUB (Severity: medium)
        elif hub_type == "Officer" and linked >= OFFICER_HUB_MIN:
            findings.append(
                Finding(
                    rule_id="NOMINEE_OFFICER_HUB",
                    severity="medium",
                    text=f"Nominee concentration indicator: Connected officer '{hub_name}' serves as officer in {linked} other offshore entities (threshold: {OFFICER_HUB_MIN}).",
                    evidence_ids=[hub_id],
                    metadata={"linked_count": linked, "officer": hub_name},
                )
            )

        # Rule 4: INTERMEDIARY_CONCENTRATION (Severity: low)
        elif hub_type == "Intermediary" and linked >= INTERMEDIARY_MIN:
            findings.append(
                Finding(
                    rule_id="INTERMEDIARY_CONCENTRATION",
                    severity="low",
                    text=f"Intermediary hub indicator: Connected intermediary '{hub_name}' facilitates {linked} offshore entities (threshold: {INTERMEDIARY_MIN}).",
                    evidence_ids=[hub_id],
                    metadata={"linked_count": linked, "intermediary": hub_name},
                )
            )

    # Determine Verdict based solely on findings
    has_high = any(f.severity == "high" for f in findings)
    has_medium = any(f.severity == "medium" for f in findings)

    if has_high:
        verdict = "escalate"
    elif has_medium:
        verdict = "review"
    else:
        verdict = "clear"

    assert verdict in VERDICTS

    return RulesEvaluation(
        verdict=verdict,
        findings=findings,
        total_links=total_links,
        resolved=True,
        notes=f"Evaluated {len(findings)} findings. Verdict: {verdict}",
    )
