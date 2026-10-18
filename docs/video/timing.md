# Video Scene Timing & Evidentiary Claim Ledger

This ledger details each recorded clip, its verified duration (measured via `ffprobe`), on-screen visual elements, and the exact Track 01 submission claim demonstrated.

Total video runtime across all 11 clips: **297.68 seconds (~5 min 00 sec)**. In final post-production, narration pacing, audio lead-ins, and editing holds bring total video duration to **~5 min 30 sec**.

---

## Clip Breakdown Table

| Clip | Duration (s) | On-Screen Visuals | Evidentiary Claim Shown | Track 01 Indicator |
|---|---|---|---|---|
| **s01.mp4** | 20.28s | Slide: "Ownership Lens: who is really behind a company?"; animated corporate ownership chain (`Company -> Director -> Company -> Director -> Company`); dashed bracket on first hop: "Standard compliance check stops here". | Direct relational checks miss multi-hop concealed control structures. | Context Hook |
| **s02.mp4** | 23.84s | Slide: "Graph Hacks \| Track 01 \| Agents That Act on Connected Data"; 5 evaluation checklist items appear sequentially at 3s intervals with green checkmarks. | Overview of the 5 contest criteria for Track 01 graph agents. | Contest Alignment |
| **s03.mp4** | 22.76s | Proof page showing verified FalkorDB telemetry: **51,940 nodes and 58,875 relationships**; smooth transition to live UI footer showing ICIJ attribution and regulatory disclaimer. | Provenance: Real ICIJ Offshore Leaks graph scale with legal disclaimer ("Exposure indicators requiring human review"). | Legal Provenance |
| **s04.mp4** | 26.12s | Live UI: Target `GLAISDALE LIMITED`, watchlist `DOM Limited`. Depth 1 returns **"No indicators found within depth 1"** (5 links). Click "Compare D1 vs D4": side-by-side view renders **red multi-hop path** and hop banner (`GLAISDALE -> Rachel Erickson -> NEWCOMBE -> Andrew Moray Stuart -> DOM Limited`). Evidence ledger highlights `WATCHLIST_PATH` row with weighted cost 4.0. | Multi-hop graph traversal flips verdict from CLEAR at depth 1 to ESCALATE at depth 4. | **Checklist 1 & 5** (Multi-hop reasoning & Explainable results) |
| **s05.mp4** | 23.64s | Agent Execution Trace Console: smooth inspection of typed tool invocations (`resolve_entity`, `ownership_chain`, `shared_links`, `path_between`, `cluster_view`), execution latency in ms, and `via: mcp` tags. | Graph algorithms invoked as typed tools via Model Context Protocol (MCP). | **Checklist 2 & 3** (Algorithms as tools & Tool selection via MCP) |
| **s05b.mp4** | 60.24s | Real-time AI agent mode execution: `toggleAiMode` checked, `NVIDIA_MODEL` (`nvidia/nemotron-3-super-120b-a12b`) autonomously issuing tool calls with live elapsed timer and streaming trace. | Autonomous LLM agent investigation loop (intended to be sped up 2-3x in video editor). | Live AI Agent Loop |
| **s06.mp4** | 22.24s | Verdict card showing case write-back confirmation. Target `NEWCOMBE LIMITED` run at depth 2: holds 5s on `#recalledCard` ("Prior Cases Recalled") displaying `GLAISDALE LIMITED` case recalled via shared director `Rachel Erickson`. | Graph write-back & recall: investigation decisions stored as `(:Case)` nodes and retrieved in future investigations. | **Checklist 4** (Actions from the graph) |
| **s07.mp4** | 25.16s | Investigation memorandum card showing "Memo source: deterministic template" and verifier status. Investigation of isolated node `Dewburn Enterprises Inc.` yields `INSUFFICIENT_EVIDENCE`. Transition to `07_injection.html` proving prompt injection immunity. | The LLM cannot alter the compliance verdict; deterministic rules govern outcomes. | Anti-Hallucination & Invariant 5 |
| **s08.mp4** | 31.08s | Carousel of static proof pages (4-5s each): `01_pytest.html` (53 passed), `02_invariants.html` (6 invariants), `03_ablation.html`, `04_exposure.html` (0 of 30 controls), `05_latency_memory.html` (0.23s p95, 41MB RAM), `06_stopped.html` (503 when FalkorDB stopped). | Comprehensive evidentiary proof: regression suite, ablation baseline, SLA, and database necessity. | Rigorous Verification |
| **s09.mp4** | 22.36s | Slide: Two-column architectural comparison ("Typical AI demo" vs "Ownership Lens: graph + rules decide; model picks tools") and real-world compliance use cases (KYC/AML, supplier risk, journalism, fraud rings). | Architectural defensibility and enterprise applicability. | Production Value |
| **s10.mp4** | 19.96s | Compliance banner: "Historical leak, demo watchlist, human review required"; end card with project title, GitHub repo link (`github.com/GoDxVictoryRR/ACD-Agent`), track metadata, and ICIJ attribution. | Transparent contest submission credentials and open-source availability. | End Card |

---

## Verification & Self-Check Status (V5)

- **Total Clips Created:** 11 clips (available in both `.webm` and `.mp4` formats under `docs/video/clips/`).
- **Resolution:** 1600 &times; 900 across all clips.
- **Red Path Visibility:** Verified in `s04.mp4`, `s04_mid.png`, `s04_end.png`.
- **Label Clutter / Overlaps:** Resolved; clean Cytoscape concentric layout with distinct node halos and badges.
- **Error Banners / Console Errors:** Zero unexpected error banners or console errors detected during recording runs.
- **Footer Disclaimer:** Present and verified in `s03_end.png` and `s10_end.png`.
- **Secret Protection:** 0 secrets found across all proof pages, scripts, and logs (scanned for `nvapi` and key patterns).
- **Clean Graph State:** Confirmed `clean_cases()` executed before and after recording sessions; 0 `(:Case)` nodes remain in database.

---

## Items Reported NOT DONE (Product Freeze Compliance)

1. **`?mode=replay` in Frontend UI:**
   - **Reason:** While backend endpoint `GET /replay/{slug}` is implemented in `api/main.py`, the static web UI (`web/app.js`) currently does not parse or load `?mode=replay`. Per the project freeze rule ("do not change core/, agent/, api/, web/"), the frontend was left unaltered. Real-time AI agent mode was recorded directly live (`s05b.mp4`) instead of falling back to UI replay.
