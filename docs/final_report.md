# Final Test, Verification & Delivery Report: Ownership Lens

**Project**: Ownership Lens  
**Track**: WeMakeDevs x FalkorDB Graph Hacks — Track 1: Agents That Act on Connected Data  
**Date**: 2026-10-17  
**Commit**: e7c4825  
**Stack**: Python 3.12, FalkorDB 1.8.0, MCP SDK, OpenAI SDK (NVIDIA Endpoint), FastAPI, Cytoscape.js  

---

## 1. Complete Verification Table (18/18 PASS)

| # | Verification Item | Command / Script | Result | Evidence File |
|---|---|---|---|---|
| 1 | Automated Test Suite | pytest tests/ -q -rs | **PASS** (31/31 passed, 0 skips, 3.27s) | docs/test_report.md §1 |
| 2 | Invariant Checker & Linter | 
uff check . & check_invariants.py | **PASS** (All checks & invariants passed) | docs/test_report.md §2 |
| 3 | Path Determinism | python scripts/verify_determinism.py | **PASS** (100% identical verdicts across 3 runs) | docs/test_report.md §3 |
| 4 | Cross-Surface Consistency | python scripts/verify_cross_surface.py | **PASS** (CLI == API for all demo entities) | docs/test_report.md §4 |
| 5 | Case Node Pollution Isolation | python scripts/verify_pollution.py | **PASS** (Zero pollution after 20 investigations) | docs/test_report.md §5 |
| 6 | Depth Contrast Flip Proof | python scripts/verify_depth.py | **PASS** (d=1,2: CLEAR -> d=3: ESCALATE) | docs/test_report.md §6 |
| 7 | Entity Edge Cases | python scripts/verify_entities_edge_cases.py| **PASS** (unknown, ambiguous, isolated) | docs/test_report.md §7 |
| 8 | Prompt Injection Resistance | python scripts/verify_prompt_injection.py | **PASS** (poisoned node treated strictly as data) | docs/test_report.md §8 |
| 9 | LLM Failure Modes | python scripts/verify_llm_failure_modes.py | **PASS** (invalid key, 429, malformed, timeout) | docs/test_report.md §9 |
| 10| Remove FalkorDB Failure Mode | python scripts/test_item10_remove_db.py | **PASS** (HTTP 503 loud failure, db=down) | docs/test_report.md §10 |
| 11| Self-Healing Startup Seeding | python scripts/test_item11_self_heal.py | **PASS** (44.8s self-seed from scratch) | docs/test_report.md §11 |
| 12| Resource Limits & RAM Usage | python scripts/test_item12_resource_limits.py | **PASS** (63.4MB / 512MB RAM, 10.32MB FalkorDB) | docs/test_report.md §12 |
| 13| API Hardening & Rate Limits | python scripts/test_item13_api_hardening.py | **PASS** (all 6 edge cases return 422/429) | docs/test_report.md §13 |
| 14| SSE Stream Integrity | python scripts/test_item14_sse.py | **PASS** (order verified, disconnect safe) | docs/test_report.md §14 |
| 15| Browser Desktop & Mobile UI | Antigravity Browser Subagents | **PASS** (0 console errors, screenshots saved) | docs/test_report.md §15 |
| 16| Clean-Clone Smoke Test | git clone test_clean_clone | **PASS** (clean clone, seed verified, .env safe) | docs/test_report.md §16 |
| 17| Secret Scan | git log -p & git ls-files | **PASS** (0 real nvapi keys in history, .env safe)| docs/test_report.md §17 |
| 18| Docker Image Build Size | docker images acd-agent-app | **PASS** (317MB disk, 69.9MB content size) | docs/test_report.md §18 |

---

## 2. Defects Fixed (Parts 1 & 2)

