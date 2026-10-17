# Building Ownership Lens: How Connected Data Solves the Offshore Shell Company Puzzle

*Track 1 Submission: Agents That Act on Connected Data (WeMakeDevs x FalkorDB Hackathon)*

Offshore corporate structures are deliberately engineered to obscure beneficial ownership. A single entity registered in Samoa, Panama, or the British Virgin Islands typically appears entirely benign when viewed in isolation: one registered agent, one postal box, and an unfamiliar corporate director. In a standard relational database or SQL table, querying this entity produces a clean bill of health.

Yet beneath that single tabular row lies an intricate graph of control. That registered agent may manage hundreds of shell companies across multiple jurisdictions. That individual director may be a nominee serving on fifty interlocking corporate boards. And three hops away—through an offshore management intermediary—that seemingly benign entity may connect directly to an entity on an international sanctions watchlist.

To solve this problem for Track 1 of the WeMakeDevs x FalkorDB Graph Hacks hackathon, we built **Ownership Lens**—an autonomous graph agent that investigates offshore control networks using FalkorDB, MCP tool calling, deterministic compliance rules, and an anti-hallucination verification ledger.

---

## The Dataset: Real-World Panama Papers

Rather than relying on artificial toy graphs, Ownership Lens runs on an empirical subset of the **ICIJ Offshore Leaks Database** (Panama Papers Samoa and Seychelles jurisdictions):
- **51,940 nodes** (Entities, Officers, Intermediaries, Addresses)
- **58,891 relationships** (`registered_address`, `officer_of`, `intermediary_of`)
- **40.91 MiB RAM footprint** in FalkorDB (safely within FalkorDB Cloud's 100 MiB free tier limit)

Inclusion in the ICIJ database is not evidence of wrongdoing or illegal conduct; consequently, Ownership Lens strictly formats all outputs as *"exposure indicators requiring human review"*, producing an evidence-backed audit ledger rather than automated accusations.

---

## Why FalkorDB is Non-Negotiable

In graph hackathons, a common pitfall is building an agent that merely uses a graph as "decoration"—an application that could just as easily run on PostgreSQL. In Ownership Lens, removing FalkorDB breaks the entire product.

### 1. The Depth 1 vs Depth 3 Contrast
Consider `MOSSACK FONSECA & CO. (SAMOA) LIMITED.` (Node ID `10001171`) evaluated against a sanctions watchlist containing `TIANSHENG INDUSTRY AND TRADING CO., LTD.` (Node ID `10000001`):
- **At Depth 1**: Zero direct connections exist between Mossack Fonseca Samoa and Tiansheng. The agent yields `clear` ("No indicators found within depth 1").
- **At Depth 3**: FalkorDB traverses 3 hops using weighted shortest paths (`algo.SPpaths`) and surfaces an indirect path via an intermediary and officer:
  `MOSSACK FONSECA` -> `[:intermediary_of]` -> `Samoan Entity` -> `[:officer_of]` -> `TIANSHENG`.
  The deterministic rules engine immediately triggers rule `SANCTION_PATH_FOUND` and escalates the investigation to **`escalate`**.

This depth toggle visually and mathematically demonstrates why shallow relational queries fail in anti-money laundering (AML) and know-your-customer (KYC) workflows.

### 2. Scratch Graph Graph Algorithms
When an entity is investigated, Ownership Lens constructs an isolated in-memory scratch graph in FalkorDB representing the local k-hop subnetwork. It then runs FalkorDB graph algorithms directly on that topology:
- **`algo.labelPropagation` & `algo.WCC`**: Identifies whether the target resides in the same structural community as a watchlisted entity even if weighted paths exceed standard search depths (`COMMUNITY_WATCHLIST` rule).
- **`algo.betweenness`**: Measures flow betweenness centrality to detect critical gatekeeper intermediaries (`CENTRALITY_SPIKE` rule).
- **`algo.pageRank`**: Ranks authority scores across nominee networks to pinpoint systemic corporate hubs (`PAGERANK_ANOMALY` rule).

### 3. Graph Memory via Case Nodes
Every completed investigation writes a `(:Case)` node back into the FalkorDB graph, bound by `[:ABOUT]` and `[:CITED]` relationships to the entities and evidence discovered. When future investigations touch related entities, `recall_cases` retrieves prior verdicts and evidence ledgers directly from the graph.

---

## Three Key Architectural Decisions

### 1. Typed Tools Instead of Free-Form Cypher
Many LLM graph agents prompt the language model to write raw Cypher queries. In production, this approach fails: models hallucinate non-existent relationship types, produce unindexed queries that cause timeouts, and introduce prompt injection vulnerabilities.

In Ownership Lens, the LLM never sees or writes raw Cypher. It chooses among six strictly typed, parameterized read tools implemented with the Python `mcp` SDK:
1. `resolve_entity(query)`
2. `ownership_chain(entity_id, max_depth)`
3. `shared_links(entity_id, max_depth)`
4. `path_between(source_id, target_id, max_depth)`
5. `cluster_view(entity_id, max_depth)`
6. `recall_cases(entity_id)`

### 2. The Deterministic Rules Engine
Language models are probabilistic text generators, not compliance officers. Having an LLM output "This entity is high risk" makes decisions impossible to audit.

In Ownership Lens, the verdict is determined **exclusively** by a deterministic Python rules layer (`core/rules.py`). Tool outputs are parsed into a structured evidence ledger. The rules evaluate calibrated thresholds against empirical dataset percentiles (e.g. officer degree $\ge 5$, community co-membership, path cost $\le 8.0$) and assign one of four immutable verdicts: `clear`, `review`, `escalate`, or `insufficient_evidence`. The LLM cannot alter the verdict.

### 3. Anti-Hallucination Verifier & Model Benchmarking
Even when restricted to writing explanatory memos, LLMs can fabricate names or addresses. We built a verifier (`core/verifier.py`) that cross-examines every named entity, officer, and address in the LLM's memorandum against the raw tool output from that exact run. If any unverified name appears, the memo is discarded and replaced with a deterministic template memo generated directly from the evidence ledger.

To ensure reliable tool selection, we benchmarked multiple models on the hosted NVIDIA endpoint using 10 standardized tool-calling scenarios. We deployed **`nvidia/nemotron-3-super-120b-a12b`**, achieving **7/10 tool accuracy** with mean latency under 3.8s, backed by a deterministic fallback loop that prevents downtime even under rate limits.

---

## Running It Locally

You can run the full stack (FalkorDB server, browser UI, and the FastAPI application) in under two minutes:

```bash
git clone https://github.com/GoDxVictoryRR/ACD-Agent.git
cd ACD-Agent
cp .env.example .env
docker compose up -d
```

Open `http://localhost:8000` to investigate offshore entities, toggle depth 1 versus depth 3, and explore the interactive Cytoscape graph canvas.

