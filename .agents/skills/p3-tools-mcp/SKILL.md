---
name: p3-tools-mcp
description: "Implements the 7 typed graph tools in core/tools.py, the FastMCP wrapper, the Case write-back and the tests. Use after p2 data is loaded."
---

# p3: tools and MCP

Before writing queries, read the FalkorDB docs pages you need via https://docs.falkordb.com/llms.txt . Verify every query in FalkorDB Browser (http://localhost:3000) or `scripts/q.py` on real data before coding it.

## Common
- Every tool returns a pydantic `ToolResult`: `{tool, params, status: ok|empty|unknown_entity|ambiguous|error, rows|paths, elapsed_ms, notes}`. The trace in the UI is built from these.
- Args validated with bounds (`max_depth` 1-3, `limit` <= 50, ids are strings). Row caps enforced in the query (`LIMIT`). Query timeouts set.
- Reads via `core.db.ro`. Relationship types only from the allowlist.

## Tools
| Tool | Inputs | Behaviour |
|---|---|---|
| `resolve_entity` | `name`, `limit<=5` | Full-text/prefix lookup. Exact case-insensitive match wins. `ambiguous` if >1 exact match or the top two candidates are not clearly separated; return candidates (id, name, label, jurisdiction). Nothing found -> `unknown_entity`. |
| `ownership_chain` | `entity_id`, `max_depth` | Paths from the entity to officers, intermediaries, addresses and other entities. Each path = list of `{id,name,label}` + relationship types. Cap 200 rows. |
| `shared_links` | `entity_id` | Hubs (Officer/Address/Intermediary) attached to the entity and how many other entities each hub touches. |
| `path_between` | `a_id`, `b_id`, `max_depth` | `CALL algo.SPpaths({sourceNode:a, targetNode:b, relTypes:[...], relDirection:'both', weightProp:'weight', pathCount:1}) YIELD path, pathWeight, pathCost` (verified `relDirection` supports `'both'`, `'outgoing'`, `'incoming'`). Return path(s) + `pathWeight`; `empty` when none within depth. |
| `cluster_view` | `entity_id`, `max_depth<=2`, `node_cap=500` | Copy the neighbourhood into scratch graph `case_<uuid8>` (truncate by degree if > cap; say so in `notes`). Run `algo.pageRank('Entity', 'OWNS')` (positional string args), `algo.betweenness({nodeLabels:['Entity'], relationshipTypes:['OWNS'], samplingSize:32, samplingSeed:42})` (config-map form, `samplingSeed` fixed for reproducibility), and `algo.wcc({nodeLabels:['Entity'], relationshipTypes:['OWNS']})` or `algo.labelPropagation({nodeLabels:['Entity'], relationshipTypes:['OWNS'], maxIterations:10})` (verified procedure names from live FalkorDB docs). Return top 5 per metric plus the entity's own rank, community id and community size. `finally`: delete the scratch graph. |
| `recall_cases` | `entity_id` | Prior `Case` nodes within 2 hops via shared nodes: id, verdict, date, shared node names. Limit 5. |
| `record_decision` | `entity_id, verdict, depth, evidence_ids, rule_ids` | Writes `Case` + `ABOUT` + `CITED` edges. Verdict must be in the enum. Idempotent on case id. Returns case id. |

Key shared-links query (adapt after seeing real labels):
```
MATCH (e:Entity {node_id:$id})-[r1]-(hub)-[r2]-(other:Entity)
WHERE (hub:Officer OR hub:Address OR hub:Intermediary) AND other.node_id <> $id
RETURN labels(hub)[0] AS hub_type, hub.name AS hub, count(DISTINCT other) AS linked
ORDER BY linked DESC LIMIT 10
```
Bind `r1`, `r2` (unreferenced relationships in a pattern are only existence-checked in FalkorDB; see https://docs.falkordb.com/cypher/known-limitations ).

## `record_decision` is not an LLM tool
The LLM is offered the six read tools only. The agent loop calls `record_decision` itself after the rules produce a verdict. Do not expose it in the OpenAI tool spec.

## MCP wrapper `mcp_server/server.py`
**Verified against MCP Python SDK README (https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md):**
- Import: `from mcp.server import MCPServer` (not `FastMCP`). The class name is `MCPServer`.
- Decorator: `@mcp.tool()` registers tools with their docstring as the description.
- Run via stdio: `mcp.run()` uses stdio transport by default. Entry point: `python -m mcp_server.server` (stdio, consumed by agent as a subprocess).
- In-process transport: the SDK supports stdio, Streamable HTTP, and SSE. For the agent loop in the same process, launch the MCP server as a subprocess and use the `stdio` client transport (`from mcp.client.stdio import stdio_client`). Do NOT attempt an in-process transport if the SDK version does not expose one — measure RSS impact of subprocess; Render free has 512MB total.
- Descriptions must be <= 2 sentences. The LLM reads them to decide which tool to call — be precise about inputs and output shape.
- One `@mcp.tool()` per tool. Thin wrapper over `core.tools`. No logic in the MCP layer.
- The MCP server belongs to the PRODUCT, not dev tooling. Keep it runnable in isolation for testing.

## Tests (`tests/test_tools.py`, tiny fixture graph `test_ownership` created in a fixture and deleted after)
unknown entity -> no further queries · ambiguous name · depth cap enforced · name containing quotes / Cypher fragments is harmless · a write attempted through a read tool fails · `path_between` returns the expected path and weight · scratch graph is deleted even when an algorithm call raises · `record_decision` idempotent · MCP wrapper lists exactly the 7 tools with valid schemas.

## Done when
`pytest -q` passes, each tool is run once against the real graph (log outputs and timings in `docs/data_notes.md`), STATE.md updated.