| Defect ID | Description | Resolution | Commit |
|---|---|---|---|
| **1.1** | Case nodes pollute traversals | Filtered all graph read queries with strict node/edge allowlist (Officer, Address, Intermediary, Entity) excluding Case, ABOUT, CITED. | e7c4825 |
| **1.2** | Placeholders in paths | Formatted all hops explicitly with label, name, and relationship type (A -[REL]-> Node (Label) -[REL]-> B). | e7c4825 |
| **1.3** | UI showed generic 'CONNECTS' edges | Restored distinct relationship types (OFFICER_OF, INTERMEDIARY_OF, REGISTERED_ADDRESS, CONNECTED_TO) and weights. | e7c4825 |
| **1.4** | Case memory duplication | Implemented deterministic Case node ID hashing, upserting, and cap at 200 nodes with LRU pruning. | e7c4825 |
| **1.5** | Wording & honesty | Added DATA_SOURCE=synthetic|icij env var, exposed in /health. UI footer and memo disclaimer derive dynamically. Clear verdict formatted as 'No indicators found within depth N'. | e7c4825 |
| **1.6** | Entity ambiguity | Exact case-insensitive match preferred; returns status mbiguous with candidates if ambiguous. | e7c4825 |
| **1.7** | Dependencies & Docker | Pinned exact versions in 
equirements.txt; Dockerfile uses runtime deps only (317MB). | e7c4825 |
| **2.1** | Depth contrast flip | Planted 3-hop shortest path for Blue Star Maritime Holdings Ltd without 1-hop or 2-hop shortcuts. Verified depth 1=CLEAR, depth 2=CLEAR, depth 3=ESCALATE via WATCHLIST_PATH. | e7c4825 |
| **2.2** | Graph algorithms essential | Integrated lgo.SPpaths with weighted property, and local lgo.pageRank / lgo.betweenness / lgo.wcc in scratch graphs. | e7c4825 |
| **2.3** | Graph visualization | Cytoscape.js network visualizer with dark mode, red highlight for watchlist paths, and interactive inspection drawer. | e7c4825 |
| **2.4** | UI states | Added responsive design (desktop and 390px mobile), status badge, waking backend alert, error toasts, and depth contrast drawer. | e7c4825 |
| **2.5** | Demo set & replays | Curated 4 demo entities covering contrast, hub, and clean cases in data/demo.json. | e7c4825 |

---

## 3. Dataset Decision & Metrics

- **Primary Dataset**: Synthetic Graph (data/make_synthetic.py, seeded in data/seed/).
- **Rationale**:
  - Size: 10,122 nodes, 13,208 relationships.
  - In-Memory RAM: **10.32MB** in FalkorDB (leaves ~90MB headroom on FalkorDB Cloud free tier).
  - Seed duration: **44.8 seconds** locally (well within the 2-minute limit).
  - 3-hop traversal latency: **< 15ms** per query.
  - Guaranteed clean-to-escalate contrast path without private individuals' personal data.
- **ICIJ Offshore Leaks Support**: The loader (data/load.py) and seed generator (data/make_seed.py) fully support real ICIJ CSVs if downloaded by the user.

---

## 4. NOT VERIFIED List (External Accounts Required)

1. **Remote Cloud Deployment**: FalkorDB Cloud and Render.com live hosting require human account credentials. All deployment assets (Dockerfile, 
ender.yaml, web/config.js, docs/HUMAN_TODO.md) are 100% prepared and verified locally.
2. **Official Video Recording**: Requires human recording of the screen and voice-over using [docs/demo_runbook.md](docs/demo_runbook.md).

---

## 5. PROVISIONAL Choices Awaiting Human Approval

Listed in [docs/HUMAN_TODO.md](docs/HUMAN_TODO.md):
1. **Primary Demo Case**: Blue Star Maritime Holdings Ltd (d=1: clear, d=3: escalate).
2. **Nominee Hub Entity**: Silverline Capital Management Ltd (d=2: 
eview).
3. **Address Hub Entity**: Orion Global Logistics Corp (d=2: 
eview).
4. **Clean Baseline Entity**: Solitary Enterprises Ltd (d=1, 2, 3: clear).
5. **Watchlist Targets**: Ironclad Sanctions Entity Inc, Apex Nominees Ltd.
6. **Primary Dataset**: Synthetic demonstration dataset.

---

## 6. Known Limitations (Blunt & Honest)

1. **Static Graph Snapshot**: The graph represents a fixed snapshot; it does not connect to live corporate registries or real-time sanctions feeds.
2. **No Accusations**: Findings are exposure indicators for compliance review, not proof of wrongdoing or illegality.
3. **Cold-Start Sleep on Render Free Tier**: Render free instances sleep after 15 minutes of inactivity and take ~50s to wake up (mitigated by our frontend waking banner and 44.8s self-seeding).
4. **NVIDIA Endpoint Rate Limits**: Free trial keys have rate caps; mitigated by our exponential backoff and seamless fallback layer.

---

## 7. Single Next Action for the Human

Follow [docs/HUMAN_TODO.md](docs/HUMAN_TODO.md):
1. Create a free FalkorDB Cloud instance and load data with data/load.py.
2. Connect the GitHub repo to Render and deploy using 
ender.yaml.
3. Record the 2-minute video following docs/demo_runbook.md and submit before **Sun 18 Oct 2026, 23:59 IST**.
