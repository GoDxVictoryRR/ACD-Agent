# HUMAN_TODO.md — Actions Required by the Human

This document lists all tasks, decisions, and deployment steps that only the human team member can perform.

---

## 1. Approve Verified Choices

Please review and approve the following choices implemented and verified with test evidence:

| Item | Choice | Status | Evidence / Verification File |
|---|---|---|---|
| **Demo Entity 1 (Primary Depth Flip)** | `GLAISDALE LIMITED` (d=1: `clear`, d=4: `escalate` to `DOM Limited`) | VERIFIED | [`docs/exposure_stats.json`](file:///c:/Users/hardi/Downloads/ACD-agent/docs/exposure_stats.json), [`scripts/measure_exposure_baseline.py`](file:///c:/Users/hardi/Downloads/ACD-agent/scripts/measure_exposure_baseline.py) |
| **Demo Watchlist Target** | `DOM Limited` (Entity node only, 10189122) | VERIFIED | [`data/demo.json`](file:///c:/Users/hardi/Downloads/ACD-agent/data/demo.json) |
| **Demo Low-Link Negative Control** | `Dewburn Enterprises Inc.` (degree 1, d=1..4 `insufficient_evidence`) | VERIFIED | [`docs/degree_distribution.json`](file:///c:/Users/hardi/Downloads/ACD-agent/docs/degree_distribution.json) |
| **Demo Related Recall Entity** | `NEWCOMBE LIMITED` (recalls Case recorded on 10024477) | VERIFIED | [`docs/demo_runbook.md`](file:///c:/Users/hardi/Downloads/ACD-agent/docs/demo_runbook.md) |
| **Demo Clean Negative Controls** | `OMNIA TECHNOLOGIES S.A.`, `GAO SHENG LIMITED` (d=1..4 `clear`) | VERIFIED | [`tests/regression/expected_icij.json`](file:///c:/Users/hardi/Downloads/ACD-agent/tests/regression/expected_icij.json) |
| **LLM Model** | `nvidia/llama-3.3-nemotron-super-49b-v1.5` (15/15 live runs pass) | VERIFIED | [`docs/live_demo_runs.json`](file:///c:/Users/hardi/Downloads/ACD-agent/docs/live_demo_runs.json), [`docs/model_bench.md`](file:///c:/Users/hardi/Downloads/ACD-agent/docs/model_bench.md) |
| **Primary Dataset** | ICIJ Panama Papers Samoa/Seychelles subset (51,940 nodes, 58,875 edges, 40.91MB RAM) | VERIFIED | [`docs/data_notes.md`](file:///c:/Users/hardi/Downloads/ACD-agent/docs/data_notes.md), [`docs/test_report.md`](file:///c:/Users/hardi/Downloads/ACD-agent/docs/test_report.md) |

---

## 2. FalkorDB Cloud Free Instance Setup

1. Sign up / log in to [FalkorDB Cloud Console](https://app.falkordb.cloud).
2. Create a **Free Tier** database instance:
   - Cloud provider: AWS or GCP (default free region)
   - Note: 100MB RAM, ephemeral, no TLS
3. Copy instance connection details:
   - Host (e.g. `falkordb-free-xxxx.cloud.falkordb.com`)
   - Port (e.g. `6379`)
   - Password
4. Load seed data from local machine into FalkorDB Cloud:
   ```powershell
   $env:FALKORDB_HOST="<cloud-host>"
   $env:FALKORDB_PORT="<cloud-port>"
   $env:FALKORDB_PASSWORD="<cloud-password>"
   .\.venv\Scripts\python.exe data/load.py --reset
   ```

---

## 3. Render Web Service Deployment

1. Sign up / log in to [Render.com](https://render.com).
2. Create a **New Web Service**:
   - Source: Connect your public GitHub repository (`https://github.com/GoDxVictoryRR/ACD-Agent`)
   - Environment: **Docker** (Render will auto-detect `Dockerfile` and `render.yaml`)
   - Plan: **Free** (512MB RAM)
   - Health check path: `/health`
3. Configure Environment Variables in Render dashboard:
   - `NVIDIA_API_KEY`: your `nvapi-...` key
   - `NVIDIA_MODEL`: `nvidia/llama-3.3-nemotron-super-49b-v1.5`
   - `FALKORDB_HOST`: FalkorDB Cloud instance host
   - `FALKORDB_PORT`: FalkorDB Cloud port
   - `FALKORDB_PASSWORD`: FalkorDB Cloud password
   - `FALKORDB_SSL`: `false`
   - `GRAPH_NAME`: `ownership`
   - `ALLOWED_ORIGINS`: `*`
   - `DAILY_LLM_CAP`: `300`
4. Click **Deploy Web Service** and copy the live URL: `https://acd-agent-3hz7.onrender.com/`.

---

## 4. Static UI on Vercel / Netlify (Optional)

*Note: The FastAPI Docker backend on Render already serves the static UI directly at `/` (bundled). If you wish to host the UI separately on Vercel/Netlify:*
1. Connect repo on Vercel or Netlify.
2. Root directory: `web`.
3. In `web/config.js`, set `API_BASE`: `https://acd-agent-3hz7.onrender.com`.

---

## 5. Post-Deployment Verification Commands

Run these commands against your live Render endpoint:
```powershell
# 1. Health check (verifies db: up or standby, llm_key: true)
curl.exe -s https://acd-agent-3hz7.onrender.com/health

# 2. Entity search
curl.exe -s "https://acd-agent-3hz7.onrender.com/entities/search?q=GLAISDALE"

# 3. Investigate Glaisdale Limited (Depth 4 flip to ESCALATE)
curl.exe -s -X POST https://acd-agent-3hz7.onrender.com/investigate -H "Content-Type: application/json" -d '{\"entity\":\"GLAISDALE LIMITED\",\"watchlist\":[\"DOM Limited\"],\"depth\":4}'
```

---

## 6. Submission Deliverables (Before Sun 18 Oct 2026, 23:59 IST)

1. **Record 2-3 Minute Demo Video**:
   - Follow [`docs/demo_runbook.md`](file:///c:/Users/hardi/Downloads/ACD-agent/docs/demo_runbook.md).
   - Beat 1: Show `GLAISDALE LIMITED` depth 1 (`clear`) vs depth 4 (`escalate`) depth flip live.
   - Beat 2: Show `CRYSTAL RISE HOLDINGS LIMITED` centrality hub (`review`) and negative controls (`OMNIA TECHNOLOGIES S.A.` clear, `Dewburn Enterprises Inc.` insufficient_evidence).
   - Beat 3: Show `NEWCOMBE LIMITED` prior Case recall (`(:Case)` node in graph).
   - Upload to YouTube / Loom. Update README.md and submission form with the link.
2. **Publish Blog Post**:
   - Copy text from [`docs/blog.md`](file:///c:/Users/hardi/Downloads/ACD-agent/docs/blog.md) to Dev.to, Medium, or Hashnode.
3. **Submit WeMakeDevs Form**:
   - Track: **Track 1: Agents That Act on Connected Data**
   - GitHub Repo URL: `https://github.com/GoDxVictoryRR/ACD-Agent`
   - Live URL: `https://<your-render-url>` (or local instructions documented in README)
   - Video URL
   - Blog URL

