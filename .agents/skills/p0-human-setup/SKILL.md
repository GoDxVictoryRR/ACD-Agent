---
name: p0-human-setup
description: "Walks the human through everything only they can do: installs, API key, data download, accounts, registration, video and submission. Use at project start and whenever any phase prints HUMAN ACTION REQUIRED."
---

# p0: human setup

You cannot do these. Ask one group at a time, give the exact steps, run the verify command yourself where possible, log the result in `STATE.md`. Never ask the human to paste a secret into chat: they put it in `.env`.

## Group A: before p1
1. **Tools.** Git, Python 3.12, Docker Desktop (running). Verify: `git --version`, `python --version`, `docker run --rm hello-world`. On Windows use WSL or Git Bash.
2. **Hackathon registration.** https://www.wemakedevs.org/hackathons/falkordb -> Register. Track 1 must be named again at submission.
3. **NVIDIA API key (free).** build.nvidia.com -> sign in/up -> open a model page (e.g. `nvidia/llama-3.3-nemotron-super-49b-v1.5`) -> generate/get API key -> copy `nvapi-...` into `.env` as `NVIDIA_API_KEY=`. UI labels may differ. Verify:
   `curl -s https://integrate.api.nvidia.com/v1/models -H "Authorization: Bearer $NVIDIA_API_KEY" | head -c 300`
   401/403 -> regenerate. Never commit `.env` (check `.gitignore` before the first commit).

## Group B: before p2
4. **ICIJ data.** Page: https://offshoreleaks.icij.org/pages/database (ODbL / CC BY-SA, cite ICIJ).
   - You may first try: `curl -L -o data/raw/icij.zip https://offshoreleaks-data.icij.org/offshoreleaks/csv/full-oldb.LATEST.zip` (URL from a third-party doc, unverified). If it fails, is not a zip, or the network is blocked: the human downloads the CSV zip from the page into `data/raw/` and unzips.
   - Verify: `ls data/raw` shows several CSVs. Never commit `data/raw/`.
5. **Demo gate (end of p2).** Human reviews `docs/demo_cases.md` and picks 2-3 demo entities, 1 entity with no useful connections (for the "insufficient evidence" beat), and the watchlist. Watchlist = companies/entities, not named private individuals. Record in `STATE.md`.
6. **Regression gate (end of p4).** Human skims the 10 expected verdicts in `tests/regression/expected.json` and says whether they look plausible.

## Group C: before p7
7. **GitHub.** Public repo; add remote; push. Verify: the repo opens in a private browser window.
8. **FalkorDB Cloud (free, no card).** https://app.falkordb.cloud/signup -> create a free instance -> copy host, port, password into `.env` (`FALKORDB_HOST`, `FALKORDB_PORT`, `FALKORDB_PASSWORD`). Free tier: no TLS, no persistence.
9. **Render** (sign in with GitHub) and **Vercel or Netlify** (sign in with GitHub).

## Group D: before p8
10. **Demo video.** Human records (OBS is free) following `docs/demo_runbook.md`; uploads (YouTube unlisted is fine); gives you the URL.
11. **Blog post.** Human edits the draft and publishes (dev.to / Hashnode / wherever the organizers accept); gives you the URL. Check the submission form for a blog field.
12. **Submission form.** Human fills: repo URL, live URL, video URL, blog URL, **Track 1**, AI-assistant disclosure. You cannot submit.

## Rules for you
- If a gate is not done, do not mock it. Continue unblocked work.
- If the human chooses to skip ICIJ: use the synthetic fallback in `/p2-data-graph` and say so in the README.
