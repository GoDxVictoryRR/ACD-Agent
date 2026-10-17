# HUMAN_TODO.md — Actions Required by the Human

This document lists all tasks, decisions, and deployment steps that only the human team member can perform.

---

## 1. Approve PROVISIONAL Choices

Please review and approve the following choices implemented and verified with test evidence:

| Item | Choice | Status | Evidence / Verification File |
|---|---|---|---|
| **Demo Entity 1 (Primary Depth Flip)** | `MOSSACK FONSECA & CO. (SAMOA) LIMITED.` (d=1: `clear`, d=3: `escalate` to `TIANSHENG INDUSTRY AND TRADING CO., LTD.`) | PROVISIONAL | [`docs/demo_cases.md`](file:///c:/Users/hardi/Downloads/ACD-agent/docs/demo_cases.md), [`scripts/find_remaining_demo_cases.py`](file:///c:/Users/hardi/Downloads/ACD-agent/scripts/find_remaining_demo_cases.py) |
| **Demo Watchlist Target** | `TIANSHENG INDUSTRY AND TRADING CO., LTD.` (Entity node only, 10000001) | PROVISIONAL | [`docs/demo_cases.md`](file:///c:/Users/hardi/Downloads/ACD-agent/docs/demo_cases.md) |
| **Demo Isolated Entity** | `Dewburn Enterprises Inc.` (degree 1, d=1..3 `clear`) | PROVISIONAL | [`docs/demo_cases.md`](file:///c:/Users/hardi/Downloads/ACD-agent/docs/demo_cases.md) |
| **Demo Related Recall Entity** | `TIANSHENG INDUSTRY AND TRADING CO., LTD.` (recalls Case recorded on 10001171) | PROVISIONAL | [`docs/demo_cases.md`](file:///c:/Users/hardi/Downloads/ACD-agent/docs/demo_cases.md) |
| **Demo Negative Controls (>=4)** | `Skytrack Investments Limited`, `OMNIA TECHNOLOGIES S.A.`, `GAO SHENG LIMITED`, `KIRBY GARDENS LTD.`, `Millex International Limited`, `SINOWAY HOLDINGS LTD.` | PROVISIONAL | [`docs/demo_cases.md`](file:///c:/Users/hardi/Downloads/ACD-agent/docs/demo_cases.md) |
| **Synthetic Fallback Demo Case** | `Blue Star Maritime Holdings Ltd` (d=1: `clear`, d=3: `escalate`) | PROVISIONAL | [`data/demo.json`](file:///c:/Users/hardi/Downloads/ACD-agent/data/demo.json) |
| **Primary Dataset** | ICIJ Panama Papers Samoa/Seychelles subset (51,940 nodes, 58,891 edges, 40.91MB RAM) | PROVISIONAL | [`docs/data_notes.md`](file:///c:/Users/hardi/Downloads/ACD-agent/docs/data_notes.md), [`docs/test_report.md`](file:///c:/Users/hardi/Downloads/ACD-agent/docs/test_report.md) |

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
   - `NVIDIA_MODEL`: `nvidia/nemotron-3-super-120b-a12b`
   - `FALKORDB_HOST`: FalkorDB Cloud instance host
   - `FALKORDB_PORT`: FalkorDB Cloud port
   - `FALKORDB_PASSWORD`: FalkorDB Cloud password
   - `FALKORDB_SSL`: `false`
   - `GRAPH_NAME`: `ownership`
   - `ALLOWED_ORIGINS`: `*`
   - `DAILY_LLM_CAP`: `300`
4. Click **Deploy Web Service** and copy the live URL (e.g. `https://ownership-lens.onrender.com`).

---

## 4. Static UI on Vercel / Netlify (Optional)

*Note: The FastAPI Docker backend on Render already serves the static UI directly at `/` (bundled). If you wish to host the UI separately on Vercel/Netlify:*
1. Connect repo on Vercel or Netlify.
2. Root directory: `web`.
3. In `web/config.js`, set `API_BASE`: `https://ownership-lens.onrender.com`.

---

## 5. Post-Deployment Verification Commands

Run these commands against your live Render endpoint:
```powershell
# 1. Health check (verifies db: up, llm_key: true)
curl.exe -s https://<your-render-url>/health

# 2. Entity search
curl.exe -s "https://<your-render-url>/entities/search?q=MOSSACK"

# 3. Investigate Mossack Fonseca Samoa (Depth 3 flip to ESCALATE)
curl.exe -s -X POST https://<your-render-url>/investigate -H "Content-Type: application/json" -d '{\"entity\":\"MOSSACK FONSECA & CO. (SAMOA) LIMITED.\",\"watchlist\":[\"TIANSHENG INDUSTRY AND TRADING CO., LTD.\"],\"depth\":3}'
```

---

## 6. Submission Deliverables (Before Sun 18 Oct 2026, 23:59 IST)

1. **Record 2-3 Minute Demo Video**:
   - Follow [`docs/demo_runbook.md`](file:///c:/Users/hardi/Downloads/ACD-agent/docs/demo_runbook.md).
   - Beat 1: Show `MOSSACK FONSECA & CO. (SAMOA) LIMITED.` depth 1 (`clear`) vs depth 3 (`escalate`) depth flip live.
   - Beat 2: Show `PORTCULLIS TRUSTNET (SAMOA) LIMITED` intermediary hub (`review`, 31 links).
   - Beat 3: Show `TIANSHENG INDUSTRY AND TRADING CO., LTD.` prior Case recall (`(:Case)` node in graph).
   - Upload to YouTube / Loom. Update README.md and submission form with the link.
2. **Publish Blog Post**:
   - Copy text from [`docs/blog.md`](file:///c:/Users/hardi/Downloads/ACD-agent/docs/blog.md) to Dev.to, Medium, or Hashnode.
3. **Submit WeMakeDevs Form**:
   - Track: **Track 1: Agents That Act on Connected Data**
   - GitHub Repo URL: `https://github.com/GoDxVictoryRR/ACD-Agent`
   - Live URL: `https://<your-render-url>` (or local instructions documented in README)
   - Video URL
   - Blog URL

