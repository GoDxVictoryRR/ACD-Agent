# Model Benchmark: Tool Calling Accuracy

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
| 1 | Investigate entity Mossack Fonseca & Co. (Sam... | `resolve_entity` | FAIL | `None` | 193 ms |
| 2 | Find the node identifier for Tiansheng Indust... | `resolve_entity` | FAIL | `None` | 30 ms |
| 3 | Trace ownership and shareholder connections f... | `ownership_chain` | FAIL | `None` | 39 ms |
| 4 | Retrieve corporate control chain for entity 1... | `ownership_chain` | FAIL | `None` | 104 ms |
| 5 | Identify shared officers and intermediaries c... | `shared_links` | FAIL | `None` | 93 ms |
| 6 | Check hub addresses and nominee officers for ... | `shared_links` | FAIL | `None` | 39 ms |
| 7 | Find the shortest control path between node 1... | `path_between` | FAIL | `None` | 46 ms |
| 8 | Is there an ownership path from source 100056... | `path_between` | FAIL | `None` | 40 ms |
| 9 | Compute centrality metrics, PageRank and betw... | `cluster_view` | FAIL | `None` | 34 ms |
| 10 | Recall previous compliance case verdicts and ... | `recall_cases` | FAIL | `None` | 41 ms |

### Model: `nvidia/nemotron-3-super-120b-a12b`
**Score**: 7/10 correct

| # | Prompt | Expected Tool | Result | Called Tool | Latency |
|---|---|---|---|---|:---:|
| 1 | Investigate entity Mossack Fonseca & Co. (Sam... | `resolve_entity` | PASS | `resolve_entity` | 3012 ms |
| 2 | Find the node identifier for Tiansheng Indust... | `resolve_entity` | PASS | `resolve_entity` | 1392 ms |
| 3 | Trace ownership and shareholder connections f... | `ownership_chain` | PASS | `ownership_chain` | 2167 ms |
| 4 | Retrieve corporate control chain for entity 1... | `ownership_chain` | PASS | `ownership_chain` | 4316 ms |
| 5 | Identify shared officers and intermediaries c... | `shared_links` | NO_TOOL | `None` | 4691 ms |
| 6 | Check hub addresses and nominee officers for ... | `shared_links` | PASS | `shared_links` | 2655 ms |
| 7 | Find the shortest control path between node 1... | `path_between` | NO_TOOL | `None` | 7908 ms |
| 8 | Is there an ownership path from source 100056... | `path_between` | NO_TOOL | `None` | 6163 ms |
| 9 | Compute centrality metrics, PageRank and betw... | `cluster_view` | PASS | `cluster_view` | 3672 ms |
| 10 | Recall previous compliance case verdicts and ... | `recall_cases` | PASS | `recall_cases` | 1812 ms |

### Model: `poolside/laguna-xs-2.1`
**Score**: 4/10 correct

| # | Prompt | Expected Tool | Result | Called Tool | Latency |
|---|---|---|---|---|:---:|
| 1 | Investigate entity Mossack Fonseca & Co. (Sam... | `resolve_entity` | FAIL | `None` | 239 ms |
| 2 | Find the node identifier for Tiansheng Indust... | `resolve_entity` | PASS | `resolve_entity` | 1044 ms |
| 3 | Trace ownership and shareholder connections f... | `ownership_chain` | PASS | `ownership_chain` | 1031 ms |
| 4 | Retrieve corporate control chain for entity 1... | `ownership_chain` | FAIL | `None` | 312 ms |
| 5 | Identify shared officers and intermediaries c... | `shared_links` | FAIL | `None` | 33 ms |
| 6 | Check hub addresses and nominee officers for ... | `shared_links` | FAIL | `None` | 240 ms |
| 7 | Find the shortest control path between node 1... | `path_between` | PASS | `path_between` | 1448 ms |
| 8 | Is there an ownership path from source 100056... | `path_between` | PASS | `path_between` | 1081 ms |
| 9 | Compute centrality metrics, PageRank and betw... | `cluster_view` | FAIL | `None` | 15012 ms |
| 10 | Recall previous compliance case verdicts and ... | `recall_cases` | FAIL | `None` | 15065 ms |

## Recommendation & Decision

- **Selected Primary Text Model**: `nvidia/nemotron-3-super-120b-a12b`
- **Vision Model Replacement**: Replaced deprecated `meta/llama-3.2-11b-vision-instruct` with dedicated text model `nvidia/nemotron-3-super-120b-a12b`.
- **Fallback Guarantee**: Invariant 11 fallback to `agent/fallback.py` operates deterministically if NVIDIA API returns 429, timeout, or invalid format.

*Generated: 2026-10-17 12:56:13 UTC*