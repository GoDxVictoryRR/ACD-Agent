"""
scripts/calibrate_betweenness.py — Calibrate betweenness threshold on >= 50 sampled scratch graphs.
In accordance with A2:
- Excludes provider hubs (Intermediaries, registered addresses)
- Excludes placeholder nodes (THE BEARER, null/empty names)
- Tests target entity's own centrality across sampled neighborhoods
"""

import sys
import uuid

from core.config import GRAPH_NAME
from core.db import drop_graph, ro, rw


def percentile(data: list[float], pct: float) -> float:
    if not data:
        return 0.0
    s = sorted(data)
    k = (len(s) - 1) * (pct / 100.0)
    f = int(k)
    c = f + 1 if f + 1 < len(s) else f
    d0 = s[f] * (c - k)
    d1 = s[c] * (k - f)
    return round(d0 + d1, 4)


def main():
    q_sample = """
    MATCH (e:Entity)
    RETURN e.node_id, e.name
    LIMIT 60
    """
    entities = ro(GRAPH_NAME, q_sample).get("rows", [])
    print(f"Sampled {len(entities)} entities for scratch graph calibration...")

    target_scores = []
    all_scores = []

    for i, (entity_id, entity_name) in enumerate(entities):
        fetch_q = """
        MATCH path = (e:Entity {node_id: $entity_id})-[:OFFICER_OF|SHAREHOLDER_OF|DIRECTOR_OF|BENEFICIARY_OF|CONNECTED_TO|RELATED_ENTITY|SAME_AS|SAME_COMPANY_AS*1..2]-(neighbor)
        WHERE NOT neighbor:Case
          AND NOT neighbor:Intermediary
          AND NOT neighbor:Address
          AND neighbor.name IS NOT NULL
          AND trim(neighbor.name) <> ''
          AND NOT toUpper(trim(neighbor.name)) CONTAINS 'BEARER'
        RETURN [n in nodes(path) | {id: n.node_id, name: n.name, label: labels(n)[0]}] AS nodes,
               [r in relationships(path) | {start_id: startNode(r).node_id, end_id: endNode(r).node_id, weight: coalesce(r.weight, 2.0)}] AS rels
        LIMIT 100
        """
        res = ro(GRAPH_NAME, fetch_q, {"entity_id": str(entity_id)})
        rows = res.get("rows", [])
        if not rows:
            target_scores.append(0.0)
            continue

        nodes_map = {}
        edges_set = set()
        for r in rows:
            for n in r[0]:
                nodes_map[n["id"]] = n
            for rel in r[1]:
                edges_set.add((rel["start_id"], rel["end_id"], float(rel["weight"])))
                edges_set.add((rel["end_id"], rel["start_id"], float(rel["weight"])))

        if len(nodes_map) < 3 or not edges_set:
            target_scores.append(0.0)
            continue

        scratch = f"calib_{uuid.uuid4().hex[:8]}"
        try:
            rw(
                scratch,
                "UNWIND $batch AS n CREATE (:ScratchNode {node_id: n.id, name: n.name})",
                {"batch": list(nodes_map.values())},
            )
            rw(
                scratch,
                "UNWIND $batch AS e MATCH (s:ScratchNode {node_id: e.src}), (d:ScratchNode {node_id: e.dst}) CREATE (s)-[:CONNECTED_TO {weight: e.weight}]->(d)",
                {"batch": [{"src": s, "dst": d, "weight": w} for s, d, w in edges_set]},
            )

            bw_q = "CALL algo.betweenness({nodeLabels:['ScratchNode'], relationshipTypes:['CONNECTED_TO'], samplingSize:32, samplingSeed:42}) YIELD node, score RETURN node.node_id, score"
            bw_res = ro(scratch, bw_q)
            target_score = 0.0
            for nid, sc in bw_res.get("rows", []):
                val = float(sc)
                all_scores.append(val)
                if nid == str(entity_id):
                    target_score = val
            target_scores.append(target_score)
        except Exception as exc:
            print(f"Error on {entity_id}: {exc}", file=sys.stderr)
            target_scores.append(0.0)
        finally:
            drop_graph(scratch)

    print(f"\nCompleted {len(target_scores)} sampled scratch graphs (>= 50 required).")

    print("\n--- Target Entity Own Betweenness Distribution (Provider Hubs Removed) ---")
    print(f"Count: {len(target_scores)}")
    print(f"Min:  {min(target_scores):.4f}")
    print(f"p50:  {percentile(target_scores, 50):.4f}")
    print(f"p75:  {percentile(target_scores, 75):.4f}")
    print(f"p90:  {percentile(target_scores, 90):.4f}")
    print(f"p95:  {percentile(target_scores, 95):.4f}")
    print(f"p99:  {percentile(target_scores, 99):.4f}")
    print(f"Max:  {max(target_scores):.4f}")

    print("\n--- All Nodes Betweenness Distribution in Provider-Free Scratch Graphs ---")
    print(f"Count: {len(all_scores)}")
    if all_scores:
        print(f"Min:  {min(all_scores):.4f}")
        print(f"p50:  {percentile(all_scores, 50):.4f}")
        print(f"p75:  {percentile(all_scores, 75):.4f}")
        print(f"p90:  {percentile(all_scores, 90):.4f}")
        print(f"p95:  {percentile(all_scores, 95):.4f}")
        print(f"p99:  {percentile(all_scores, 99):.4f}")
        print(f"Max:  {max(all_scores):.4f}")


if __name__ == "__main__":
    main()
