# Ownership Lens — Final Verification & Submission Report (Final Pass Z1–Z10)

**Track 1: Agents That Act on Connected Data**  
**Hackathon**: WeMakeDevs x FalkorDB Graph Hacks (Submissions close Sun 18 Oct 2026, 23:59 IST)  
**Repository**: `https://github.com/GoDxVictoryRR/ACD-Agent`  
**Latest Verification Timestamp**: 2026-10-18T13:05:00+05:30  
**Status**: **ALL PASS (49/49 Tests Pass) · ZERO REGRESSIONS · CODE FROZEN**  

---

## 1. Item-by-Item Verification Matrix (Items Z1–Z10)

| Item | Requirement & Scope | Verification Command | Raw Output / Evidence File | Status |
|---|---|---|---|---|
| **Z1** | Law firm & service provider decoupling. Purge Mossack Fonseca from demo targets, watchlists, placeholders. Document 21 service-provider patterns. | `pytest tests/regression/test_regression.py` | `core/config.py` (`SERVICE_PROVIDER_PATTERNS`), `docs/data_notes.md` (Section 8) | **PASS** |
| **Z2 & Z3** | Primary demo case: genuine corporate directorship chain with 0 intermediaries, 0 address hubs. D1 `clear` $\to$ D4 `escalate`. | `python scripts/measure_exposure_baseline.py` | `GLAISDALE LIMITED` (Entity `10024477`, deg 5) $\to$ `Rachel Erickson` (`12116679`) $\to$ `NEWCOMBE LIMITED` (`10028037`) $\to$ `ANDREW MORAY STUART` (`12151058`) $\to$ `DOM Limited` (`10189122`, deg 5). `data/demo.json` | **PASS** |
| **Z4** | Real prompt injection immunity: live adversarial node injected into graph leaves deterministic verdict intact and memo reverts to template. | `pytest tests/test_injection.py -v -s` | `tests/test_injection.py` passed live against NVIDIA LLM in 109.34s. `docs/test_report.md` Section 10.7 | **PASS** |
| **Z5** | Exposure statistics & degree-matched baseline: 30-sample degree-matched control cohort (deg 4–6, `seed=42`) has 0.0% reachability to `DOM Limited`. Exact vs cumulative depth measured. | `python scripts/measure_exposure_baseline.py` | `docs/exposure_stats.json`: 0 / 30 (0.0%) reached. Exact depths: D1=4, D2=1, D3=2, D4=1. | **PASS** |
| **Z6** | Negative controls & degree distribution: 16.88% entities have degree 1 (< MIN_LINKS=2) returning `insufficient_evidence`. 5 negative controls verified. Snapshot updated. | `python scripts/measure_degree_distribution.py` | `docs/degree_distribution.json`, `tests/regression/expected_icij.json` | **PASS** |
| **Z7** | Matrix verification audit with explicit node IDs (`10024477`, `INJECT_TEST_9999`) across CLI==API, Case pollution, injection, API hardening, and SSE sequencing. | `python scripts/matrix_verification.py` | `scripts/matrix_verification.py`: 5/5 passed in 8.58s. `docs/test_report.md` Section 10.4 | **PASS** |
| **Z8** | Model benchmark & live 3x multi-turn runs: 15/15 runs pass with 100% agreement to deterministic baselines. Deployed model: `nvidia/llama-3.3-nemotron-super-49b-v1.5`. Depth clamping enforced. | `python scripts/live_demo_runs.py` | `docs/live_demo_runs.json` (15/15 PASS), `docs/model_bench.md` | **PASS** |
| **Z9** | Cross-surface parity & UI screenshots: Cytoscape font-weight warning fixed, inline favicon added $\implies$ 0 console warnings, 0 console errors. Full-res screenshots captured. | `chrome-devtools-mcp` browser capture | `docs/screens/desktop_comparison.png`, `docs/screens/desktop_investigation.png`, `docs/screens/mobile_view.png` | **PASS** |
| **Z10** | Comprehensive audits, latency benchmarks, memory load, self-healing re-seed, invariant checks & linter. | `pytest -v`, `check_invariants.py`, `ruff check .`, `test_memory_load.py`, `test_item11_self_heal.py` | 49/49 pytest pass, 6/6 invariants pass, 0 ruff errors, peak RAM 81.09 MiB under 512MB limit, self-heal in 22.16s. | **PASS** |

---

## 2. Key Numbers & Benchmarks

