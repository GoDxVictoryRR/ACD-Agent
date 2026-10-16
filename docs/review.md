# Hostile Judge Review: Ownership Lens

*An adversarial audit evaluating the codebase against strict hackathon scoring criteria.*

---

### 1. Which verdict would a domain expert call wrong, and why? Is the language accusatory anywhere?
- **Audit Finding**: In early iterations of graph agents, developers often classify entities as "fraudulent" or "guilty" based purely on graph distance. In financial compliance, being 3 hops from a sanctioned entity is an exposure risk requiring Enhanced Due Diligence (EDD), not proof of illegality.
- **Resolution**: Every user-facing string across the UI, rules, and prompts uses calibrated regulatory phrasing: *"exposure indicators requiring human review"*. The words "fraud", "criminal", and "guilty" are strictly prohibited and tested for in the unit test suite.

### 2. Where does the product still work if FalkorDB is removed?
- **Audit Finding**: Nowhere. If FalkorDB is offline or returns an error, `/health` immediately reports `db: "down"` and `/investigate` rejects runs. The system never falls back to an LLM-only guess. Without FalkorDB, no nodes can be resolved, no paths can be traversed, and no verdict can be computed.

### 3. Is every algorithm used because it changes a decision?
- **Audit Finding**: Algorithms must serve a functional purpose rather than acting as visual decoration.
- **Resolution**:
  - `algo.SPpaths`: Essential for `WATCHLIST_PATH`. It computes the weighted shortest path between the target entity and watchlist entities using directional evidence weights.
  - `algo.pageRank` & `algo.betweenness`: Used in `cluster_view` to score node importance in local shell company clusters.
  - `algo.wcc`: Identifies weakly connected corporate component groupings.
  - Geographic A* was evaluated and discarded because corporate ownership networks are topological, not geographic.

### 4. Which claims in the README or UI are not demonstrated by a test or demo case?
- **Audit Finding**: The claim that "Depth 1 vs Depth 3 flips the verdict" must be verified across both tests and live data.
- **Resolution**: Verified by `tests/regression/test_regression.py` on `Blue Star Maritime Holdings Ltd` (Depth 1 = `insufficient_evidence` / `clear`; Depth 3 = `escalate`). Demonstrated interactively by the "Compare D1 vs D3" button in the UI.

### 5. What breaks under 5 judges clicking at once?
- **Audit Finding**: A burst of simultaneous requests could exceed LLM rate limits or exhaust Render's 512MB RAM.
- **Resolution**:
  - In-memory concurrency semaphore limits simultaneous runs to 2 (`CONCURRENT_INVESTIGATIONS = 2`).
  - IP-based token bucket prevents API abuse (`RATE_LIMIT_INVESTIGATIONS_PER_HOUR = 6`).
  - LLM response cache (`cache/`) caches identical prompt runs to conserve quota.
  - If rate limits occur, the agent loop gracefully degrades to the deterministic fallback path without crashing.

### 6. Which file would the human fail to explain?
- **Audit Finding**: Overly abstracted agent frameworks (e.g. LangChain or Graphiti) hide control flow inside deep call stacks.
- **Resolution**: All logic is written in plain, transparent Python:
  - `core/db.py`: 130 lines of direct FalkorDB wrapper.
  - `core/rules.py`: Plain conditional checks returning pydantic findings.
  - `agent/loop.py`: Straightforward while-loop handling OpenAI tool calls.
  - Every component is fully explained in `docs/EXPLAIN.md`.
