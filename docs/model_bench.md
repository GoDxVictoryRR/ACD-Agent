# Model Benchmark: Tool Calling Accuracy & Live Runs

Evaluation of candidate NVIDIA-hosted text models on 10 canned corporate investigation prompts using 6 typed read-tool schemas from `core/tools.py`.

## Summary Table

| Model Name | Type | Tool Calls Correct | Accuracy | Mean Latency | Status |
|---|---|:---:|:---:|:---:|---|
| `nvidia/llama-3.3-nemotron-super-49b-v1.5` | Text | 0/10 | 0.0% | N/A | FAIL (410 Gone / EOL) |
| `nvidia/nemotron-3-super-120b-a12b` | Text | 7/10 | 70.0% | 3779 ms | **PASS** (Meets >= 7/10 Threshold) |
| `poolside/laguna-xs-2.1` | Text | 4/10 | 40.0% | 1151 ms | PARTIAL (Below 7/10) |

## Detailed Evaluation Per Prompt

### Model: `nvidia/llama-3.3-nemotron-super-49b-v1.5`
**Score**: 0/10 correct

| # | Prompt | Expected Tool | Result | Called Tool | Latency |
|---|---|---|---|---|:---:|
| 1 | Investigate entity GLAISDALE LIMITED and resolve its unique graph identifier. | `resolve_entity` | FAIL | `None` | 193 ms |
| 2 | Find the node identifier for DOM Limited to check compliance watchlist records. | `resolve_entity` | FAIL | `None` | 30 ms |
| 3 | Trace ownership and shareholder connections for entity 10024477 up to 2 hops. | `ownership_chain` | FAIL | `None` | 39 ms |
| 4 | Retrieve corporate control chain for entity 10028037 up to depth 3. | `ownership_chain` | FAIL | `None` | 104 ms |
| 5 | Identify shared officers and intermediaries connected to entity 10024477. | `shared_links` | FAIL | `None` | 93 ms |
| 6 | Check hub addresses and nominee officers for entity 10014876. | `shared_links` | FAIL | `None` | 39 ms |
| 7 | Find the shortest control path between node 10024477 and node 10189122. | `path_between` | FAIL | `None` | 46 ms |
| 8 | Is there an ownership path from source 10024477 to target 10028037? | `path_between` | FAIL | `None` | 40 ms |
| 9 | Compute centrality metrics, PageRank and betweenness for entity 10024477. | `cluster_view` | FAIL | `None` | 34 ms |
| 10 | Recall previous compliance case verdicts and findings recorded for entity 10024477. | `recall_cases` | FAIL | `None` | 41 ms |

### Model: `nvidia/nemotron-3-super-120b-a12b`
**Score**: 7/10 correct

| # | Prompt | Expected Tool | Result | Called Tool | Latency |
|---|---|---|---|---|:---:|
| 1 | Investigate entity GLAISDALE LIMITED and resolve its unique graph identifier. | `resolve_entity` | PASS | `resolve_entity` | 3012 ms |
| 2 | Find the node identifier for DOM Limited to check compliance watchlist records. | `resolve_entity` | PASS | `resolve_entity` | 1392 ms |
| 3 | Trace ownership and shareholder connections for entity 10024477 up to 2 hops. | `ownership_chain` | PASS | `ownership_chain` | 2167 ms |
| 4 | Retrieve corporate control chain for entity 10028037 up to depth 3. | `ownership_chain` | PASS | `ownership_chain` | 4316 ms |
| 5 | Identify shared officers and intermediaries connected to entity 10024477. | `shared_links` | NO_TOOL | `None` | 4691 ms |
| 6 | Check hub addresses and nominee officers for entity 10014876. | `shared_links` | PASS | `shared_links` | 2655 ms |
| 7 | Find the shortest control path between node 10024477 and node 10189122. | `path_between` | NO_TOOL | `None` | 7908 ms |
| 8 | Is there an ownership path from source 10024477 to target 10028037? | `path_between` | NO_TOOL | `None` | 6163 ms |
| 9 | Compute centrality metrics, PageRank and betweenness for entity 10024477. | `cluster_view` | PASS | `cluster_view` | 3672 ms |
| 10 | Recall previous compliance case verdicts and findings recorded for entity 10024477. | `recall_cases` | PASS | `recall_cases` | 1812 ms |

### Model: `poolside/laguna-xs-2.1`
**Score**: 4/10 correct

| # | Prompt | Expected Tool | Result | Called Tool | Latency |
|---|---|---|---|---|:---:|
| 1 | Investigate entity GLAISDALE LIMITED and resolve its unique graph identifier. | `resolve_entity` | FAIL | `None` | 239 ms |
| 2 | Find the node identifier for DOM Limited to check compliance watchlist records. | `resolve_entity` | PASS | `resolve_entity` | 1044 ms |
| 3 | Trace ownership and shareholder connections for entity 10024477 up to 2 hops. | `ownership_chain` | PASS | `ownership_chain` | 1031 ms |
| 4 | Retrieve corporate control chain for entity 10028037 up to depth 3. | `ownership_chain` | FAIL | `None` | 312 ms |
| 5 | Identify shared officers and intermediaries connected to entity 10024477. | `shared_links` | FAIL | `None` | 33 ms |
| 6 | Check hub addresses and nominee officers for entity 10014876. | `shared_links` | FAIL | `None` | 240 ms |
| 7 | Find the shortest control path between node 10024477 and node 10189122. | `path_between` | PASS | `path_between` | 1448 ms |
| 8 | Is there an ownership path from source 10024477 to target 10028037? | `path_between` | PASS | `path_between` | 1081 ms |
| 9 | Compute centrality metrics, PageRank and betweenness for entity 10024477. | `cluster_view` | FAIL | `None` | 15012 ms |
| 10 | Recall previous compliance case verdicts and findings recorded for entity 10024477. | `recall_cases` | FAIL | `None` | 15065 ms |

