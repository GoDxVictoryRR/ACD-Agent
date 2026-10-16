---
name: p2-data-graph
description: "Loads an ICIJ Offshore Leaks subset into FalkorDB, defines the schema and indexes, measures size, finds demo cases and stops at a human gate. Use after p1 and whenever data or schema changes."
---

# p2: data and graph

Goal: a small, fast, real ownership graph where at least one entity looks clean at depth 1 but reaches a watchlist entity by depth 3.

## 1. Inspect before designing
Data must be in `data/raw/` (p0 group B). Print per CSV: header, row count, 3 sample rows. Expected but unverified: `nodes-entities.csv`, `nodes-officers.csv`, `nodes-intermediaries.csv`, `nodes-addresses.csv`, `nodes-others.csv`, `relationships.csv` (start/end node id, `rel_type`, dates, `sourceID`). Write the real column names and the distinct `rel_type` values with counts to `docs/data_notes.md`.

## 2. Pick the subset
Filter by source leak or jurisdiction. Starting guess: <=150k nodes, <=300k edges. Measure (step 5) and shrink until in-memory size is <= ~60MB; the Cloud cap is 100MB and you need room for Case nodes and scratch graphs. Keep only: id, name, jurisdiction/country, status, source, dates. Drop long text.
`data/make_seed.py`: raw -> `data/seed/*.csv` (committed; each file < 25MB). Add `data/seed/ATTRIBUTION.md` (ICIJ, ODbL/CC BY-SA, link, "filtered subset"). Raw stays gitignored.

## 3. Schema (`core/schema.cypher`, `core/config.py`)
- Labels: `Entity`, `Officer`, `Intermediary`, `Address`, `Other` (one per ICIJ node file).
- Relationship types: ICIJ `rel_type` values normalised to UPPER_SNAKE; keep an allowlist in `config.py`.
- Every edge gets `weight` from `EDGE_WEIGHT` in `config.py` (lower = stronger evidence): officer / beneficial / intermediary ~1-2, registered address ~3, ICIJ fuzzy matches (similar / same-name) ~4. Adjust after you see the real types.
- Case model (written in p3): `(:Case {id, entity_id, verdict, depth, created_at})-[:ABOUT]->(:Entity)` and `(:Case)-[:CITED]->(n)`.
- Indexes: `node_id` on every label; full-text on `name` for Entity/Officer/Intermediary/Address. Read the FalkorDB docs for exact syntax.

## 4. Loader `data/load.py`
- Idempotent. `--reset` drops and rebuilds; default skips when counts already match.
- Target from env (`FALKORDB_*`) so the same script loads local and Cloud.
- Batches of ~1000 with `UNWIND $rows AS r ...` and params. Relationship types cannot be parameters: one query per allowlisted type.
- Indexes before edges. Print counts per label/type and elapsed time.
- Expose `ensure_seed()` for the API (used when the graph is missing). It must finish well under 2 minutes on the target.

## 5. Measure and record in `docs/data_notes.md`
Counts, load time, in-memory size (the FalkorDB memory-usage command if the docs list one, else `docker stats`), p95 time of a 3-hop expansion from typical entities. If 3-hop > ~1 s: add limits or shrink.

## 6. Find demo cases `scripts/explore_demo.py`
Entities where the depth-1 shared-link count is low yet a watchlist candidate is reachable at weighted cost <= threshold within depth 3. Write the top 10 with paths to `docs/demo_cases.md`. Candidates must be entities/companies, not named private individuals.

> **HUMAN REQUIRED (gate):** show `docs/demo_cases.md`. Human picks 2-3 demo entities, 1 "no useful connections" entity, and the watchlist. Save to `data/demo.json` and `STATE.md`. Do not start p4 before this.

## 7. Fallback: synthetic data
If no candidate shows the depth-1 vs depth-3 contrast, or size/load targets cannot be met: `data/make_synthetic.py` (seeded RNG) producing ~20k nodes in the same schema with a realistic hub/degree distribution, 3 planted structures (nominee officer fan-out, shared-address cluster, 3-hop link to a watchlist entity) plus noise. README must say the data is synthetic. The rules allow it.

## Done when
`python data/load.py --reset` works locally, size and timings are recorded, demo cases are approved, loader tests on a tiny fixture pass, STATE.md is updated.
