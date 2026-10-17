# Demo Cases & Negative Controls: Real ICIJ Offshore Leaks & Synthetic

This document specifies the primary demo case, isolated entity, case recall entity, and negative controls tested and verified on the live **ICIJ Offshore Leaks (Panama Papers Samoa/Seychelles subset)** and the **Synthetic** fallback dataset.

---

## 1. Primary Depth Contrast Case (PROVISIONAL)

Demonstrates the critical value of multi-hop graph traversal. At depth 1 and depth 2, the entity has no risk escalation. At depth 3, the ownership path reaches a watchlisted entity and flips the verdict to `escalate`.

- **Source Entity**: `MOSSACK FONSECA & CO. (SAMOA) LIMITED.` (`node_id: 10001171`)
  - Jurisdiction: Samoa (`SAM`)
  - Source: Panama Papers
  - Status: Active
  - Name uniqueness: Exactly 1 entity with this name in the dataset
- **Watchlist Entity**: `TIANSHENG INDUSTRY AND TRADING CO., LTD.` (`node_id: 10000001`)
  - Label: `Entity` (Entity nodes only; never Officer persons)
  - Jurisdiction: Samoa (`SAM`)
  - Source: Panama Papers
  - Status: Defaulted
  - Name uniqueness: Exactly 1 entity with this name in the dataset
- **Traversed Path (Depth 3)**:
  `MOSSACK FONSECA & CO. (SAMOA) LIMITED. (Entity)`
  `-[SAME_AS]-> MOSSACK FONSECA & CO. (SAMOA) LIMITED (Entity)`
  `-[OFFICER_OF]-> MOSSFON SUBSCRIBERS LTD. (Officer)`
  `-[OFFICER_OF]-> TIANSHENG INDUSTRY AND TRADING CO., LTD. (Entity)`
- **Weighted Path Cost**: `6.0` (weight threshold <= 8.0)
  - `SAME_AS`: 4.0
  - `OFFICER_OF`: 1.0
  - `OFFICER_OF`: 1.0
  - Total = 6.0
- **Shortest Path Verification**:
  - `algo.SPpaths` confirmed: `hops = 3`, `path_weight = 6.0`.
  - Bounded BFS confirmed: Zero paths exist at depth 1 or depth 2.
- **Verdicts by Depth**:
  - **Depth 1**: `clear` (No watchlist entity in range; low intermediary concentration indicator only)
  - **Depth 2**: `clear` (No watchlist entity in range)
  - **Depth 3**: `escalate` (Rule `WATCHLIST_PATH` triggered: cost 6.0 <= 8.0)

---

## 2. Isolated / Low-Link Entity (PROVISIONAL)

Entities with minimal or no graph connections, demonstrating that sparse structures do not trigger spurious risk findings.

- **Entity**: `Dewburn Enterprises Inc.` (`node_id: 10000290`)
  - Jurisdiction: Samoa (`SAM`)
  - Degree: 1 link (connected to single officer `David G. Baker`)
  - Verdicts: Depth 1 `clear`, Depth 2 `clear`, Depth 3 `clear`
- **Alternative (0-link)**:
  - If an entity is queried with 0 connections, `evaluate()` returns `insufficient_evidence` per `MIN_LINKS = 1`.

---

## 3. Related Entity for Case Memory Recall (PROVISIONAL)

Demonstrates the read/write graph feedback loop: writing an investigation verdict as a `Case` node allows subsequent investigations on connected entities to recall prior decisions.

- **Primary Investigation**: Investigate `MOSSACK FONSECA & CO. (SAMOA) LIMITED.` -> verdict `escalate`, recorded with `record_decision`.
- **Related Query Entity**: `TIANSHENG INDUSTRY AND TRADING CO., LTD.` (`node_id: 10000001`)
  - Shares the investigation path and connection nodes.
  - Calling `recall_cases("10000001")` immediately recalls the primary case node (`case_id: case_...`, verdict `escalate`, depth `3`).

---

## 4. Negative Controls (PROVISIONAL - 6 Real Structures)

Real offshore structures from the ICIJ dataset that exhibit significant graph connectivity (multiple officers, intermediaries, or addresses) but **must not escalate** because they have no watchlist connection.

| # | Entity Name | Node ID | Degree | Verdict (D1) | Verdict (D3) | Active Indicators |
|---|---|---|---|---|---|---|
| 1 | `Skytrack Investments Limited` | `10017419` | 3 | `clear` | `clear` | None (0 findings) |
| 2 | `OMNIA TECHNOLOGIES S.A.` | `10000280` | 5 | `clear` | `clear` | None (0 findings) |
| 3 | `GAO SHENG LIMITED` | `10028434` | 4 | `clear` | `clear` | Intermediary Concentration (Low) |
| 4 | `KIRBY GARDENS LTD.` | `10022468` | 4 | `clear` | `clear` | Intermediary Concentration (Low) |
| 5 | `Millex International Limited` | `10014876` | 4 | `review` | `review` | Nominee Officer Hub, Intermediary Hub (Medium/Low; never escalates) |
| 6 | `SINOWAY HOLDINGS LTD.` | `10189507` | 4 | `clear` | `clear` | Intermediary Concentration (Low) |

---

## 5. Synthetic Fallback Demo Cases (Reference)

If running with `DATA_SOURCE=synthetic`, the following planted cases are used:

| Entity Name | Depth 1 | Depth 3 | Target / Note |
|---|---|---|---|
| `Blue Star Maritime Holdings Ltd` | `clear` | `escalate` | Flips at depth 3 to `Ironclad Sanctions Entity Inc` via `Marcus Sterling` -> `Apex Nominees Ltd` |
| `Silverline Capital Management Ltd` | `review` | `review` | Nominee Officer Hub `John Alexander Vance` (50+ shells) |
| `Orion Global Logistics Corp` | `review` | `review` | Address Hub `Suite 301, St. James Court` (60+ companies) |
| `Solitary Enterprises Ltd` | `clear` | `clear` | Clean solitary entity with 1 address |