## Live 3x Investigation Runs (`docs/live_demo_runs.json`)

Verified live executions across all primary demo targets and controls against the NVIDIA endpoint (`nvidia/nemotron-3-super-120b-a12b`).

| Case Name | Run | Verdict | Det Verdict | Matches? | LLM Calls | Forced Calls | 429s | Memo Source | Verifier Result | Latency |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `GLAISDALE LIMITED` (D4) | 1 | **escalate** | `escalate` | **True** | 6 | 2 | 0 | `template` | `TEMPLATE_FALLBACK` | 62.4 s |
| `GLAISDALE LIMITED` (D4) | 2 | **escalate** | `escalate` | **True** | 4 | 4 | 0 | `template` | `TEMPLATE_FALLBACK` | 87.6 s |
| `GLAISDALE LIMITED` (D4) | 3 | **escalate** | `escalate` | **True** | 6 | 3 | 0 | `template` | `TEMPLATE_FALLBACK` | 61.0 s |
| `GLAISDALE LIMITED` (D1) | 1 | **clear** | `clear` | **True** | 5 | 3 | 0 | `template` | `TEMPLATE_FALLBACK` | 40.3 s |
| `GLAISDALE LIMITED` (D1) | 2 | **clear** | `clear` | **True** | 6 | 3 | 0 | `template` | `TEMPLATE_FALLBACK` | 39.1 s |
| `GLAISDALE LIMITED` (D1) | 3 | **clear** | `clear` | **True** | 7 | 3 | 0 | `template` | `TEMPLATE_FALLBACK` | 26.6 s |
| `Millex International Limited` (D2) | 1 | **review** | `review` | **True** | 3 | 2 | 0 | `template` | `TEMPLATE_FALLBACK` | 23.8 s |
| `Millex International Limited` (D2) | 2 | **review** | `review` | **True** | 3 | 2 | 0 | `template` | `TEMPLATE_FALLBACK` | 27.4 s |
| `Millex International Limited` (D2) | 3 | **review** | `review` | **True** | 3 | 2 | 0 | `template` | `TEMPLATE_FALLBACK` | 50.7 s |
| `OMNIA TECHNOLOGIES S.A.` (D2) | 1 | **clear** | `clear` | **True** | 4 | 4 | 0 | `llm` | **`PASSED`** | 36.2 s |
| `OMNIA TECHNOLOGIES S.A.` (D2) | 2 | **clear** | `clear` | **True** | 5 | 3 | 0 | `llm` | **`PASSED`** | 36.5 s |
| `OMNIA TECHNOLOGIES S.A.` (D2) | 3 | **clear** | `clear` | **True** | 4 | 3 | 0 | `llm` | **`PASSED`** | 40.2 s |
| `Dewburn Enterprises Inc.` (D1) | 1 | **insufficient_evidence** | `insufficient_evidence` | **True** | 4 | 3 | 0 | `template` | `TEMPLATE_FALLBACK` | 75.2 s |
| `Dewburn Enterprises Inc.` (D1) | 2 | **insufficient_evidence** | `insufficient_evidence` | **True** | 6 | 3 | 0 | `template` | `TEMPLATE_FALLBACK` | 72.0 s |
| `Dewburn Enterprises Inc.` (D1) | 3 | **insufficient_evidence** | `insufficient_evidence` | **True** | 5 | 3 | 0 | `template` | `TEMPLATE_FALLBACK` | 68.9 s |

*Note 1*: Traversal depth clamping in `agent/loop.py` (`args["max_depth"] = min(int(args.get("max_depth", depth)), depth)`) strictly guarantees that tool traversals never cross the requested investigation depth boundary, achieving 100% deterministic alignment across all 15 live runs.

## Recommendation & Decision

- **Selected Primary Text Model**: `nvidia/nemotron-3-super-120b-a12b`
- **Vision Model Replacement**: Replaced deprecated `meta/llama-3.2-11b-vision-instruct` with dedicated text model `nvidia/nemotron-3-super-120b-a12b`.
- **Anti-Hallucination Verifier**: For complex graphs with multiple findings, LLM memos frequently contain unverifiable assertions (e.g. "No other links", "Based on findings"). Invariant 6 rigorously catches these and reverts to deterministic template memos. For clean negative controls (`OMNIA TECHNOLOGIES S.A.`), the LLM memo verifier passed 3/3 times (`PASSED`).
- **Deterministic Rules & Fallback Guarantee**: Invariant 5 guarantees verdicts come solely from `core/rules.py`. Invariant 11 fallback to `agent/fallback.py` operates deterministically if NVIDIA API returns 429, timeout, or invalid format.