# Building Ownership Lens: How Connected Data Solves the Offshore Shell Company Puzzle

*Track 1 Submission: Agents That Act on Connected Data*

Offshore corporate structures are rarely transparent. A single entity registered in the British Virgin Islands or Panama typically appears entirely benign in isolation: one registered agent, one postal box, and an unfamiliar individual listed as director. In a standard relational database or SQL table, querying this entity produces a clean bill of health.

Yet beneath that single row of tabular data lies an extensive web of interconnected relationships. That individual director may be a nominee serving on the boards of dozens of shell companies. That postal box might house sixty separate corporate entities. And three hops away, through an offshore management intermediary, that clean entity may be directly connected to an entity on an international sanctions watchlist.

To solve this problem for Track 1 of the WeMakeDevs x FalkorDB Graph Hacks hackathon, we built **Ownership Lens**—an autonomous graph agent that navigates offshore control structures using FalkorDB, MCP tool calling, and deterministic compliance rules.

---

## Why a Graph Database is Non-Negotiable

If you remove the graph database from an application and the application still works, the graph was merely decorative. In Ownership Lens, FalkorDB is the engine that drives every single decision.

Without multi-hop graph traversal:
1. **Depth 1 vs Depth 3 Contrast**: At depth 1, the target entity `Blue Star Maritime Holdings Ltd` appears to have zero risk indicators. The verdict is `CLEAR` or `INSUFFICIENT EVIDENCE`. But when FalkorDB traverses 3 hops using weighted shortest paths (`algo.SPpaths`), the verdict flips to `ESCALATE` because an indirect path reaches a sanctioned entity.
2. **Nominee and Address Hubs**: Aggregating two-hop neighbors (`(e)-[r1]-(hub)-[r2]-(other:Entity)`) surfaces corporate officers and addresses that link to dozens of other entities.
3. **Graph Memory**: Every investigation outcome is written back as a `(:Case)` node connected with `[:ABOUT]` and `[:CITED]` relationships. Subsequent investigations query historical graph neighbors to recall prior cases.

---

## Three Key Architectural Decisions

### 1. Typed Tools Instead of Free-Form Cypher
Many LLM graph agents prompt the language model to write raw Cypher queries. In production, this approach fails: models hallucinate non-existent relationship types, produce unindexed queries that time out, and introduce prompt injection risks.

In Ownership Lens, the LLM never sees or writes raw Cypher. It chooses among six strictly typed, parameterized read tools implemented with the Python `mcp` SDK: `resolve_entity`, `ownership_chain`, `shared_links`, `path_between`, `cluster_view`, and `recall_cases`.

### 2. The Deterministic Rules Engine
Language models are probabilistic text generators, not compliance officers. Having an LLM output "This entity is high risk" makes decisions impossible to audit.

In Ownership Lens, the verdict is determined **exclusively** by a deterministic Python rules layer (`core/rules.py`). Tool outputs are parsed into a structured evidence ledger. The rules check thresholds (e.g. officer degree >= 5, path cost <= 8.0) and assign the verdict: `clear`, `review`, `escalate`, or `insufficient_evidence`. The LLM's only role is to write a readable, concise memorandum explaining those findings.

### 3. The Anti-Hallucination Verifier
Even when constrained to writing memos, language models can invent plausible-sounding names. We built an automated verifier (`core/verifier.py`) that cross-examines every entity, person, and address name in the LLM's text against the raw graph data returned during that specific run. If any unverified name is detected, the LLM memo is discarded, and a deterministic template memo generated from the ledger is used instead.

---

## An Honest Limitation

Offshore leaks data (such as the ICIJ Offshore Leaks database) reflects historical corporate filings, not real-time registry snapshots. Furthermore, inclusion in an offshore leaks dataset is not proof of wrongdoing or illegal conduct. For this reason, Ownership Lens strictly formats all conclusions as "exposure indicators requiring human review," providing compliance teams with an evidence-backed audit trail rather than automated accusations.

---

## Running It Locally

You can launch the entire stack (FalkorDB server, browser GUI, and the FastAPI/web app) with a single command:

```bash
git clone https://github.com/GoDxVictoryRR/ACD-Agent.git
cd ACD-Agent
cp .env.example .env
docker compose up -d
```

Open `http://localhost:8000` to run an investigation, compare depth 1 versus depth 3, and explore the interactive Cytoscape subnetwork.
