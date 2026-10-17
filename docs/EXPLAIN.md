# Technical Defense Guide: Ownership Lens

*A plain-language guide for explaining and defending the codebase during judging and presentation.*

---

## 1. High-Level Architecture in Plain Words

Ownership Lens investigates offshore corporate networks to detect hidden control, nominee directors, mass-incorporation addresses, and multi-hop paths to watchlisted entities.

The system is deliberately split into four strict layers:
1. **Primary Database (FalkorDB)**: Holds the property graph of Entities, Officers, Intermediaries, and Addresses. All multi-hop queries and graph algorithms execute here.
2. **Deterministic Rules Engine (`core/rules.py`)**: Computes the final verdict (`clear`, `review`, `escalate`, `insufficient_evidence`). The LLM **never** decides or alters the verdict.
3. **Agent Loop (`agent/loop.py`)**: An NVIDIA-hosted text model (`nvidia/nemotron-3-super-120b-a12b`) that chooses which read tools to invoke and writes a concise investigation memorandum.
4. **Memo Verifier (`core/verifier.py`)**: Verifies that every named entity in the LLM's memorandum exists in the graph tool outputs. If the LLM hallucinates an unverified name, the memo is instantly discarded and replaced with a deterministic template memo.

---

## 2. The 7 Graph Tools (`core/tools.py`)

| Tool | Graph Operation | Why the Decision Needs It |
|---|---|---|
| `resolve_entity` | Full-text / exact lookup on `:Entity(name)` | Anchors the investigation. Unknown or ambiguous entity immediately terminates with `insufficient_evidence`. |
| `ownership_chain` | Variable-length traversal `(e)-[*1..depth]-(target)` | Traces direct and indirect shareholding, directorship, and control up to 3 hops. |
| `shared_links` | Two-hop aggregation through hubs `(e)-[r1]-(hub)-[r2]-(other)` | Detects nominee officers and mass-registration addresses shared across dozens of shell entities. |
| `path_between` | `CALL algo.SPpaths` with `weightProp:'weight'` | Finds the shortest weighted evidence path between the target and any watchlisted entity within max depth. |
| `cluster_view` | Subgraph extraction + `algo.pageRank`, `algo.betweenness`, `algo.wcc`, `algo.labelPropagation` | Measures network centrality and community clustering in the entity's 2-hop neighborhood. Scratch graph is always deleted. |
| `recall_cases` | 2-hop traversal to historical `(:Case)` nodes | Surfaces prior compliance decisions that share directors, addresses, or intermediaries with the target entity. |
| `record_decision` | Writes back `(:Case)-[:ABOUT]->(:Entity)` and `[:CITED]->(node)` | Persists human and automated decisions directly back into the graph for future recall. |

---

## 3. The Rules Engine and Thresholds (`core/rules.py`)

The verdict is determined by pure Python functions with zero LLM influence:
- **`WATCHLIST_PATH` (High Severity)**: Fires if `path_between` finds a watchlist entity within depth 3 at weighted cost <= 8.0. Triggers **`escalate`**.
- **`PATH_REDUNDANCY` (High Severity)**: Fires if $\ge 2$ node-disjoint paths exist to a watchlist entity ("independent paths"). Triggers **`escalate`**.
- **`PATH_DEPENDENCY` (Medium Severity)**: Fires if exposure passes through a single intermediate bottleneck node ("exposure depends on <node>"). Triggers **`review`**.
- **`COMMUNITY_WATCHLIST` (Medium Severity)**: Fires if the entity shares a graph community (via `algo.labelPropagation`) with a watchlist entity without a direct path in range. Triggers **`review`**.
- **`HUB_CENTRALITY` (Medium Severity)**: Fires if node betweenness $B \ge 50.0$ (calibrated to the 99.5th percentile of scratch graph betweenness). Triggers **`review`**.
- **`NOMINEE_OFFICER_HUB` (Medium Severity)**: Fires if a connected officer serves in >= 5 distinct offshore entities (95th percentile). Triggers **`review`**.
- **`ADDRESS_HUB` (Medium Severity)**: Fires if a registered address is shared by >= 5 distinct offshore entities (95th percentile). Triggers **`review`**.
- **`INTERMEDIARY_CONCENTRATION` (Low Severity)**: Fires if an intermediary manages >= 10 entities (95th percentile). Triggers **`review`**.
- **Fewer than 2 links or unresolved**: Triggers **`insufficient_evidence`**.
- **No findings (connections >= 2)**: Triggers **`clear`** (displays as `"No indicators found within depth N"`).

