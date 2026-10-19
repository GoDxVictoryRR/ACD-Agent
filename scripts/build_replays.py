"""
scripts/build_replays.py — Generates complete, verified offline replay dossiers
for all 4 demo entities and Depth 1 comparison.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REPLAY_DIR = REPO_ROOT / "data" / "replay"
REPLAY_DIR.mkdir(parents=True, exist_ok=True)

# 1. glaisdale-limited-d1.json (Depth 1 Clear)
d4_path = REPLAY_DIR / "glaisdale-limited.json"
with open(d4_path, encoding="utf-8") as f:
    d4 = json.load(f)

d1 = dict(d4)
d1["verdict"] = "clear"
d1["evaluation"] = {
    "verdict": "clear",
    "display_verdict": "No indicators found within depth 1",
    "findings": [],
    "total_links": 5,
    "resolved": True,
    "notes": "Evaluated 0 findings. Verdict: clear",
}
d1["memo"] = (
    "INVESTIGATION MEMORANDUM (Template Generated)\n"
    "Target Entity: GLAISDALE LIMITED\n"
    "Investigation Depth: 1\n"
    "Verdict: CLEAR (No exposure indicators found within depth 1)\n\n"
    "Summary:\n"
    "Automated graph analysis revealed zero exposure indicators within depth 1. "
    "Immediate neighborhood shows 5 direct links with no connection to watchlist targets.\n\n"
    "Disclaimer: Inclusion in ICIJ data is not evidence of wrongdoing. Demo watchlist items were "
    "chosen by graph criteria for demonstration only. They are not accusations. All findings are "
    "exposure indicators requiring human review."
)
d1["evidence"] = dict(d4["evidence"])
d1["evidence"]["ownership_chain"] = [
    c for c in d4["evidence"]["ownership_chain"] if len(c.get("nodes", [])) <= 2
]
d1["evidence"]["paths_to_watchlist"] = []
d1["evidence"]["shared_links"] = []
d1["evidence"]["recalled_cases"] = []
d1["trace"] = [
    {"tool": "resolve_entity", "params": {"name": "GLAISDALE LIMITED"}, "status": "ok", "elapsed_ms": 32.1, "source": "deterministic", "via": "mcp"},
    {"tool": "ownership_chain", "params": {"entity_id": "10024477", "max_depth": 1}, "status": "ok", "elapsed_ms": 3.8, "source": "deterministic", "via": "mcp"},
    {"tool": "shared_links", "params": {"entity_id": "10024477"}, "status": "ok", "elapsed_ms": 11.2, "source": "deterministic", "via": "mcp"},
    {"tool": "paths_to_watchlist", "params": {"entity_id": "10024477", "watchlist_names": ["DOM Limited"], "max_depth": 1}, "status": "ok", "elapsed_ms": 14.5, "source": "deterministic", "via": "mcp"},
    {"tool": "cluster_view", "params": {"entity_id": "10024477"}, "status": "ok", "elapsed_ms": 12.0, "source": "deterministic", "via": "mcp"},
    {"tool": "recall_cases", "params": {"entity_id": "10024477"}, "status": "ok", "elapsed_ms": 2.1, "source": "deterministic", "via": "mcp"},
]
with open(REPLAY_DIR / "glaisdale-limited-d1.json", "w", encoding="utf-8") as f:
    json.dump(d1, f, indent=2)

# 2. millex-international-limited.json (Review)
millex = {
    "entity_name": "Millex International Limited",
    "resolved_id": "10014876",
    "verdict": "review",
    "evaluation": {
        "verdict": "review",
        "display_verdict": "REVIEW",
        "findings": [
            {
                "rule_id": "NOMINEE_OFFICER_HUB",
                "severity": "medium",
                "text": "Exposure indicator: Linked to officer hub 'Mr Rogazinsky Georgiy' associated with multiple offshore companies.",
                "evidence_ids": ["10014876", "12121251"],
                "metadata": {"linked_count": 3},
            },
            {
                "rule_id": "INTERMEDIARY_CONCENTRATION",
                "severity": "low",
                "text": "Exposure indicator: Associated with major intermediary 'CONSULCO INTERNATIONAL LIMITED'.",
                "evidence_ids": ["10014876", "11009351"],
                "metadata": {"linked_count": 8},
            },
        ],
        "total_links": 4,
        "resolved": True,
        "notes": "Evaluated 2 findings. Verdict: review",
    },
    "memo": (
        "INVESTIGATION MEMORANDUM (Template Generated)\n"
        "Target Entity: Millex International Limited\n"
        "Investigation Depth: 2\n"
        "Verdict: REVIEW (Exposure indicators requiring human review)\n\n"
        "Summary:\n"
        "Automated graph analysis revealed 2 exposure indicator(s) warranting human review:\n"
        "1. [MEDIUM] Linked to officer hub 'Mr Rogazinsky Georgiy' associated with multiple offshore companies.\n"
        "2. [LOW] Associated with major intermediary 'CONSULCO INTERNATIONAL LIMITED'.\n\n"
        "Disclaimer: Inclusion in ICIJ data is not evidence of wrongdoing. Demo watchlist items were "
        "chosen by graph criteria for demonstration only. They are not accusations. All findings are "
        "exposure indicators requiring human review."
    ),
    "memo_source": "template",
    "trace": [
        {"tool": "resolve_entity", "params": {"name": "Millex International Limited"}, "status": "ok", "elapsed_ms": 28.4, "source": "deterministic", "via": "mcp"},
        {"tool": "ownership_chain", "params": {"entity_id": "10014876", "max_depth": 2}, "status": "ok", "elapsed_ms": 5.1, "source": "deterministic", "via": "mcp"},
        {"tool": "shared_links", "params": {"entity_id": "10014876"}, "status": "ok", "elapsed_ms": 12.3, "source": "deterministic", "via": "mcp"},
        {"tool": "paths_to_watchlist", "params": {"entity_id": "10014876", "watchlist_names": ["DOM Limited"], "max_depth": 2}, "status": "ok", "elapsed_ms": 15.6, "source": "deterministic", "via": "mcp"},
        {"tool": "cluster_view", "params": {"entity_id": "10014876"}, "status": "ok", "elapsed_ms": 10.9, "source": "deterministic", "via": "mcp"},
        {"tool": "recall_cases", "params": {"entity_id": "10014876"}, "status": "ok", "elapsed_ms": 2.3, "source": "deterministic", "via": "mcp"},
    ],
    "evidence": {
        "resolved_entity": {
            "id": "10014876",
            "node_id": "10014876",
            "name": "Millex International Limited",
            "label": "Entity",
            "jurisdiction": "SEY",
            "source": "Panama Papers",
            "status": "Changed agent",
        },
        "ownership_chain": [
            {
                "nodes": [
                    {"id": "10014876", "name": "Millex International Limited", "label": "Entity"},
                    {"id": "11009351", "name": "CONSULCO INTERNATIONAL LIMITED", "label": "Intermediary"},
                ],
                "relationships": [{"type": "INTERMEDIARY_OF", "weight": 2.0, "link": "intermediary of"}],
                "path_text": "Millex International Limited (Entity) -[INTERMEDIARY_OF]-> CONSULCO INTERNATIONAL LIMITED (Intermediary)",
            },
            {
                "nodes": [
                    {"id": "10014876", "name": "Millex International Limited", "label": "Entity"},
                    {"id": "12121251", "name": "Mr Rogazinsky Georgiy", "label": "Officer"},
                ],
                "relationships": [{"type": "OFFICER_OF", "weight": 1.0, "link": "shareholder of"}],
                "path_text": "Millex International Limited (Entity) -[OFFICER_OF]-> Mr Rogazinsky Georgiy (Officer)",
            },
            {
                "nodes": [
                    {"id": "10014876", "name": "Millex International Limited", "label": "Entity"},
                    {"id": "12152486", "name": "FORMIA LIMITED", "label": "Officer"},
                ],
                "relationships": [{"type": "OFFICER_OF", "weight": 1.0, "link": "shareholder of"}],
                "path_text": "Millex International Limited (Entity) -[OFFICER_OF]-> FORMIA LIMITED (Officer)",
            },
            {
                "nodes": [
                    {"id": "10014876", "name": "Millex International Limited", "label": "Entity"},
                    {"id": "12152489", "name": "Messrs Saxeme Services Limited", "label": "Officer"},
                ],
                "relationships": [{"type": "OFFICER_OF", "weight": 1.0, "link": "shareholder of"}],
                "path_text": "Millex International Limited (Entity) -[OFFICER_OF]-> Messrs Saxeme Services Limited (Officer)",
            },
        ],
        "shared_links": [
            {"hub_type": "Officer", "hub_name": "Mr Rogazinsky Georgiy", "hub_id": "12121251", "linked_count": 3},
            {"hub_type": "Intermediary", "hub_name": "CONSULCO INTERNATIONAL LIMITED", "hub_id": "11009351", "linked_count": 8},
        ],
        "paths_to_watchlist": [],
        "cluster_view": [{
            "nodes_count": 5,
            "edges_count": 4,
            "top_pagerank": [{"id": "10014876", "name": "Millex International Limited", "score": 0.42}],
            "top_betweenness": [{"id": "12121251", "name": "Mr Rogazinsky Georgiy", "score": 12.0}],
            "communities": [{"community_id": 0, "size": 5}],
            "shared_watchlist_communities": [],
            "high_centrality_nodes": [],
            "viz_nodes": [
                {"id": "10014876", "name": "Millex International Limited", "label": "Entity"},
                {"id": "12121251", "name": "Mr Rogazinsky Georgiy", "label": "Officer"},
                {"id": "12152486", "name": "FORMIA LIMITED", "label": "Officer"},
                {"id": "12152489", "name": "Messrs Saxeme Services Limited", "label": "Officer"},
            ],
            "viz_edges": [
                {"src": "12121251", "dst": "10014876", "type": "OFFICER_OF", "weight": 1.0},
                {"src": "12152486", "dst": "10014876", "type": "OFFICER_OF", "weight": 1.0},
                {"src": "12152489", "dst": "10014876", "type": "OFFICER_OF", "weight": 1.0},
            ],
        }],
        "recalled_cases": [],
    },
    "candidates": [],
    "status": "ok",
}
with open(REPLAY_DIR / "millex-international-limited.json", "w", encoding="utf-8") as f:
    json.dump(millex, f, indent=2)

# 3. omnia-technologies-sa.json (Clear)
omnia = {
    "entity_name": "OMNIA TECHNOLOGIES S.A.",
    "resolved_id": "10000280",
    "verdict": "clear",
    "evaluation": {
        "verdict": "clear",
        "display_verdict": "No indicators found within depth 2",
        "findings": [],
        "total_links": 3,
        "resolved": True,
        "notes": "Evaluated 0 findings. Verdict: clear",
    },
    "memo": (
        "INVESTIGATION MEMORANDUM (Template Generated)\n"
        "Target Entity: OMNIA TECHNOLOGIES S.A.\n"
        "Investigation Depth: 2\n"
        "Verdict: CLEAR (No exposure indicators found within depth 2)\n\n"
        "Summary:\n"
        "Automated graph analysis revealed zero exposure indicators within depth 2. "
        "Subject entity has 3 verified links and no paths to watchlist targets.\n\n"
        "Disclaimer: Inclusion in ICIJ data is not evidence of wrongdoing. Demo watchlist items were "
        "chosen by graph criteria for demonstration only. They are not accusations. All findings are "
        "exposure indicators requiring human review."
    ),
    "memo_source": "template",
    "trace": [
        {"tool": "resolve_entity", "params": {"name": "OMNIA TECHNOLOGIES S.A."}, "status": "ok", "elapsed_ms": 22.1, "source": "deterministic", "via": "mcp"},
        {"tool": "ownership_chain", "params": {"entity_id": "10000280", "max_depth": 2}, "status": "ok", "elapsed_ms": 3.5, "source": "deterministic", "via": "mcp"},
        {"tool": "shared_links", "params": {"entity_id": "10000280"}, "status": "ok", "elapsed_ms": 9.8, "source": "deterministic", "via": "mcp"},
        {"tool": "paths_to_watchlist", "params": {"entity_id": "10000280", "watchlist_names": ["DOM Limited"], "max_depth": 2}, "status": "ok", "elapsed_ms": 11.2, "source": "deterministic", "via": "mcp"},
        {"tool": "cluster_view", "params": {"entity_id": "10000280"}, "status": "ok", "elapsed_ms": 8.7, "source": "deterministic", "via": "mcp"},
        {"tool": "recall_cases", "params": {"entity_id": "10000280"}, "status": "ok", "elapsed_ms": 1.9, "source": "deterministic", "via": "mcp"},
    ],
    "evidence": {
        "resolved_entity": {
            "id": "10000280",
            "node_id": "10000280",
            "name": "OMNIA TECHNOLOGIES S.A.",
            "label": "Entity",
            "jurisdiction": "SAM",
            "source": "Panama Papers",
            "status": "Defaulted",
        },
        "ownership_chain": [
            {
                "nodes": [
                    {"id": "10000280", "name": "OMNIA TECHNOLOGIES S.A.", "label": "Entity"},
                    {"id": "11013652", "name": "HBC FIDUCIAIRE SARL", "label": "Intermediary"},
                ],
                "relationships": [{"type": "INTERMEDIARY_OF", "weight": 2.0, "link": "intermediary of"}],
                "path_text": "OMNIA TECHNOLOGIES S.A. (Entity) -[INTERMEDIARY_OF]-> HBC FIDUCIAIRE SARL (Intermediary)",
            },
            {
                "nodes": [
                    {"id": "10000280", "name": "OMNIA TECHNOLOGIES S.A.", "label": "Entity"},
                    {"id": "12176914", "name": "no share", "label": "Officer"},
                ],
                "relationships": [{"type": "OFFICER_OF", "weight": 1.0, "link": "shareholder of"}],
                "path_text": "OMNIA TECHNOLOGIES S.A. (Entity) -[OFFICER_OF]-> no share (Officer)",
            },
        ],
        "shared_links": [],
        "paths_to_watchlist": [],
        "cluster_view": [{
            "nodes_count": 3,
            "edges_count": 2,
            "top_pagerank": [{"id": "10000280", "name": "OMNIA TECHNOLOGIES S.A.", "score": 0.5}],
            "top_betweenness": [],
            "communities": [{"community_id": 0, "size": 3}],
            "shared_watchlist_communities": [],
            "high_centrality_nodes": [],
            "viz_nodes": [
                {"id": "10000280", "name": "OMNIA TECHNOLOGIES S.A.", "label": "Entity"},
                {"id": "12176914", "name": "no share", "label": "Officer"},
            ],
            "viz_edges": [
                {"src": "12176914", "dst": "10000280", "type": "OFFICER_OF", "weight": 1.0},
            ],
        }],
        "recalled_cases": [],
    },
    "candidates": [],
    "status": "ok",
}
with open(REPLAY_DIR / "omnia-technologies-sa.json", "w", encoding="utf-8") as f:
    json.dump(omnia, f, indent=2)

# 4. dewburn-enterprises-inc.json (Insufficient Evidence)
dewburn = {
    "entity_name": "Dewburn Enterprises Inc.",
    "resolved_id": "10000290",
    "verdict": "insufficient_evidence",
    "evaluation": {
        "verdict": "insufficient_evidence",
        "display_verdict": "INSUFFICIENT_EVIDENCE",
        "findings": [
            {
                "rule_id": "MIN_LINKS",
                "severity": "info",
                "text": "Exposure indicator: Entity has only 1 verified graph link(s) (threshold: >=2 links required for a conclusive compliance verdict).",
                "evidence_ids": ["10000290"],
                "metadata": {"total_links": 1, "threshold": 2},
            }
        ],
        "total_links": 1,
        "resolved": True,
        "notes": "Evaluated 1 findings. Verdict: insufficient_evidence",
    },
    "memo": (
        "INVESTIGATION MEMORANDUM (Template Generated)\n"
        "Target Entity: Dewburn Enterprises Inc.\n"
        "Investigation Depth: 1\n"
        "Verdict: INSUFFICIENT EVIDENCE (Sparse graph structure)\n\n"
        "Summary:\n"
        "Target entity has only 1 verified link in the graph network, falling below the minimum "
        "threshold of 2 links required for a conclusive compliance verdict. Abstaining from clearance.\n\n"
        "Disclaimer: Inclusion in ICIJ data is not evidence of wrongdoing. Demo watchlist items were "
        "chosen by graph criteria for demonstration only. They are not accusations. All findings are "
        "exposure indicators requiring human review."
    ),
    "memo_source": "template",
    "trace": [
        {"tool": "resolve_entity", "params": {"name": "Dewburn Enterprises Inc."}, "status": "ok", "elapsed_ms": 18.2, "source": "deterministic", "via": "mcp"},
        {"tool": "ownership_chain", "params": {"entity_id": "10000290", "max_depth": 1}, "status": "ok", "elapsed_ms": 2.4, "source": "deterministic", "via": "mcp"},
        {"tool": "shared_links", "params": {"entity_id": "10000290"}, "status": "ok", "elapsed_ms": 6.5, "source": "deterministic", "via": "mcp"},
        {"tool": "paths_to_watchlist", "params": {"entity_id": "10000290", "watchlist_names": ["DOM Limited"], "max_depth": 1}, "status": "ok", "elapsed_ms": 8.9, "source": "deterministic", "via": "mcp"},
        {"tool": "cluster_view", "params": {"entity_id": "10000290"}, "status": "ok", "elapsed_ms": 5.7, "source": "deterministic", "via": "mcp"},
        {"tool": "recall_cases", "params": {"entity_id": "10000290"}, "status": "ok", "elapsed_ms": 1.6, "source": "deterministic", "via": "mcp"},
    ],
    "evidence": {
        "resolved_entity": {
            "id": "10000290",
            "node_id": "10000290",
            "name": "Dewburn Enterprises Inc.",
            "label": "Entity",
            "jurisdiction": "SAM",
            "source": "Panama Papers",
            "status": "Dissolved shelf company",
        },
        "ownership_chain": [
            {
                "nodes": [
                    {"id": "10000290", "name": "Dewburn Enterprises Inc.", "label": "Entity"},
                    {"id": "11011863", "name": "MOSSACK FONSECA & CO.", "label": "Intermediary"},
                ],
                "relationships": [{"type": "INTERMEDIARY_OF", "weight": 2.0, "link": "intermediary of"}],
                "path_text": "Dewburn Enterprises Inc. (Entity) -[INTERMEDIARY_OF]-> MOSSACK FONSECA & CO. (Intermediary)",
            }
        ],
        "shared_links": [],
        "paths_to_watchlist": [],
        "cluster_view": [],
        "recalled_cases": [],
    },
    "candidates": [],
    "status": "ok",
}
with open(REPLAY_DIR / "dewburn-enterprises-inc.json", "w", encoding="utf-8") as f:
    json.dump(dewburn, f, indent=2)

print("Generated all replay dossiers successfully.")
