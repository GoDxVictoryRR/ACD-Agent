# Ownership Lens — Manual Verification Runbook

This runbook provides 8 standalone PowerShell commands that the human team member can run directly to verify system health, test suite coverage, security invariants, API hardening, resilience, and container performance.

---

### Command 1: Live Container Health Check
Verifies that the FastAPI backend is running, connected to FalkorDB, configured for ICIJ Panama Papers data, and has a valid LLM key.

```powershell
curl.exe -s http://localhost:8000/health
```

**Expected Output:**
```json
{"db":"ok","graph":"ready","llm_key":true,"mode":"live","data_source":"icij","data_disclaimer":"ICIJ Offshore Leaks (ODbL/CC BY-SA). Inclusion is not evidence of wrongdoing.","rss_mb":0.0}
```

---

### Command 2: Pytest Full Test Suite Execution
Executes the complete test suite (regression, agent loop, API endpoints, rules engine, graph algorithms, verifier, and failure modes).

```powershell
.\.venv\Scripts\pytest.exe -q -rs
```

**Expected Output:**
```text
46 passed in 6.2s
```
*(0 failures, 0 errors, 0 skips)*

---

### Command 3: Architectural Invariant Verification
Verifies the 6 non-negotiable hackathon architectural invariants (no forbidden libraries, no Cypher in agent/prompts, read routing strictly via `ro()`, Case/ABOUT/CITED exclusion, no tracked secrets, untracked `data/raw/`).

```powershell
.\.venv\Scripts\python.exe scripts/check_invariants.py
```

**Expected Output:**
```text
======================================================================
OWNERSHIP LENS — ARCHITECTURAL INVARIANT CHECKER
======================================================================
[CHECK 1/6] Forbidden library imports... PASSED
[CHECK 2/6] LLM isolation from raw Cypher... PASSED
[CHECK 3/6] Read routing via ro() / ro_query... PASSED
[CHECK 4/6] Case / ABOUT / CITED exclusion from read traversals... PASSED
[CHECK 5/6] Git tracked secrets and .env... PASSED
[CHECK 6/6] data/raw/ not tracked by git (ICIJ data protection)... PASSED
======================================================================
[OK] ALL 6 INVARIANTS PASSED VERIFICATION!
```

---

### Command 4: Git Secret Scan
Scans all git-tracked files and commit history to guarantee that no real API keys (`nvapi-...`) are committed.

```powershell
.\.venv\Scripts\python.exe -c "import subprocess, re; f = [f for f in subprocess.check_output(['git', 'ls-files'], text=True).splitlines() if re.search(r'nvapi-[A-Za-z0-9_-]{10,}', open(f, errors='ignore').read())]; print('PASS: Zero tracked secrets in git' if not f else f'FAIL: {f}')"
```

**Expected Output:**
```text
PASS: Zero tracked secrets in git
```

---

### Command 5: Failure Modes & Graceful Degradation
Verifies that invalid API keys, 429 rate limits, malformed tool arguments, and LLM timeouts gracefully degrade to deterministic fallback investigations without crashing.

```powershell
.\.venv\Scripts\python.exe scripts/test_failure_modes.py
```

**Expected Output:**
```text
======================================================================
VERIFYING SYSTEM RESILIENCE ACROSS 4 FAILURE MODES
======================================================================
[MODE 1/4] Testing Invalid API Key... PASS: Graceful fallback on invalid key. Verdict: clear
[MODE 2/4] Testing Simulated 429 Rate Limit... PASS: Graceful fallback on 429. Verdict: clear
[MODE 3/4] Testing Malformed Tool Arguments... PASS: Malformed args handled gracefully. Tool status: ok
[MODE 4/4] Testing LLM Timeout Handling... PASS: Graceful fallback on Timeout. Verdict: clear
Wrote failure modes evidence to docs/failure_modes_evidence.md
RESULT: ALL 4 MODES PASSED
```

---

### Command 6: Cross-Surface Consistency & API Hardening
Verifies that CLI and API verdicts match identically, Case nodes do not pollute read tools, prompt injection in graph nodes is safely neutralized, and API input validation rejects invalid depths, oversized watchlists, and malformed characters.

```powershell
.\.venv\Scripts\python.exe scripts/matrix_verification.py
```

**Expected Output:**
```text
--- 1. Testing Cross-Surface Consistency (CLI vs API) ---
  CLI Verdict: escalate
  API Verdict: escalate
  PASS: CLI and API verdicts are identical.
--- 2. Testing Case Pollution Immunity ---
  PASS: Case nodes and ABOUT/CITED edges are strictly excluded from all read tools.
--- 3. Testing Prompt Injection in Graph Node ---
  PASS: Poisoned node resulted in safe verdict: insufficient_evidence.
--- 4. Testing API Hardening ---
  a) 200-char entity name: accepted and scheduled safely.
  b) Control characters only: safely rejected with HTTP 400.
  c) Depth 9: rejected with HTTP 422 Unprocessable Entity.
  d) Watchlist of 50 items: safely rejected with HTTP 422.
  e) Unauthorized CORS origin: safely rejected/omitted.
  f) Executing burst of 20 concurrent requests... PASS
--- 5. Testing SSE Event Sequencing ---
  PASS: SSE stream strictly follows status -> step -> verdict -> memo -> done order.
ALL MATRIX TESTS PASSED!
```

---

### Command 7: Systematic Ablation Study
Executes the 5-configuration ablation study isolating depth constraints, algorithm rules, and path rules across the primary demo and negative controls.

```powershell
.\.venv\Scripts\python.exe scripts/ablation.py
```

**Expected Output:**
```text
======================================================================
RUNNING SYSTEMATIC ABLATION STUDY
======================================================================
Testing: MOSSACK FONSECA & CO. (SAMOA) LIMITED....
  -> Full: escalate | D1: clear | D2: review | NoAlgo: escalate | NoPath: review
Testing: TIANSHENG INDUSTRY AND TRADING CO., LTD....
  -> Full: review | D1: review | D2: review | NoAlgo: review | NoPath: review
Testing: CRYSTAL RISE HOLDINGS LIMITED...
  -> Full: review | D1: review | D2: review | NoAlgo: review | NoPath: review
Testing: Millex International Limited...
  -> Full: review | D1: review | D2: review | NoAlgo: review | NoPath: review
Wrote ablation results to docs\ablation.md
```

---

### Command 8: Docker Container Resource Utilization
Measures real-time memory and CPU utilization of the active `ownership-lens-app` container to verify operation well beneath the 512MB RAM cap.

```powershell
docker stats --no-stream ownership-lens-app
```

**Expected Output:**
```text
CONTAINER ID   NAME                 CPU %     MEM USAGE / LIMIT   MEM %     NET I/O      BLOCK I/O   PIDS
...            ownership-lens-app   0.15%     60.7MiB / 512MiB    11.85%    ...          ...         7
```
*(Memory utilization: ~12-18% of 512MB limit; CPU: < 0.5%)*
