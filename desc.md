# FalkorDB hackathon project analysis and planning

**Created:** 10/16/2026 3:18:48  
**Updated:** 10/16/2026 10:04:46  
**Exported:** 10/16/2026 11:01:52  
**Link:** [https://claude.ai/chat/55657a78-68d2-449b-9fab-d00a25fc63c5](https://claude.ai/chat/55657a78-68d2-449b-9fab-d00a25fc63c5)  

## User:

> 10/16/2026 3:18:49

> File: Track 1 Graph Hacks AI Agent Research.md

https://www.wemakedevs.org/hackathons/falkordb#challenge i have attached the hackathn link and the track 1   discusion , reseach and chat with grok about hte project what i ant you to go throught the chat properly and then do your seperate dont just copy ross check everything  reseaach and analysis for this project and after all that give the final plan about the project be brutally honest and practical with everything

## Assistant:

> 10/16/2026 3:21:11

> Verifying hackathon details through search.
>
> - Gathering the uploaded file and linked content.
> - Updating memory
> - Read the uploaded research/chat file
> - Read the truncated middle of the research file (part 1)
> - Read the truncated middle of the research file (part 2)
> - Read remaining truncated section of the research file
> - Verifying hackathon details through search.
> - **Done**

I've read the whole Grok chat. Now I'm checking its claims against the official hackathon page and FalkorDB's own docs.

> Drafting the full strategy response with citations and structure.
>
> - [Graph Hacks: Context for AI Agents | WeMakeDevs (wemakedevs.org)](https://www.wemakedevs.org/hackathons/falkordb#challenge)
> - Calculating the remaining time until the countdown ends.
> - [Rules | Graph Hacks: Context for AI Agents | WeMakeDevs (wemakedevs.org)](https://www.wemakedevs.org/hackathons/falkordb/rules)
> - Evaluating the submission against the grading rubric criteria.
> - [Resources | Graph Hacks: Context for AI Agents | WeMakeDevs (wemakedevs.org)](https://www.wemakedevs.org/hackathons/falkordb/resources)
> - [https://docs.falkordb.com/algorithms/ (falkordb.com)](https://docs.falkordb.com/algorithms/)
> - [How to Build an Agent That Reasons Over a Graph (wemakedevs.org)](https://www.wemakedevs.org/blogs/how-to-build-an-agent-that-reasons-over-a-graph)
> - Evaluating a hackathon project against competition categories.
> - FalkorDB MCP server
> - Investigating what the FalkorDB MCP server actually exposes.
> - [https://docs.falkordb.com/algorithms/betweenness-centrality](https://docs.falkordb.com/algorithms/betweenness-centrality)
> - FalkorDB algo.betweenness betweenness centrality syntax
> - Verifying the correct graph algorithm name and its parameters.
> - TigerGraph Hacker House Goa HHGOA fraud investigation agent LangGraph MCP
> - Searching for open, login-free datasets for the project.
> - falkordb python client pypi latest release version
> - Verifying the latest release claim for a software client.
> - ICIJ Offshore Leaks Database download CSV bulk license
> - Mapping out the build schedule and deployment plan.
> - [Schedule | Graph Hacks: Context for AI Agents | WeMakeDevs (wemakedevs.org)](https://www.wemakedevs.org/hackathons/falkordb/schedule)
> - Drafting the full strategy response with citations and structure.
> - **Done**

## Verdict

The Grok chat is right about what Track 1 asks for, but its plan is the generic consensus plan, and several specifics are wrong or unverified. I checked the official page, rules, FAQ, the organizers' own blog post, FalkorDB's docs and the TigerGraph projects it cites. About 2.5 days remain (the deadline is Sunday Oct 18, 11:59 PM IST).

## What Grok got right

- The core requirements: multi-hop reasoning, algorithms and queries as tools, MCP, actions, and explainable paths.
- The graph must be the decision engine, not a side store.
- Writing cases back to the graph, a deterministic rules layer, and skipping Obsidian, fine-tuning and multi-agent complexity.

## What it got wrong or never checked

1. **The official FalkorDB MCP server isn't what Grok described.** It lets a model run OpenCypher (with a read-only mode), create nodes and relationships, and list or delete graphs. It does not ship PageRank or shortest-path tools. Grok told you to "expose 4–6 algorithm tools via the official server" and also to use "parameterized tools only". Those conflict, because the official server lets the model write raw Cypher. The organizers' own reference build does the opposite: a fixed catalogue of human-written, typed tools exposed over MCP, where the model never writes a query. Write your own small MCP server. Also, the MCP server defaults to port 3000, which clashes with FalkorDB Browser in the Docker command, so remap one.
2. **Wrong procedure name.** It's `algo.betweenness`, not `betweennessCentrality`. It takes nodeLabels, relationshipTypes and an optional samplingSize, and the docs warn it's expensive on large, dense graphs. The working `SPpaths` and `pageRank` syntax is in the organizers' blog. A* is a geographic (haversine) algorithm in FalkorDB, so it's useless for non-spatial data.
3. **"falkordb 1.8.0 released Oct 14" is unverified.** The newest I could find was 1.6.2, released 2026-07-19. Just run `pip install falkordb`. I also couldn't verify several repos Grok named (langgraph-goat, prsdm/langgraph-mcp, SEEK, AoG, SAG), so don't build on them.
4. **IEEE-CIS Fraud as "the best dataset" is a trap.** As far as I know it sits on Kaggle behind login and rules acceptance. The rules say no login-protected or restricted data; only public, synthetic or your own. It's also the exact dataset behind many TigerGraph hackathon fraud agents.
5. **It missed rules that can disqualify you.**
   - If the product still works with FalkorDB removed, the graph counts as decoration.
   - You must submit a public repo, a README with your graph data model, the Cypher or algorithms the product depends on, a demo video, and a live deployment or local setup instructions.
   - AI coding assistants must be disclosed, and you must be able to explain the code. Fully AI-generated projects may be rejected.
6. **"Algorithms are required or you lose" is overstated.** I found no published scoring rubric. The only judging guidance is the organizers' blog, which says it comes down to whether the graph does work the agent couldn't do without it. Use an algorithm only where it changes a decision.
7. **Bloat.** GraphRAG-SDK is for turning documents into a graph, and Graphiti is a memory layer aimed at Track 2. With structured data you need neither. LangGraph is optional too: a plain tool-calling loop with a step cap and a trace is fine.

## The competitive reality

The page showed 7,138 registrants. The organizers published a reference project, "Blast Radius", a service-dependency agent. Judges have seen it, so skip that domain. The fraud-investigator pattern (LangGraph, MCP, policy rules, case write-back) is also well covered by the TigerGraph hackathon write-ups. Those are the same blueprint Grok handed you, and other entrants are getting the same advice. The basics are table stakes; you win by being clearly better on one distinctive idea, or you don't.

My honest odds: finishing a clean, honest project and reaching the top 50 (T-shirt) is realistic. Winning the iPhone is a long shot for anyone. The blog-post prize is a cheap second chance.

## The plan

I'm assuming Python and an LLM API you can use. If you're already strong in a domain, use that instead, because domain knowledge beats data convenience.

**Concept: an ownership-network due-diligence agent on the ICIJ Offshore Leaks data.**
- It's licensed under ODbL with CC BY-SA contents, free to download as CSV, and cite ICIJ.
- It's a native graph (entities, officers, intermediaries, addresses) with no login and no crawling.
- Real people appear in it. ICIJ states that inclusion doesn't imply wrongdoing, so the agent reports "exposure indicators needing human review", never guilt. Screen against a watchlist the user supplies.

**Build**
- Load one leak or one jurisdiction subset, not everything. Measure query speed before you commit. Check `relationships.csv` for the real relationship types, and treat ICIJ's fuzzy "similar" links as weak evidence.
- Write six read tools and one write tool, each with human-written parameterized Cypher:
  - resolve entity (an unknown name returns "unknown entity" and runs nothing)
  - ownership chain
  - shared officers, addresses and intermediaries
  - path between two entities (`algo.SPpaths`)
  - cluster and centrality (WCC/CDLP/PageRank, precomputed or on the subset)
  - recall prior cases
  - record decision
- A deterministic rules layer turns tool output into one of four verdicts: clear, review, escalate, or insufficient evidence. The LLM picks tools and writes the memo. Reject any memo that names an entity the tools didn't return (the organizers' own check).
- The decision is written back as a Case node linked to its evidence, and later runs can recall it.

**Demo (about 3 minutes, three beats)**
1. Depth 1 looks clean. At depth 3 the entity shares a nominee officer and address with a cluster that connects to a watchlist name, with the path shown.
2. A question the graph can't support returns "insufficient evidence" rather than a guess.
3. A second, related entity cites the earlier case from memory.

Before writing any agent code, find your two demo entities by hand in FalkorDB Browser. Make sure the story exists in the data.

## Schedule

- **Fri (today):** register, check the submission form, start Docker, load the data, run five hand-written queries, pick the demo cases.
- **Sat:** MCP server, rules layer, agent loop, trace, write-back. End the day with three cases working from the command line.
- **Sun:** minimal UI (hop chain plus one subgraph view), README with data model, listed queries and AI disclosure, demo video, deployment (a local setup plus video is explicitly allowed), and a short blog post. Submit by early evening and add no features after noon.

## Cut list

Obsidian, Graphiti, GraphRAG-SDK, multi-agent, fine-tuning, custom algorithms, and a fancy frontend. Skip any Neo4j-only Cypher too, since FalkorDB implements a subset of OpenCypher.

## Submission checklist

Name Track 1 explicitly (the organizers' blog says one submission is judged in one track, while the rules say you may enter several). Make sure the main FalkorDB work is new, because only original work done during the event is judged.

If you tell me your team size and skills, I can turn this into an hour-by-hour build list and the exact Cypher for the tools.

---

**Sources:**

- [github.com](https://github.com/FalkorDB/FalkorDB-MCPServer/wiki)
- [falkordb falkordb mcpserver](https://lobehub.com/mcp/falkordb-falkordb-mcpserver)
- [MCP Server](https://docs.falkordb.com/genai-tools/mcpserver)
- [> ## Documentation Index](https://docs.falkordb.com/agentic-memory/graphiti-mcp-server.md)
- [falkordb graph](https://playbooks.com/mcp/falkordb-graph)
- [MCP Servers/FalkorDB](https://agentpedia.codes/mcp/falkordb)
- [> ## Documentation Index](https://new.docs.falkordb.com/genai-tools/mcpserver.md)
- [Betweenness Centrality](https://docs.falkordb.com/algorithms/betweenness_centrality.html)
- [> ## Documentation Index](https://docs.falkordb.com/cypher/procedures.md)
- [Betweenness Centrality](https://docs.falkordb.com/algorithms/betweenness-centrality.html)
- [> ## Documentation Index](https://docs.falkordb.com/algorithms/betweenness-centrality.md)
- [Betweenness Centrality](https://docs.falkordb.com/algorithms/betweenness-centrality)
- [> ## Documentation Index](https://docs.falkordb.com/algorithms.md)
- [> ## Documentation Index](https://new.docs.falkordb.com/algorithms/betweenness-centrality.md)
- [DEV Community](https://dev.to/yash_gupta_4eb6e1b9159a4b/goa-hack-278l)
- [DEV Community](https://dev.to/atharvaiparkar/fraudlens-tigergraph-4ckj)
- [DEV Community](https://dev.to/saadhan/tigergraph-fraud-sentinel-37on)
- [DEV Community](https://dev.to/mukull-s/a-fraud-investigation-agent-247l)
- [www.itechguides.com](https://www.itechguides.com/?p=1058676)
- [NEWn1n v2.0.1 is live! Enterprise Unified LLM API Gateway with 500+ AI Models, up to 90% off, Try now](https://explore.n1n.ai/blog/building-autonomous-fraud-investigation-agent-graphrag-2026-09-24)
- [www.itechguides.com](https://www.itechguides.com/?p=1056077)
- [trendshift.io](https://trendshift.io/repositories/259600)
- [Advancing Entity Resolution for Fraud Detection with TigerGraph](https://www.tigergraph.com/2023/09/08/)
- [<?xml version="1.0" encoding="UTF-8"?>](https://pypi.org/rss/project/kiarina-falkordb/releases.xml)
- [kiarina falkordb](https://pypi.org/project/kiarina-falkordb/)
- [pypi.org](https://pypi.org/project/FalkorDB/1.6.2/)
- [pypi.org](https://pypi.org/project/FalkorDB)
- [Python client for interacting with FalkorDB database](https://pypi.python.org/pypi/falkordb)
- [www.piwheels.org](https://www.piwheels.org/project/falkordb/)
- [Last released Apr 1, 2024](https://pypi.python.org/user/SWilly22/)
- [The International Consortium of Investigative Journalists Home Download Support Us](https://offshoreleaks.icij.org/pages/database)
- [# ICIJ Offshore Leaks Database](https://download.hermesedi.duckdns.org/.hermes/hermes-agent/optional-skills/research/osint-investigation/references/sources/icij-offshore.md)
- [offshoreleaks.icij.org](https://offshoreleaks.icij.org/nodes/245692)
- [offshoreleaks.icij.org](https://offshoreleaks.icij.org/nodes/236132)
- [offshoreleaks.icij.org](https://offshoreleaks.icij.org/nodes/239840)
- [icij offshoreleaks](https://opensanctions.org/datasets/icij_offshoreleaks)
- [offshoreleaks.icij.org](https://offshoreleaks.icij.org/nodes/234908)
- [The International Consortium of Investigative Journalists Home Download Support Us](https://offshoreleaks.icij.org/nodes/169730)
- [offshoreleaks.icij.org](https://offshoreleaks.icij.org/nodes/14020190)
- [offshoreleaks.icij.org](https://offshoreleaks.icij.org/nodes/289141)

## User:

> 10/16/2026 3:34:43

> File: 

this is what grok told what i want you to do is to use the most optimised high quality features, tools , algo , mcp, memory , etc that would gurantee win in the track one, also keep in mind i wont spend a penny of money on this project so everything must be free and use this for llm brain https://build.nvidia.com/models  be brutally honest and practical with everything

## Assistant:

> 10/16/2026 3:35:42

> Highlighting per-case subgraph analysis as a standout differentiator.
>
> - Planning a free optimized setup using an NVIDIA-hosted LLM.
> - Adding to memory
> - build.nvidia.com free API key rate limit requests per minute function calling models
> - Checking free-tier rate limits and compatible API endpoints.
> - NVIDIA API catalog build.nvidia.com trial prototyping terms Nemotron function calling tool use model
> - Surveying free hosted API options with compatible endpoints.
> - falkordb-py releases 1.8.0 GitHub FalkorDB python client changelog
> - Verifying the release date and conceding the earlier claim.
> - FalkorDB Cloud free tier plan limits memory
> - Highlighting per-case subgraph analysis as a standout differentiator.
> - **Done**

## Corrections first

Grok is right that `falkordb` 1.8.0 exists. PyPI lists it as uploaded on Oct 14, 2026. I was wrong, because my earlier source lagged. Just run `pip install falkordb`.

On the rest, Grok's review mostly agrees with my critique, so there's little to argue. Its pushback on LangGraph is fair. Use a plain tool loop or LangGraph, whichever you already know. Don't learn a new framework this weekend.

Nobody can guarantee a win. 7,000+ people registered and there is one prize per track. What I can do is give you the plan that maximizes your odds at $0, and flag where it can break.

## The $0 stack

| Layer | Choice | Free-tier catch |
|---|---|---|
| Database | FalkorDB in local Docker | None |
| Live database (optional) | FalkorDB Cloud free | 100MB RAM, no persistence, stopped after 1 idle day and deleted after 7. Script the reload. |
| Data | ICIJ Offshore Leaks subset | The full set likely won't fit in 100MB, so load one leak or jurisdiction and test early. |
| LLM | build.nvidia.com | See below |
| MCP | Your own small server (official MCP Python SDK) | None |
| Agent loop | Plain Python loop | None |
| UI | FastAPI plus one HTML page with Cytoscape.js from a CDN | None |
| Video and blog | OBS, dev.to | None |

The rules accept a local setup plus demo video, so a live deployment is a bonus and not a requirement. Do it last and only if everything else works.

## Using NVIDIA's free LLM

- The key is free with no credit card, and the endpoint is OpenAI-compatible (`integrate.api.nvidia.com/v1`). Use it through the OpenAI client and convert your MCP tool schemas into function-calling specs.
- It runs under NVIDIA's API Trial Terms. That's fine for a hackathon prototype, but it's not a production setup.
- Third-party tooling reports a free-tier limit of about 40 requests per minute, and says heavy tool loops can hit 429 errors. That figure isn't from NVIDIA's own docs, so check your dashboard. Either way, budget for it.
- Models to try first: llama-3.3-nemotron-super-49b-v1.5, which a proxy project uses as its default with single and parallel tool calling, then the Nemotron 3 Super and Nano agent models. Avoid DeepSeek-R1 for tool use; on the hosted endpoint its reasoning and tool calling reportedly don't work together. The catalog changes, so spend the first 30 minutes testing two or three models on your actual tools and keep whichever calls them correctly.

**Design for the limit.** Cap each investigation at about 6–8 LLM calls, add retry with backoff, and cache responses for your demo cases. The LLM only picks tools and writes the memo, so if it fails twice, a deterministic fallback runs the standard investigation sequence. This keeps your demo from dying at the worst moment.

## What goes beyond Grok's list

These are ordered by value per hour:

1. **A graph on/off panel.** Run the same entity with depth limited to 1 versus depth 3 and show the verdict flipping from clear to review. This directly answers the rule that says the product must not work without FalkorDB, and it matches the contrast the organizers' blog calls their strongest demo move. It costs under an hour.
2. **A per-case subgraph in its own FalkorDB graph.** Copy each investigation's neighborhood (roughly 50–500 nodes) into a graph named `case:<id>` and run PageRank, betweenness and CDLP there. Centrality scores mean something on a small neighborhood. They are slow and noisy on a huge graph. It also uses FalkorDB's multigraph feature, which the sponsor highlights. This is the one ambitious piece. If it isn't working by Saturday noon, fall back to precomputed community IDs stored as node properties.
3. **Evidence ledger plus abstention.** Every verdict lists the rule that fired and the path behind it. "Insufficient evidence" is a real outcome, not an error.
4. **A memo verifier.** Reject any memo that names an entity the tools didn't return.
5. **A small regression suite.** Ten fixed entities with expected verdicts, shown as a table in the README. You have no ground-truth labels, so this proves consistency and not accuracy, and you should say so in the README.
6. **Graph-native memory.** Case nodes link to the entities involved, and a `recall` tool finds earlier cases that share entities. There is no vector store and no embeddings.
7. **A trace panel** showing each tool call, its arguments, row count and time.

Skip everything else: Graphiti, GraphRAG-SDK, multi-agent, Obsidian, custom algorithms, and a fancy frontend.

## Schedule

Today is Friday, and the deadline is Sunday 11:59 PM IST.

- **Friday:**
  - Register and read the submission form.
  - Run the 30-minute NVIDIA tool-calling test.
  - Start Docker and load the ICIJ subset, checking the real relationship types and load speed.
  - Hand-find two demo entities in FalkorDB Browser where depth 1 looks clean and depth 3 doesn't.
  - Gate: if the subset can't load and query fast tonight, switch to a synthetic graph of your own design. That's allowed and still counts as the graph doing real work.
- **Saturday:** MCP server with six read tools and one write tool, then the rules layer, the loop with its fallback, the trace, write-back, and the depth-1-versus-3 toggle. End the day with three cases running from the command line. The per-case subgraph goes in only if time allows.
- **Sunday:**
  - Minimal UI.
  - README with the data model, the Cypher and algorithms you use, AI-assistant disclosure and ICIJ attribution.
  - Demo video (three beats: depth contrast, honest abstention, memory recall).
  - Blog post.
  - Submit by evening with no new features after noon.

You must be able to explain every line, so don't paste in code you can't walk through.

## Brutal risk list

- **The demo case doesn't exist in the data.** This is the most common failure. Find it before you code the agent.
- **The free LLM flakes or rate-limits.** Mitigated by the call cap, caching and fallback.
- **Scope creep.** If something isn't on this page, it's cut.
- **Real people in the data.** Report "exposure indicators needing human review", never guilt, and screen only against a watchlist the user supplies.

Realistically, finishing this cleanly gets you a strong shot at the top 50, and a decent shot at the blog prize if you write it well. The iPhone depends on how many others build equally clean projects and how well your demo lands. If you tell me your team size and Python comfort, I'll write the exact tool Cypher and the NVIDIA tool-calling test script.

---

**Sources:**

- [pypi.org](https://pypi.org/project/nvd-claude-proxy/0.2.6/)
- [pypi.org](https://pypi.org/project/nvd-claude-proxy/0.2.3/)
- [pypi.org](https://pypi.org/project/nvd-claude-proxy/0.2.7/)
- [pypi.org](https://pypi.org/project/nvd-claude-proxy/0.2.0/)
- [pypi.org](https://pypi.org/project/nvd-claude-proxy/0.2.4/)
- [pypi.org](https://pypi.org/project/nvd-claude-proxy/0.2.8/)
- [pypi.org](https://pypi.org/project/nvd-claude-proxy/0.2.2/)
- [build an enterprise data flywheel](https://build.nvidia.com/nvidia/build-an-enterprise-data-flywheel.md)
- [nim claude proxy](https://pypi.org/project/nim-claude-proxy/)
- [build.nvidia.com](https://build.nvidia.com/nvidia/aiq.md)
- [llama nemotron embed 1b v2](https://build.nvidia.com/nvidia/llama-nemotron-embed-1b-v2.md)
- [docs.openclaw.ai](https://docs.openclaw.ai/ja-JP/providers/nvidia)
- [build.nvidia.com](https://build.nvidia.com/nvidia/nemotron-mini-4b-instruct/modelcard)
- [mistral nemotron](https://www.llmreference.com/provider/nvidia-nim/mistral-nemotron)
- [Releases · FalkorDB/falkordb-py · GitHub](https://github.com/FalkorDB/falkordb-py/releases)
- [Releases: FalkorDB/FalkorDB](https://github.com/FalkorDB/FalkorDB/releases)
- [Releases · FalkorDB/falkordblite · GitHub](https://github.com/FalkorDB/falkordblite/releases)
- [github.com](https://github.com/FalkorDB/FalkorDB/releases/tag/v4.0.2)
- [FalkorDB · PyPI](https://pypi.org/project/FalkorDB/)
- [falkordb 0.1.11](https://docs.rs/crate/falkordb/latest/source/README.md)
- [<?xml version="1.0" encoding="UTF-8"?>](https://pypi.org/rss/project/kiarina-falkordb/releases.xml)
- [falkordb-py/AGENTS.md at main · FalkorDB/falkordb-py · GitHub](https://github.com/FalkorDB/falkordb-py/blob/main/AGENTS.md)
- [falkordblite · PyPI](https://pypi.org/project/falkordblite/)
- [docs.falkordb.com](https://docs.falkordb.com/cloud/tiers/free)
- [free tier](https://docs.falkordb.com/cloud/free-tier)
- [> ## Documentation Index](https://docs.falkordb.com/cloud/tiers/free.md)
- [Startup Tier](https://docs.falkordb.com/cloud/startup-tier.html)
- [Startup Tier](https://docs.falkordb.com/cloud/startup-tier)
- [Frequently Asked Questions](https://www.falkordb.com/plans/)
- [us.fitgap.com](https://us.fitgap.com/products/036814/falkordb)

## User:

> 10/16/2026 3:43:13

i want you to give the final full plan about the project from end to end start to deployement (vercel ,render ,netify whatever is best ) list everything that is gong to be used and and must be used to build the high quality and optimized project

## Assistant:

> 10/16/2026 3:44:22

> Laying out API, UI, deployment steps, and timeline details.
>
> - Planning a full deployment setup for the project.
> - Render free web service limits 512 MB spin down 15 minutes inactivity 2026
> - Hugging Face Spaces free CPU basic 2 vCPU 16 GB RAM Docker Space sleep inactivity
> - Laying out API, UI, deployment steps, and timeline details.
> - **Done**

## Honest framing

No plan can guarantee a win. This one maximizes your odds at $0 and flags what can break. I'm assuming Python, a solo builder or a small team, and the ICIJ ownership-network concept we settled on. Today is Friday and you submit by Sunday 11:59 PM IST.

## 1. The product

**Name idea:** Ownership Lens, an agent that investigates who is connected to an offshore entity and takes action on what the graph shows.

- **Input:** an entity name plus an optional user-supplied watchlist.
- **Output, one of four verdicts:** clear, review, escalate, or insufficient evidence. Each verdict comes with an evidence ledger, the exact paths, a case memo, and a Case node written back to the graph.
- **Three demo beats:**
  1. Depth 1 looks clean, depth 3 reveals a link, with a depth toggle on screen.
  2. A question the graph can't support returns "insufficient evidence".
  3. A second related entity cites the earlier case from memory.

Frame results as "exposure indicators needing human review", never guilt. ICIJ states that inclusion in its data doesn't imply wrongdoing, and you must cite ICIJ and respect its CC BY-SA licensing.

## 2. Everything you'll use

| Item | Priority | Why |
|---|---|---|
| FalkorDB (Docker locally, Cloud free for deployment) | MUST | Rules require it as the primary database |
| ICIJ Offshore Leaks subset | MUST | Public, no login |
| Own MCP server (official MCP Python SDK) | MUST | Typed tools, and the model never writes Cypher |
| NVIDIA build API (OpenAI-compatible) | MUST | Your free LLM |
| Python 3.12, `falkordb` client, FastAPI, `openai` client, `pydantic` | MUST | Core backend |
| Deterministic rules layer | MUST | The graph and rules decide, and the LLM explains |
| Case write-back and `recall` tool | MUST | Memory with no extra system |
| Memo verifier (every named entity must come from tool output) | MUST | Prevents invented entities |
| Fallback plan when the LLM fails | MUST | Protects the demo |
| Cytoscape.js (CDN) for subgraph view | SHOULD | Shows the path |
| Depth 1 vs 3 toggle | SHOULD | Strongest demo move |
| Per-case subgraph graph (`case:<id>`) with algorithms run on it | SHOULD, cut if late | Makes centrality meaningful and uses multigraph |
| Regression suite of 10 entities | SHOULD | README credibility |
| Docker Compose | SHOULD | Fallback submission path |
| LangGraph, Graphiti, GraphRAG-SDK, Obsidian, multi-agent | SKIP | No payoff in 2.5 days |

## 3. Graph model and loading

- **Nodes:** `Entity`, `Officer`, `Intermediary`, `Address`, plus a watchlist label for the user's screening names.
- **Edges:** use the real relationship types from `relationships.csv`. I haven't seen the file, so check column names and types after download. Treat ICIJ's fuzzy "similar"-style links as weak evidence.
- **Case model:** `(:Case {id, verdict, at, depth})-[:ABOUT]->(:Entity)` and `(:Case)-[:CITED]->(node)`.
- **Indexes:** an index on the ID property and a full-text index on name for lookup. Check FalkorDB's docs for exact syntax.
- **Size:** the free cloud tier has 100MB of RAM, which is also the dataset cap, so load one leak or jurisdiction. Write the loader as a single idempotent script using batched `UNWIND` inserts.

## 4. The seven tools

All read tools use `GRAPH.RO_QUERY`, have typed arguments, and validate names against the graph before running.

1. `resolve_entity(name)`: name to ID, or "unknown entity" and nothing else runs.
2. `ownership_chain(id, depth≤3)`: officers, intermediaries and addresses with paths.
3. `shared_links(id)`: who else shares each of them, with counts.
4. `path_between(a, b)`: `algo.SPpaths`.
5. `cluster_view(id)`: copy the neighborhood into `case:<id>`, then run PageRank, betweenness and CDLP there.
6. `recall_cases(id)`: earlier cases sharing entities.
7. `record_decision(...)`: the only write.

```cypher
MATCH (e:Entity {node_id: $id})-[r1]-(hub)-[r2]-(other:Entity)
WHERE hub:Officer OR hub:Address OR hub:Intermediary
RETURN labels(hub)[0] AS hubType, hub.name AS hub, count(DISTINCT other) AS linked
ORDER BY linked DESC LIMIT 10
```

The organizers' blog shows the `algo.SPpaths` call with sourceNode, targetNode, relTypes, relDirection, weightProp and pathCount, and `algo.pageRank('Label','REL')`. Use its syntax and substitute your relationship names. Betweenness is `algo.betweenness`.

## 5. Decision rules

The rules turn tool output into a verdict. The exact thresholds come from looking at your data, and these are the shapes:

- A shared address with at least N other entities.
- An officer or nominee linked to at least N entities.
- A path of at most k hops to a watchlist name.
- The same CDLP community as a watchlist name.
- Intermediary hub concentration.

Several rules firing yields escalate or review. An unresolved entity, or one with too little connectivity to judge, yields insufficient evidence. The LLM never changes the verdict. It only picks tools and writes the memo.

## 6. Agent loop with the free NVIDIA LLM

- Use the OpenAI-compatible endpoint with your free key; third parties report roughly 40 requests per minute on the free tier. Cap each investigation at 6–8 LLM calls.
- Spend the first 30 minutes testing two or three models on your seven tools, starting with `nvidia/llama-3.3-nemotron-super-49b-v1.5`. Avoid DeepSeek-R1 for tool calls.
- Add retry with backoff on 429s, response caching, and a deterministic fallback plan that runs the standard sequence if the model fails twice.
- Verify every memo before it's shown. If it names an entity the tools didn't return, replace it with a templated memo built from the evidence ledger.

## 7. UI

One static page with an entity box and watchlist field, a verdict card, an evidence ledger, a live trace (tool, arguments, rows, milliseconds), a Cytoscape subgraph with the path highlighted, the depth toggle, and a prior-cases panel. Stream trace steps with SSE.

## 8. Deployment, all free

**Architecture:** static UI on Vercel (Netlify works the same), a FastAPI backend with the MCP tools on Render, and FalkorDB Cloud free.

- **Why not host the backend on Vercel.** The agent loop makes several sequential LLM and database calls. As far as I know, serverless time limits make that fragile, so keep the long-running logic on Render.
- **Render's free limits:** free web services get 512 MB RAM and 0.1 CPU. They spin down after 15 minutes without traffic and take about a minute to start again. Your backend mostly waits on I/O, so it fits, but keep dependencies light.
- **Fix the cold start.** The Vercel page pings `/health` on load and shows "waking the agent, about a minute" so a judge doesn't see a dead link. Optionally add a free uptime pinger during the judging window.
- **FalkorDB Cloud free has no persistence, and idle instances are stopped after a day and deleted after seven.** Make the backend self-healing: on startup, if the graph is missing, reload the bundled subset from the repo. Keep the subset small so reload takes seconds. The free tier also has no TLS, which is acceptable for public data, but use a password.
- **Protect the NVIDIA key.** Keep it in Render environment variables, never in the repo. Add a per-IP limit and a global concurrency cap so a few judges can't burn your 40 requests per minute.
- **Replay mode.** Store traces for your three demo entities and serve them when the LLM is rate-limited, clearly labeled "replay" in the UI.
- **Skip Hugging Face.** One current doc says Docker Spaces that run compute require a paid plan, which conflicts with older pages, so I wouldn't rely on it at $0.
- **Embedded FalkorDB is a fallback only.** FalkorDBLite is an embedded Python package requiring Python 3.12 or later. I haven't tested it on Render free, so treat it as a last resort.
- **Guaranteed fallback:** the rules accept a local setup with complete instructions and a demo video if you can't deploy. Docker Compose plus a good video is a valid submission.

I haven't verified Vercel or Netlify limits, so check them when you sign up.

## 9. Repo layout

`/data` (loader, small seed), `/graph` (schema, indexes, Cypher), `/mcp` (tools), `/agent` (loop, rules, verifier), `/api`, `/web`, `/tests`, `docker-compose.yml`, `README.md`.

**README must contain** (per the rules): a data-model diagram, the Cypher and algorithms the product depends on, setup steps, the AI-assistant disclosure, ICIJ attribution, and a limitations section.

## 10. Timeline

| When | Deliverable | Gate |
|---|---|---|
| Fri | Register, NVIDIA key and model test, Docker, ICIJ subset loaded, 5 hand-written queries, two demo entities chosen | If the subset can't load and query fast tonight, switch to a synthetic graph |
| Sat AM | MCP tools 1–4 and 6–7 | Each tool returns correct rows |
| Sat PM | Rules, agent loop, fallback, verifier, trace, 3 cases from the command line | Three cases give stable verdicts |
| Sat late | Per-case subgraph and `cluster_view` | Cut if not working by noon |
| Sun AM | UI, depth toggle, deploy Render, Vercel and Cloud, replay mode | Live URL opens from a fresh browser |
| Sun PM | README, regression table, demo video (OBS), blog post | Submit by early evening |

## 11. Last checks

- Open the live link from a phone and an incognito window.
- Run the "remove FalkorDB" test mentally: every verdict must come from graph queries.
- Name Track 1 explicitly on the submission.
- Make sure you can explain every file, since you must be able to defend the code.

**Biggest risks:** the demo entity not existing in your data, free-tier LLM flakiness, and scope creep. The gates above cover the first two. Anything not on this page is cut.

If you tell me your Python comfort and whether you're solo, I'll write the exact Cypher for each tool and the NVIDIA test script. I can also turn this into a document you can export or keep.

---

**Sources:**

- [mintlify.com](https://www.mintlify.com/BhaveshBytess/PREDICTIVE-MAINTENANCE/guides/monitoring)
- [huggingface.co](https://huggingface.co/spaces/devrup404/SignalMod/blob/main/docs/DEPLOY.md?code=true)
- [huggingface.co](https://huggingface.co/spaces/devrup404/SignalMod/raw/main/docs/DEPLOY.md)
- [Render Free Tier 2026 caution](https://agentdeals.dev/vendor/render)
- [Render Pricing 2026: Free Tier Sleep, Plans, Compute](https://temps.sh/blog/render-pricing-2026)
- [# Render.com in Mid-2026: The Plan Change on 1 August, the 20x Bandwidth Cut, and When It Is Actually the Right Host](https://jwatte.com/blog/render-com-platform-review.md)
- [Render pricing explained: the workspace fee, the compute bill, and the 15-minute spin-down](https://livemy.app/blog/render-pricing)
- [nemaquant / README.md](https://huggingface.co/spaces/BreedingInsight/nemaquant/blob/main/README.md)
- [Hub documentation](https://huggingface.co/docs/hub/en/spaces-gpus)
- [gemischtes_hack / README.md](https://huggingface.co/spaces/mavengence/gemischtes_hack/blob/main/README.md)
- [Hub documentation](https://huggingface.co/docs/hub/spaces-gpus)
- [Hub documentation](https://huggingface.co/docs/hub/en/spaces-overview)
- [Hub documentation](https://huggingface.co/docs/hub/spaces-overview)
- [Introduction to Hugging Face Spaces Beginner](https://aischool.lillytechsystems.com/hf-spaces/introduction.html)

## User:

> 10/16/2026 3:49:11

what about using this Ready Datasets (Save Hours of Data Modeling)
Dataset / SourceDomain FitPractical NotesUse?IEEE-CIS Fraud Detection (used in many TigerGraph HHGOA projects)Fraud investigationAlready modeled as graphs in community repos – easiest to adaptYes – best for fraud angleSmall public codebases + tree-sitter / codebase-graph toolsCodebase impact analysisFast to turn into CALLS / IMPORTS / DEPENDS_ON graphYes if doing code domainSynthetic + real small security graphs (CVE + hosts + alerts)Security triageEasy to generate or find on Hugging FaceYesGraphRAG-SDK sample docs + your own PDFs/MarkdownAny domainFastest way to bootstrap a real KGAlways usefulLarge public graphs (MalNet etc.)—Too big / slow for 3-day hackathonSkip

## Assistant:

> 10/16/2026 3:49:31

> Checking access requirements and scale of the dataset.
>
> - Evaluating dataset options for suitability and risk.
> - IEEE-CIS Fraud Detection dataset Kaggle download requires login accept competition rules
> - Checking access requirements and scale of the dataset.
> - **Done**

Short answer: I'd keep ICIJ and drop most of this table. The table is generic advice, and each row has a problem for your situation.

| Dataset | Verdict | Why |
|---|---|---|
| IEEE-CIS Fraud | Skip | Access, fit and size problems (below) |
| Codebase graph (tree-sitter) | Fallback only | Crowded shape and noisy call graphs |
| Security graph (CVE, hosts, alerts) | Fallback only | The "alerts" side must be synthetic |
| GraphRAG-SDK with sample docs | Skip | Wrong tool and a bad fit for the free LLM |
| Large graphs such as MalNet | Skip | Too big for a 100MB free database |

**IEEE-CIS Fraud.** There are three separate problems.
- **Access.** Using it requires a Kaggle account and joining the competition first. The rules ban login-protected data, so this is a real disqualification risk.
- **It isn't a graph.** It's a table of real e-commerce transactions where many features are masked or poorly described. It has about 590,000 rows and hundreds of columns. The "already modeled as graphs" repos get their links from heuristics like inferring a card or client ID, so you'd spend your hours reverse-engineering identity instead of building the agent. That's the opposite of saving modeling time.
- **Size and crowding.** 590k transactions won't fit in FalkorDB Cloud's 100MB, so you'd run the database locally. Many TigerGraph hackathon entries already used it.

**Codebase graph.** This is feasible, but it has two drawbacks.
- Static call resolution across files is noisy, especially in Python or JavaScript. A wrong edge produces a confidently wrong blast-radius answer.
- It's close to the organizers' own Blast Radius demo, a `DEPENDS_ON` traversal over a service graph, so judges have seen the shape. Use it only if you already know a codebase deeply, because that familiarity is your edge.

**Security graph.** CVE and advisory data is public, but hosts and alerts would have to be synthetic. That's allowed, but the demo then depends entirely on how convincing your generated data is, and judges can tell when an answer was planted. I couldn't verify the claim that ready-made security graphs sit on Hugging Face, so don't count on it.

**GraphRAG-SDK sample docs.** It's built to turn unstructured documents into a graph. That means many LLM extraction calls, which on the free NVIDIA tier (reportedly about 40 requests per minute) would be slow and rate-limited. It also isn't what Track 1 rewards.

**Why ICIJ is the better "ready dataset".** It's the only option here that is already a graph, freely downloadable without login, and permitted under the rules. That's the real hours saved.

**Fallback order if ICIJ fails Friday night:**
1. A synthetic ownership network you generate yourself, with a documented generator, a few planted multi-hop structures, and noise so the demo isn't obviously rigged.
2. Public CVE and advisory data plus a synthetic asset layer.
3. A codebase graph, only if you know the code well.

Make the call by tonight. A synthetic graph that works beats a perfect dataset you're still wrestling with on Saturday.

---

**Sources:**

- [science.ecosyste.ms](https://science.ecosyste.ms/projects/106531)
- [Authors: Peter Macinec, Timotej Zatko](https://github.com/pmacinec/transactions-fraud-detection)
- [ieee cis fraud detection](https://ieee-dataport.org/documents/ieee-cis-fraud-detection)
- [IEEE CIS Fraud Detection](https://github.com/fariha123/IEEE-CIS-Fraud-Detection)
- [Data Science](https://developer.nvidia.com/blog/?p=23421)
- [0% found this document useful (0 votes)](https://www.scribd.com/document/990940751/Assignment)
- [towardsdatascience.com](https://towardsdatascience.com/?p=159334)
- [ieee cis fraud detection top 5 solution 5488fc66e95f](https://towardsdatascience.com/ieee-cis-fraud-detection-top-5-solution-5488fc66e95f/)
- [IEEE-CIS fraud](https://robustcov.readthedocs.io/en/stable/external_results/ieee_cis_fraud.html)

Powered by Claude Exporter (https://www.ai-chat-exporter.net)
