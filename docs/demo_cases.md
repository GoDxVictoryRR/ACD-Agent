# Demo Cases & Negative Controls: Real ICIJ Offshore Leaks

This document specifies the primary demo case, isolated entity, case recall entity, and negative controls tested and verified on the live **ICIJ Offshore Leaks (Panama Papers Samoa/Seychelles subset)** from `data/demo.json`.

---

## 1. Primary Depth Contrast Case (Active Demo)

Demonstrates the critical value of multi-hop graph traversal. At depth 1, the entity appears standard and unconnected to flagged targets (clear). At depth 4, multi-hop traversal across corporate directorship links uncovers an authentic ownership path to a watchlisted entity and flips the verdict to `escalate`.

- **Source Entity**: `GLAISDALE LIMITED` (`node_id: 10024477`)
  - Jurisdiction: Samoa (`SAM`)
  - Source: Panama Papers
  - Status: Active
  - Degree: 5 links (1 officer, 1 address, 3 intermediaries)
- **Watchlist Entity**: `DOM Limited` (`node_id: 10189122`)
  - Label: `Entity`
  - Jurisdiction: Samoa (`SAM`)
  - Source: Panama Papers
  - Status: Defaulted
  - Degree: 5 links
- **Traversed Path (Depth 4)**:
  `GLAISDALE LIMITED (Entity 10024477)`
  `-[OFFICER_OF]-> Rachel Erickson (Officer 12116679)`
  `-[OFFICER_OF]-> NEWCOMBE LIMITED (Entity 10028037)`
  `-[OFFICER_OF]-> ANDREW MORAY STUART (Officer 12151058)`
  `-[OFFICER_OF]-> DOM Limited (Watchlist Entity 10189122)`
- **Weighted Path Cost**: `4.0` (weight threshold <= 8.0)
  - 4 x `OFFICER_OF` @ 1.0 = 4.0
- **Shortest Path Verification**:
  - `algo.SPpaths` confirmed: `hops = 4`, `path_weight = 4.0`.
  - Zero watchlist paths exist within depth 1, 2, or 3.
- **Verdicts by Depth**:
  - **Depth 1**: `clear` ("No exposure indicators found within depth 1")
  - **Depth 4**: `escalate` (Rule `WATCHLIST_PATH` triggered: cost 4.0 <= 8.0)

---

## 2. Isolated / Low-Link Entity

Entities with minimal or no graph connections, demonstrating that sparse structures honestly abstain rather than guessing.

- **Entity**: `Dewburn Enterprises Inc.` (`node_id: 10000290`)
  - Jurisdiction: Samoa (`SAM`)
  - Degree: 1 link (connected to single officer `David G. Baker`)
  - Verdicts: Depth 1 `insufficient_evidence`, Depth 4 `insufficient_evidence` (degree < MIN_LINKS=2)

---

## 3. Related Entity for Case Memory Recall

Demonstrates the read/write graph feedback loop: writing an investigation verdict as a `Case` node allows subsequent investigations on connected entities to recall prior decisions.

- **Primary Investigation**: Investigate `GLAISDALE LIMITED` -> verdict `escalate`, recorded with `record_decision`.
- **Related Query Entity**: `NEWCOMBE LIMITED` (`node_id: 10028037`)
  - Shares corporate directorship links (`Rachel Erickson`).
  - Calling `recall_cases("10028037")` immediately recalls the prior case node (`verdict: escalate`).

---

## 4. Negative Controls (6 Real Structures)

Real offshore structures from the ICIJ dataset that exhibit significant graph connectivity (multiple officers, intermediaries, or addresses) but **must not escalate** because they have no watchlist connection.

| # | Entity Name | Node ID | Degree | Verdict (D1) | Verdict (D4) | Active Indicators |
|---|---|---|---|---|---|---|
| 1 | `Skytrack Investments Limited` | `10017419` | 3 | `clear` | `clear` | None (0 findings) |
| 2 | `OMNIA TECHNOLOGIES S.A.` | `10000280` | 5 | `clear` | `clear` | None (0 findings) |
| 3 | `GAO SHENG LIMITED` | `10028434` | 4 | `clear` | `clear` | Intermediary Concentration (Low) |
| 4 | `KIRBY GARDENS LTD.` | `10022468` | 4 | `clear` | `clear` | Intermediary Concentration (Low) |
| 5 | `Millex International Limited` | `10014876` | 4 | `review` | `review` | Nominee Officer Hub, Intermediary Hub (Medium/Low; never escalates) |
| 6 | `SINOWAY HOLDINGS LTD.` | `10189507` | 4 | `clear` | `clear` | Intermediary Concentration (Low) |

---

## 5. Active Benchmark Dossier Summary (`data/demo.json`)

| Entity Name | Depth 1 | Depth 4 | Target / Note |
|---|---|---|---|
| `GLAISDALE LIMITED` | `clear` | `escalate` | Flips at depth 4 to `DOM Limited` via `Rachel Erickson` -> `NEWCOMBE LIMITED` -> `ANDREW MORAY STUART` |
| `Millex International Limited` | `review` | `review` | Nominee Officer Hub, Intermediary Hub (Medium/Low; never escalates) |
| `OMNIA TECHNOLOGIES S.A.` | `clear` | `clear` | Connected entity with no high-risk hubs or watchlist connections |
| `Dewburn Enterprises Inc.` | `insufficient_evidence` | `insufficient_evidence` | Low-link entity (degree 1 < MIN_LINKS=2) |
