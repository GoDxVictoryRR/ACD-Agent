# Demo Runbook & Video Script: Ownership Lens

*3-minute live demonstration script for submission video and live judging.*

---

## Beat 1: Proving the Graph Matters (Depth 1 vs Depth 3 Contrast)

1. Open the UI at `http://localhost:8000` (or the live URL).
2. Click the quick-pick button: **"🏢 Blue Star Maritime Holdings Ltd"**.
3. Point out the Watchlist containing: `Ironclad Sanctions Entity Inc, Apex Nominees Ltd`.
4. Click **"Compare D1 vs D3"**.
5. **Observation**:
   - **Depth 1 Panel**: Verdict is **CLEAR** (no exposure indicators found within depth 1). The memo notes only 1 director and 1 registered address.
   - **Depth 3 Panel**: Verdict flips to **ESCALATE**!
   - Look at the Cytoscape graph: A bright red exposure path appears:
     `Blue Star Maritime Holdings Ltd -> Marcus Sterling (Officer) -> Sterling Bridge Holdings Ltd -> Apex Nominees Ltd / Ironclad Sanctions Entity Inc`.
   - **Takeaway**: Relational databases and shallow depth 1 checks fail completely. Only multi-hop graph traversal reveals the concealed sanctions exposure.

---

## Beat 2: Nominee Hubs & The Honest System

1. Click the quick-pick button: **"🏢 Silverline Capital Management Ltd"**.
2. Select **Depth 2** and click **Investigate**.
3. **Observation**:
   - Watch the live SSE trace stream as tools execute.
   - Verdict: **REVIEW**.
   - Evidence ledger flags `NOMINEE_OFFICER_HUB`: Director "John Alexander Vance" serves as officer in 50 distinct offshore shell companies!
   - Now test an entity not in the graph: enter **"Ghostly Shell Enterprises XYZ"**.
   - Click **Investigate**.
   - Verdict: **INSUFFICIENT EVIDENCE**. The system abstains honestly rather than hallucinating an answer.

---

## Beat 3: Memory and Recall

1. Observe the **"Prior Cases Recalled"** card on the left panel.
2. The earlier decision on Blue Star Maritime is recalled automatically because related entities share the same incorporation agent.
3. Every verdict persists back into FalkorDB as a `(:Case)` node connected with `[:ABOUT]` and `[:CITED]` edges, making compliance intelligence compound over time.

---

## Voice-Over Script (145 Words — Read Aloud in ~60 Seconds)

> "Welcome to Ownership Lens, an autonomous graph agent built on FalkorDB for Track 1: Agents That Act on Connected Data.
>
> Offshore networks hide beneficial ownership behind layers of shell companies and nominee directors. If you search 'Blue Star Maritime' at depth 1, it looks clean: a single director and an ordinary office.
>
> But when our agent traverses FalkorDB to depth 3, the verdict flips to ESCALATE. The graph uncovers a multi-hop path linking Blue Star through a nominee director and an intermediary directly to an entity on the sanctions watchlist.
>
> The LLM never writes raw Cypher and never invents a verdict. All decisions are computed deterministically by graph rules, and every memorandum is verified against real tool output to eliminate hallucinations.
>
> Every decision is written back to FalkorDB as a Case node, so future runs recall past intelligence. That is connected data in action."

---

## "If It Breaks" Backup Plan

If FalkorDB Cloud or the live LLM endpoint experiences an outage during recording:
1. Append `no_llm: true` or toggle the replay mode.
2. All demo runs have pre-generated replay traces stored in `data/replay/`.
3. The UI will prominently display the `REPLAY` badge, showing complete transparency without faking live data.
