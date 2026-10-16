---
name: p8-submission
description: "Produces the README, EXPLAIN.md, demo runbook and video script, blog draft and the final submission checklist. Use after p7, or after the fallback in p7."
---

# p8: submission

Rules source: https://www.wemakedevs.org/hackathons/falkordb/rules . Re-read its submission section before finishing; if it conflicts with this file, the rules page wins.

## 1. README.md (top to bottom)
1. One-paragraph pitch + live URL + demo video URL + blog URL + **Track 1**.
2. Screenshot or GIF of the depth 1 vs 3 contrast.
3. Architecture diagram (Mermaid) and the data flow.
4. **Graph data model:** diagram + table of labels, relationship types, properties, weights, and the Case model.
5. **Cypher and algorithms the product depends on:** table `tool -> query or algorithm -> file:line -> why the decision needs it`. Include `algo.SPpaths`, the algorithms used in `cluster_view`, and the shared-links query.
6. Rules table with thresholds and the percentile used.
7. "Why FalkorDB is essential": what the product does with depth 1 only vs the full graph, with the demo case numbers. State plainly that without the graph there is no verdict.
8. Evaluation: regression table (10 entities). Say it measures consistency, not accuracy; there is no ground truth.
9. Run locally: `docker compose up`, `.env` setup, data loading, tests.
10. Deployment notes (free-tier limits, replay mode, cold start).
11. Limitations and ethics: ICIJ inclusion is not wrongdoing; verdicts are indicators for human review; fuzzy-match edges are weak; subset only; LLM may be rate-limited.
12. Data attribution and licence: ICIJ Offshore Leaks (ODbL / CC BY-SA) with link; note that the seed is a filtered derivative. Ask the human which licence to put on the code (MIT is the default suggestion).
13. **AI disclosure:** built with Google Antigravity (name the models it used if shown), NVIDIA-hosted LLM at runtime; the human reviewed and can explain the code.

## 2. `docs/EXPLAIN.md` (the human must defend the code)
One page each: architecture in plain words; each of the 7 tools (what it asks the graph, why); each rule and its threshold; the agent loop and why `forced` calls exist; the verifier; free-tier workarounds; 10 questions a judge might ask with 2-line answers (including "what if FalkorDB is removed?" and "how do you know it is right?").

## 3. Demo
`docs/demo_runbook.md`: exact entity names, clicks and expected output for 3 beats (~2-3 min): (1) depth 1 looks clean, depth 3 reveals the watchlist path, shown in the subgraph; (2) an entity with nothing connected returns "insufficient evidence" instead of a guess; (3) a related second entity recalls the earlier case. Plus a 150-word voice-over script and a "if it breaks" plan (use replay).
> **HUMAN REQUIRED:** record the video, upload, give you the URL.

## 4. Blog draft `docs/blog.md`
Title, problem, why a graph, 3 design decisions that changed the result (e.g. typed tools instead of free Cypher, rules decide / LLM explains, depth contrast), one honest limitation, how to run it. ~700 words, plain tone, no hype. Human edits and publishes.

## 5. Final checklist (verify each yourself; report as a table of pass/fail)
- Repo public; fresh clone + `docker compose up` works.
- `git log -p | grep -c nvapi-` is 0; no `.env`, no raw data tracked.
- README links all resolve (live URL, video, blog, licence).
- Live URL works in an incognito window and on a phone.
- Demo video is publicly viewable and shows FalkorDB doing the work.
- `scripts/check_invariants.py` and `pytest -q` green on the final commit; tag it.
- AI disclosure present; Track 1 named; `docs/EXPLAIN.md` present.
> **HUMAN REQUIRED:** submit the form before the deadline (Sun 18 Oct 2026, 23:59 IST). Aim for at least a few hours of buffer. You cannot submit it.

## Done when
Checklist is all pass (or each fail is stated and accepted by the human) and STATE.md shows "submitted: yes/no".
