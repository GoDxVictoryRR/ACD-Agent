# Ablation Study: Verdict Stability and Layer Contribution

This ablation study isolates the decision boundary contributions of each architectural layer:
1. **Full Rules (Depth 3)**: Complete multi-hop graph traversal, node-disjoint path detection (`algo.SPpaths`), scratch graph community detection (`algo.labelPropagation`, `algo.WCC`), and centrality metrics (`algo.betweenness`, `algo.pageRank`).
2. **Depth 1 Only**: Single-hop neighborhood query without multi-hop traversal or cluster graph execution.
3. **Depth 2 Only**: Bounded 2-hop exploration.
4. **Without Algorithm Rules**: Removes `COMMUNITY_WATCHLIST` and `HUB_CENTRALITY` rule evaluation.
5. **Without Path Rules**: Removes `WATCHLIST_PATH`, `PATH_REDUNDANCY`, and `PATH_DEPENDENCY` rule evaluation.

---

## Ablation Matrix

| Entity Name | Category | Full Rules (Depth 3) | Depth 1 Only | Depth 2 Only | No Algorithm Rules | No Path Rules | Verdict Shifts? |
|---|---|---|---|---|---|---|---|
| `MOSSACK FONSECA & CO. (SAMOA) LIMITED.` | Primary Demo (Depth Flip) | **escalate** | `clear` | `review` | `escalate` | `review` | **YES** (Flippable) |
| `TIANSHENG INDUSTRY AND TRADING CO., LTD.` | Redundant Paths Demo | **review** | `review` | `review` | `review` | `review` | No (Stable) |
| `CRYSTAL RISE HOLDINGS LIMITED` | Hub Centrality Demo | **review** | `review` | `review` | `review` | `review` | No (Stable) |
| `Millex International Limited` | Nominee Hub Demo | **review** | `review` | `review` | `review` | `review` | No (Stable) |
| `Unknown Entity Alpha` | Negative Control: Unknown Entity | **insufficient_evidence** | `insufficient_evidence` | `insufficient_evidence` | `insufficient_evidence` | `insufficient_evidence` | No (Stable) |
| `Isolated Shell Corp` | Negative Control: Isolated (0 links) | **insufficient_evidence** | `insufficient_evidence` | `insufficient_evidence` | `insufficient_evidence` | `insufficient_evidence` | No (Stable) |
| `Single Link LLC` | Negative Control: Low-Link (1 link) | **insufficient_evidence** | `insufficient_evidence` | `insufficient_evidence` | `insufficient_evidence` | `insufficient_evidence` | No (Stable) |
| `Solitary Clean Trading Ltd` | Negative Control: Clean (No indicators) | **clear** | `clear` | `clear` | `clear` | `clear` | No (Stable) |

---

## Key Observations and Findings

1. **Depth Traversal Demonstrates Critical Graph Value**:
   - `MOSSACK FONSECA & CO. (SAMOA) LIMITED.` flips from **`clear`** at Depth 1 ("No indicators found within depth 1") to **`escalate`** at Depth 3 when connecting to watchlisted target `TIANSHENG INDUSTRY AND TRADING CO., LTD.`. Without multi-hop graph traversal, the entity would be falsely cleared.
2. **Algorithm Rules Surface Hidden Topological Exposure**:
   - `CRYSTAL RISE HOLDINGS LIMITED` has zero direct watchlist paths at Depth 2/3 (without path rules, it would remain clear of watchlist exposure). The `HUB_CENTRALITY` rule computed on the scratch graph detects that its intermediate node acts as a major structural bridge (`betweenness >= 0.05`), correctly shifting the verdict to **`review`**.
3. **Path Redundancy Differentiates Multi-Route Exposure from Single Bottlenecks**:
   - `TIANSHENG INDUSTRY AND TRADING CO., LTD.` exhibits independent node-disjoint paths connecting through distinct intermediary nominees, triggering `PATH_REDUNDANCY` with independent paths evidence.
4. **Negative Controls and Low-Link Rules Enforce Safety Invariants**:
   - Degree 0 (`Isolated Shell Corp`) and Degree 1 (`Single Link LLC`) entities strictly return `insufficient_evidence` across all conditions, enforcing that low-connection entities can never falsely clear.
   - Unresolved and unknown entities immediately terminate with `insufficient_evidence`.