---

## 4. Why "Forced" Tool Calls Exist

If the LLM makes unnecessary queries, runs out of its 8-call budget, or fails to call a critical tool (like `shared_links`), the agent loop executes a **Coverage Check**. Any missing required tool is executed deterministically and tagged `source: forced` in the audit trace. This guarantees that every investigation possesses a complete evidence ledger regardless of LLM behavior.

---

## 5. Free-Tier Resilience & Limits

1. **FalkorDB Cloud (100MB RAM, ephemeral)**:
   - Data seed is capped at ~60MB RAM footprint.
   - Self-seeding: On API startup, `ensure_seed()` checks graph counts; if empty or missing, it automatically loads the seed in under 60 seconds.
2. **Render Free Tier (512MB RAM, 15-min idle sleep)**:
   - Zero heavyweight runtime dependencies (no pandas, no vector DBs, no LangChain). Total process RSS is under 120MB.
   - Frontend UI monitors `/health` and alerts the user with a "Waking up backend" message if waking from sleep.
3. **NVIDIA API Rate Limits**:
   - Max 8 LLM calls per run with exponential backoff on 429/5xx errors.
   - If the LLM endpoint is unavailable or fails twice, the system seamlessly transitions to `agent/fallback.py` to produce deterministic results without crashing.

---

## 6. Ten Questions a Judge Might Ask (With 2-Line Answers)

1. **What happens if FalkorDB is removed?**
   The application halts immediately with an explicit error. Without the graph traversal and algorithms in FalkorDB, no paths, hubs, or centrality metrics exist, and no verdict can be generated.

2. **Why does the LLM not write raw Cypher?**
   Allowing LLMs to write raw Cypher creates prompt injection vulnerabilities, hallucinations, and unconstrained query timeouts. Typed tools guarantee parameterized queries, bounded depths, and deterministic schemas.

3. **How do you guarantee the LLM didn't hallucinate the verdict?**
   The LLM has zero control over the verdict. `core/rules.py` evaluates graph evidence deterministically and maps findings directly to `clear`, `review`, `escalate`, or `insufficient_evidence`.

4. **How do you prevent hallucinations in the written memo?**
   `core/verifier.py` parses all capitalized entities in the LLM memo and matches them against the tool output data. Any unverified name causes the memo to be discarded and replaced with a deterministic template memo.

5. **Why is depth 3 needed if depth 1 is already checked?**
   Offshore corporate networks deliberately use multi-layered nominee directorships and shell companies. At depth 1, an entity appears clean with an individual director; at depth 3, that director connects through an intermediary to a sanctioned target.

6. **Are you accusing entities in ICIJ data of wrongdoing?**
   No. All findings are strictly phrased as "exposure indicators requiring human review". Inclusion in ICIJ offshore leaks data does not imply illegality or wrongdoing.

7. **How does the system scale within FalkorDB Cloud free tier (100MB)?**
   We pruned redundant text fields, normalized relationship types, and loaded a high-density offshore subset that consumes only ~45MB of RAM, leaving room for scratch graphs and Case nodes.

8. **Why use SPpaths instead of basic shortestPath?**
   `algo.SPpaths` supports weighted traversals (`weightProp: 'weight'`), allowing officer and beneficial ownership links (weight 1.0) to be prioritized over weaker fuzzy-match links (weight 4.0).

9. **What is the purpose of the scratch graph in `cluster_view`?**
   Running global PageRank and betweenness on a full database takes unnecessary RAM and CPU. Extracting the local 2-hop neighborhood into a temporary scratch graph allows instant local centrality scoring, and the scratch graph is deleted in a `finally` block.

10. **Why not use LangChain, LlamaIndex, or GraphRAG SDK?**
    Direct integration with the official `falkordb` and `mcp` libraries eliminates dependency bloat, fits within Render's 512MB RAM constraint, and ensures every line of code is explainable, transparent, and debuggable.
