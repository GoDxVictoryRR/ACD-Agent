"""
core/rules.py — Deterministic rules engine for ACD-Agent.

Invariants:
- Pure functions: evaluate(evidence, max_depth, watchlist) -> RulesEvaluation.
- No LLM and no DB access inside this module.
- Verdict is determined SOLELY by these rules; LLM can never alter it.
- Wording: "exposure indicators requiring human review" (never guilty/fraud).
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from core.config import (
    ADDRESS_HUB_MIN,
    CENTRALITY_BETWEENNESS_MIN,
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
    display_verdict: str = ""
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
      - 'cluster_view': list of cluster_view dicts with community & centrality info
    """
    findings: list[Finding] = []
    watchlist_lower = [w.strip().lower() for w in (watchlist or []) if w.strip()]

    # Check 1: Resolution check (unknown, ambiguous, or error -> insufficient_evidence)
    resolved = evidence.get("resolved_entity")
    if not resolved:
        return RulesEvaluation(
            verdict="insufficient_evidence",
            display_verdict="insufficient_evidence",
            findings=[],
            total_links=0,
            resolved=False,
            notes="Entity could not be resolved to a unique graph node.",
        )

    if isinstance(resolved, dict):
        status = resolved.get("status", "")
        if status in ("ambiguous", "unknown_entity", "error"):
            return RulesEvaluation(
                verdict="insufficient_evidence",
                display_verdict="insufficient_evidence",
                findings=[],
                total_links=0,
                resolved=False,
                notes=f"Entity resolution status is '{status}'. Insufficient evidence to proceed.",
            )

    # Count total observed links / paths
    chain_paths = evidence.get("ownership_chain", [])
    hubs = evidence.get("shared_links", [])
    total_links = len(chain_paths) + len(hubs)

    # Check 2: Low-link entities return insufficient_evidence, never clear
    if total_links < MIN_LINKS:
        return RulesEvaluation(
            verdict="insufficient_evidence",
            display_verdict="insufficient_evidence",
            findings=[],
            total_links=total_links,
            resolved=True,
            notes=f"Insufficient graph connections (total links {total_links} < min {MIN_LINKS}).",
        )

    # Check 3: Watchlist paths, PATH_REDUNDANCY and PATH_DEPENDENCY (Requirements 3 & 5)
    watchlist_paths = evidence.get("paths_to_watchlist", [])
    has_watchlist_path = False

    for p in watchlist_paths:
        # CRITICAL (Requirement 3): Path tagging — rules count ONLY watchlist targets!
        if not p.get("is_watchlist", False):
            continue

        cost = float(p.get("path_weight", 999.0))
        nodes = p.get("nodes", [])
        if cost <= PATH_COST_MAX and len(nodes) > 1:
            has_watchlist_path = True
            target_name = p.get("target_name") or nodes[-1].get("name", "Unknown Watchlist Entity")
            target_id = p.get("target_id") or nodes[-1].get("id", "")
            disjoint_count = p.get("disjoint_paths_count", 1)
            exposure_depends_on = p.get("exposure_depends_on")

            if disjoint_count >= 2:
                # Requirement 5: >= 2 node-disjoint paths -> escalate, ledger says "independent paths"
                findings.append(
                    Finding(
                        rule_id="PATH_REDUNDANCY",
                        severity="high",
                        text=f"Redundant watchlist exposure: >= 2 independent paths link entity to watchlist target '{target_name}' at cost {cost:.1f} (node-disjoint paths confirmed).",
                        evidence_ids=[n.get("id") for n in nodes if n.get("id")],
                        metadata={
                            "path_weight": cost,
                            "target_id": target_id,
                            "disjoint_paths_count": disjoint_count,
                            "independent_paths": True,
                        },
                    )
                )
            elif exposure_depends_on and len(nodes) == 3:
                # Requirement 5: A single path through one intermediate node -> review, ledger names it "exposure depends on <node>"
                findings.append(
                    Finding(
                        rule_id="PATH_DEPENDENCY",
                        severity="medium",
                        text=f"Exposure indicator: Single indirect connection to watchlist target '{target_name}'; exposure depends on {exposure_depends_on}.",
                        evidence_ids=[n.get("id") for n in nodes if n.get("id")],
                        metadata={
                            "path_weight": cost,
                            "target_id": target_id,
                            "exposure_depends_on": exposure_depends_on,
                            "independent_paths": False,
                        },
                    )
                )
            else:
                findings.append(
                    Finding(
                        rule_id="WATCHLIST_PATH",
                        severity="high",
                        text=f"Exposure indicator: Direct or indirect path to watchlist entity '{target_name}' at cost {cost:.1f} (within depth {max_depth}): {' -> '.join([n.get('name', '') for n in nodes])}",
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
                    if not any(
                        f.rule_id in ("WATCHLIST_PATH", "PATH_REDUNDANCY", "PATH_DEPENDENCY")
                        and n.get("id") in f.evidence_ids
                        for f in findings
                    ):
                        has_watchlist_path = True
                        findings.append(
                            Finding(
                                rule_id="WATCHLIST_PATH",
                                severity="high",
                                text=f"Exposure indicator: Watchlist entity '{n.get('name')}' encountered in ownership chain within depth {max_depth}.",
                                evidence_ids=[n.get("id", "")],
                                metadata={"target_id": n.get("id"), "name": n.get("name")},
                            )
                        )

    # Check 4: Algorithm-driven rules (Requirement 4)
    cluster_data = evidence.get("cluster_view", [])
    if cluster_data:
        cdata = cluster_data[0] if isinstance(cluster_data, list) else cluster_data

        # Rule: COMMUNITY_WATCHLIST (no weighted path within depth, same community as a watchlist entity -> review)
        shared_comms = cdata.get("shared_watchlist_communities", [])
        if shared_comms and not has_watchlist_path:
            for sc in shared_comms:
                wl_name = sc.get("watchlist_name", "watchlist target")
                cid = sc.get("community_id", "?")
                findings.append(
                    Finding(
                        rule_id="COMMUNITY_WATCHLIST",
                        severity="medium",
                        text=f"Community exposure indicator: Entity belongs to the same network community (community {cid}) as watchlist entity '{wl_name}', though no short path exists within depth {max_depth}.",
                        evidence_ids=[sc.get("watchlist_id")] if sc.get("watchlist_id") else [],
                        metadata={"community_id": cid, "watchlist_name": wl_name},
                    )
                )

        # Rule: HUB_CENTRALITY (above a calibrated percentile -> review)
        high_centrality = cdata.get("high_centrality_nodes", [])
        for hc in high_centrality:
            hc_name = hc.get("name", "Hub")
            hc_score = hc.get("score", 0.0)
            hc_id = hc.get("id", "")
            findings.append(
                Finding(
                    rule_id="HUB_CENTRALITY",
                    severity="medium",
                    text=f"High graph centrality indicator: Node '{hc_name}' acts as a major structural bridge in the local network (betweenness centrality: {hc_score:.3f}, threshold: {CENTRALITY_BETWEENNESS_MIN}).",
                    evidence_ids=[hc_id] if hc_id else [],
                    metadata={"betweenness": hc_score, "threshold": CENTRALITY_BETWEENNESS_MIN},
                )
            )

    # Check 5: Hub rules
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

    # Requirement 1: "clear" displays as "No indicators found within depth N"
    display_verdict = f"No indicators found within depth {max_depth}" if verdict == "clear" else verdict

    return RulesEvaluation(
        verdict=verdict,
        display_verdict=display_verdict,
        findings=findings,
        total_links=total_links,
        resolved=True,
        notes=f"Evaluated {len(findings)} findings. Verdict: {verdict}",
    )