1. **Test Suite Coverage**: **49 / 49 PASS** in 101.11s (100% pass rate, 0 skips, 0 failures).
2. **Architectural Invariants**: **6 / 6 PASS** (`scripts/check_invariants.py` verified against AST and git history).
3. **Graph Traversal Latency (50 runs per depth)**:
   - **Depth 1**: p50 = 72.8ms, p95 = 80.8ms (mean = 74.0ms)
   - **Depth 2**: p50 = 115.6ms, p95 = 133.7ms (mean = 117.6ms)
   - **Depth 3**: p50 = 146.3ms, p95 = 179.7ms (mean = 147.8ms)
   - **Depth 4**: p50 = 147.8ms, p95 = 227.1ms (mean = 159.5ms)
   - **p95 < 2000ms**: **TRUE** across all depths (well within human real-time response budget).
4. **Memory Load under 512MB & 0.5 CPU**:
   - 10 sequential investigations completed in **20.06s** with zero OOM crashes.
   - Baseline container memory: 79.44 MiB (15.52%).
   - Peak container memory: **81.09 MiB** (15.84% utilization; leaving >430 MiB headroom).
5. **Self-Healing Startup Seeding**:
   - Total elapsed from graph deletion + container restart to `ready`: **22.16 seconds**.
   - Verified restored graph: **51,940 nodes** and **58,875 relationships**.
6. **Topological Baseline & Degree Distribution**:
   - 30-sample degree-matched control cohort (deg 4–6, `seed=42`): **0 / 30 (0.0%)** reach `DOM Limited` within 4 hops.
   - Degree 1 entities in Panama Papers subset: **16.88%** (all correctly return `insufficient_evidence` per `MIN_LINKS=2` invariant).
7. **Live LLM Reliability**:
   - 15 / 15 multi-turn live investigations matched deterministic ground truth (100% verdict fidelity).
   - Rate limit retries encountered: 0.

---

## 3. Fixes Implemented in this Final Pass

1. **Service Provider Exclusion (`core/config.py`)**: Added `SERVICE_PROVIDER_PATTERNS` (21 case-insensitive regex patterns) and `is_service_provider_name()`. Purged Mossack Fonseca entities from demo targets, watchlists, and UI placeholders.
2. **Primary Demo Case Realignment (`data/demo.json`)**: Replaced demo entity with `GLAISDALE LIMITED` (`10024477`) and watchlist with `["DOM Limited"]` (`10189122`). Verified 4-hop corporate directorship chain passing through zero intermediaries and zero mass-address hubs.
3. **Multi-Turn Traversal Depth Clamping (`agent/loop.py`)**: Forced `args["max_depth"] = min(int(args.get("max_depth", depth)), depth)` on all LLM-selected tool calls to strictly prevent multi-hop boundary leakage when investigating low-depth negative controls.
4. **SSE Timeout Expansion (`api/main.py`)**: Increased SSE request timeout from 60s to 180s to prevent stream aborts during multi-turn LLM generation.
5. **Prompt Injection Test Hardening (`tests/test_injection.py`)**: Added real live injection test against the active NVIDIA LLM, verifying that injected prompt nodes cannot alter deterministic verdicts or cause hallucinations in verified memos.
6. **Frontend Cleanliness (`web/index.html`)**: Corrected Cytoscape font-weight attributes to string literals (`"bold"`) and embedded an inline SVG favicon to achieve 0 console warnings and 0 console errors.

---

## 4. Known Limitations (Bluntly)

1. **Historical Leaked Data**: The ICIJ Panama Papers dataset reflects historical filings from law firm records up to 2015, not real-time corporate registry feeds.
2. **Exposure Indicators Only**: Inclusion in the database is not evidence of illegality, fraud, or wrongdoing. All verdicts are strictly styled as "exposure indicators requiring human review".
3. **Graph Horizon Boundary**: Traversal terminates at the Samoa/Seychelles jurisdictional seed boundary. Cross-jurisdictional shell structures that extend into unseeded jurisdictions may return `insufficient_evidence`.
4. **NVIDIA Public Endpoint Latency**: While tool accuracy and verdict fidelity are 100%, hosted multi-turn LLM generation can require 60–90 seconds per full investigation turn due to network latency on NVIDIA's hosted trial API. Automatic fallback to deterministic rules ensures instant recovery if the API throttles.

---

## 5. Single Next Action for Human

Record the 2–3 minute demo video following [`docs/demo_runbook.md`](file:///c:/Users/hardi/Downloads/ACD-agent/docs/demo_runbook.md) (highlighting `GLAISDALE LIMITED` at Depth 1 `clear` vs Depth 4 `escalate`), publish the blog post from [`docs/blog.md`](file:///c:/Users/hardi/Downloads/ACD-agent/docs/blog.md), and submit the repository URL to the WeMakeDevs Track 1 submission portal before **Sun 18 Oct 2026, 23:59 IST**.

---

## 6. Code Freeze Declaration

As of 2026-10-18T13:05:00+05:30, all code changes for the WeMakeDevs Track 1 submission are **FROZEN**. All 49 unit, integration, and regression tests pass, all 6 architectural invariants pass, and all documentation is verified and consistent.
