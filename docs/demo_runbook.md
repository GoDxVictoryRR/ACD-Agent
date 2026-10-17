# Demo Runbook & Video Script: Ownership Lens

*3-minute live demonstration script for submission video and live judging.*

---

## Beat 1: Proving the Graph Matters (Depth 1 vs Depth 3 Contrast)

1. Open the UI at `http://localhost:8000` (or the live URL).
2. Enter Target Entity Name: **`MOSSACK FONSECA & CO. (SAMOA) LIMITED.`** (or enter node ID `10001171`).
3. Set Watchlist Entities: **`TIANSHENG INDUSTRY AND TRADING CO., LTD.`** (node ID `10000001`).
4. Click **"Compare D1 vs D3"** (or run at Depth 1, then at Depth 3).
5. **Observation**:
   - **Depth 1 Panel**: Verdict is **CLEAR** (`"No indicators found within depth 1"`). The entity has a registered address and intermediary, but zero watchlist paths exist in 1 hop.
   - **Depth 3 Panel**: Verdict flips to **ESCALATE**!
   - Look at the Cytoscape graph canvas: A bright red highlighted exposure path appears:
     `MOSSACK FONSECA & CO. (SAMOA) LIMITED. (Entity) -[SAME_AS]-> MOSSACK FONSECA & CO. (SAMOA) LIMITED (Entity) -[OFFICER_OF]-> MOSSFON SUBSCRIBERS LTD. (Officer) -[OFFICER_OF]-> TIANSHENG INDUSTRY AND TRADING CO., LTD. (Watchlist Entity)`.
   - **Takeaway**: Relational lookups and shallow 1-hop checks completely miss the risk. Only multi-hop graph traversal through FalkorDB uncovers the hidden control path.

---

## Beat 2: Structural Hubs, Algorithms & The Honest System

1. Enter Target Entity: **`CRYSTAL RISE HOLDINGS LIMITED`** (node ID `10005699`).
2. Select **Depth 2** and click **Investigate**.
3. **Observation**:
   - Watch the live SSE trace stream as tools execute (`resolve_entity`, `ownership_chain`, `shared_links`, `cluster_view`).
   - Notice the trace markers: `via: mcp` and `source: llm`.
   - Verdict: **REVIEW**.
   - Evidence ledger flags `HUB_CENTRALITY`: Computed by FalkorDB `algo.betweenness` in the scratch graph with score $B = 79.0$ (calibrated $\ge 50.0$, 99.5th percentile).
   - Now test an entity not in the graph: enter **`Ghostly Offshore Unknown Corp XYZ`**.
   - Click **Investigate**.
   - Verdict: **INSUFFICIENT_EVIDENCE**. The system abstains honestly and lists candidate resolutions rather than hallucinating an answer.

---

## Beat 3: Graph Memory and Prior Case Recall

1. Now enter related entity: **`TIANSHENG INDUSTRY AND TRADING CO., LTD.`** (`node_id: 10000001`).
2. Select **Depth 2** and click **Investigate**.
3. **Observation**:
   - Observe the **"Prior Cases Recalled"** card on the results panel.
   - The earlier decision recorded on Mossack Fonseca is recalled automatically via 2-hop graph traversal from `(:Case)-[:ABOUT]->(shared)`.
   - Every verdict is written back into FalkorDB as a `(:Case)` node connected with `[:ABOUT]` and `[:CITED]` edges, making compliance intelligence compound over time.

---

## Voice-Over Script (150 Words — Read Aloud in ~60 Seconds)

> "Welcome to Ownership Lens, an autonomous graph agent built on FalkorDB for Track 1: Agents That Act on Connected Data.
>
> Offshore networks deliberately conceal beneficial ownership behind layers of shell companies and nominee directors. When we examine 'Mossack Fonseca Samoa' at depth 1, it appears clear: an ordinary address and registration.
>
> But when our agent traverses FalkorDB to depth 3, the verdict flips to ESCALATE. The graph uncovers a 3-hop control path through an officer hub directly into a defaulted entity on the watchlist.
>
> The LLM never writes raw Cypher and never invents verdicts. All decisions are computed deterministically by graph algorithms—PageRank, Betweenness, and Shortest Paths—and every memorandum is verified against tool data to eliminate hallucinations.
>
> Each decision is persisted back to FalkorDB as a Case node, allowing future investigations to recall past compliance intelligence. That is connected data in action."

---

## "If It Breaks" Backup Plan (Replay Fallback)

If the live LLM endpoint experiences an unexpected outage during recording:
1. Append `?mode=replay` to the URL or select any of the pre-configured replay demo cards in the UI.
2. The UI automatically displays the verified offline trace, Cytoscape graph layout, evidence ledger, and memo with a clear `"Replay Mode"` indicator badge, ensuring the demo can proceed flawlessly.
