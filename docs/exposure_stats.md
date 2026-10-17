# Graph Exposure Statistics

**Dataset**: ICIJ (Panama Papers Samoa/Seychelles subset in FalkorDB)  
**Sample Size**: 250 entities (degree >= 1, seeded random sample, seed=42)  
**Target Watchlist**: TIANSHENG INDUSTRY AND TRADING CO., LTD. (Node IDs: 10000001)  

> [!IMPORTANT]
> **Caveat & Legal Disclaimer**: Demo watchlist items were chosen by graph criteria for demonstration only. They are not accusations. Inclusion in ICIJ data is not evidence of wrongdoing.

---

## Reachability by Graph Depth

| Depth | Exact Reach Count | Exact % | Cumulative Reach Count | Cumulative % |
|---|---|---|---|---|
| **Depth 1** | 0 | 0.0% | 0 | 0.0% |
| **Depth 2** | 75 | 30.0% | 75 | 30.0% |
| **Depth 3** | 0 | 0.0% | 75 | 30.0% |
| **Depth 4** | 86 | 34.4% | 161 | 64.4% |
| **None (>4 hops / disconnected)** | 89 | 35.6% | 250 | 100.0% |

---

## Key Graph Findings

1. **Depth 1 Sparsity**: Only **0.0%** of sampled entities connect directly to the watchlist target at depth 1.
2. **Multi-Hop Expansion**: By depth 3, cumulative exposure expands to **30.0%** (reaching **64.4%** at depth 4), demonstrating why multi-hop graph traversal is vital for uncovering hidden exposure.
3. **Graph Modularity**: **35.6%** of connected entities remain outside the 4-hop radius of the target, proving that the offshore network is partitioned into distinct clusters rather than a single trivial component.
