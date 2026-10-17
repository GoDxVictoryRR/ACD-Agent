"""
scripts/test_subset_search.py — Search for candidate depth-contrast pairs in SAM+SEY cluster.
"""

import csv
import heapq
from collections import defaultdict
from pathlib import Path

raw_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
target_source = "Panama Papers"
target_jur = {"SAM", "SEY"}

entities = {}
with open(raw_dir / "nodes-entities.csv", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        if row.get("sourceID") == target_source and row.get("jurisdiction") in target_jur:
            entities[row["node_id"]] = row.get("name", "")

node_labels = {nid: "Entity" for nid in entities}

adj = defaultdict(dict)
weights = {
    "officer_of": 1.0,
    "intermediary_of": 2.0,
    "registered_address": 3.0,
    "connected_to": 2.5,
    "underlying": 1.5,
    "same_name_as": 4.0,
    "same_address_as": 4.0,
}

with open(raw_dir / "relationships.csv", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        s = row["node_id_start"]
        e = row["node_id_end"]
        rt = row["rel_type"]
        if s in entities or e in entities:
            w = weights.get(rt, 2.5)
            adj[s][e] = (rt, w)
            adj[e][s] = (rt, w)

for fname, lbl in [
    ("nodes-officers.csv", "Officer"),
    ("nodes-addresses.csv", "Address"),
    ("nodes-intermediaries.csv", "Intermediary"),
]:
    with open(raw_dir / fname, encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            nid = row["node_id"]
            if nid in adj and nid not in node_labels:
                node_labels[nid] = lbl

print(f"Total nodes in cluster: {len(adj):,}")
hub_deg = {n: len(adj[n]) for n in adj}

candidates = []
for a in entities:
    if len(adj[a]) < 1:
        continue
    violates = False
    for n1 in adj[a]:
        lbl = node_labels.get(n1, "Unknown")
        d = hub_deg[n1]
        if lbl == "Address" and d >= 5:
            violates = True
            break
        if lbl == "Officer" and d >= 5:
            violates = True
            break
        if lbl == "Intermediary" and d >= 10:
            violates = True
            break
    if violates:
        continue

    # BFS unweighted to find hop distances up to 3
    bfs_dist = {a: 0}
    q_bfs = [a]
    while q_bfs:
        u = q_bfs.pop(0)
        if bfs_dist[u] >= 3:
            continue
        for v in adj[u]:
            if v not in bfs_dist:
                bfs_dist[v] = bfs_dist[u] + 1
                q_bfs.append(v)

    # Dijkstra up to depth 3
    visited = {}
    queue = [(0.0, 0, a, [a])]
    while queue:
        c, h, curr, path = heapq.heappop(queue)
        if curr in visited and visited[curr][0] <= c:
            continue
        visited[curr] = (c, h, path)
        if h >= 3:
            continue
        for nbr, (rt, w) in adj[curr].items():
            if nbr not in path:
                heapq.heappush(queue, (c + w, h + 1, nbr, path + [nbr]))

    for target, (cost, hops, path) in visited.items():
        if target != a and node_labels.get(target) == "Entity":
            if hops == 3 and cost <= 8.0 and bfs_dist.get(target) == 3:
                candidates.append((a, target, cost, path))
                if len(candidates) >= 15:
                    break
    if len(candidates) >= 15:
        break

print(f"Found {len(candidates)} candidate pairs!")
for a, b, cost, p in candidates[:10]:
    p_desc = [f"{n} ({node_labels.get(n)}: {entities.get(n, n)})" for n in p]
    print(f"A: {a} ({entities.get(a)}) -> B: {b} ({entities.get(b)}): cost={cost:.1f}")
    arrow = " -> "
    print(f"  Path: {arrow.join(p_desc)}")
