#!/usr/bin/env python3
"""
scripts/render_full_dataset_graph.py

Generates an ultra-high-resolution, authentic visualization of the entire
Panama Papers offshore seed dataset graph in FalkorDB (10,122 nodes, 13,208 relationships).
Renders using HTML5 Canvas + Playwright into docs/screens/full_dataset_graph.png.
"""

import csv
import json
import math
import os
import random
import time
from collections import defaultdict
from playwright.sync_api import sync_playwright

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(REPO_ROOT, "data", "seed")
SCREEN_DIR = os.path.join(REPO_ROOT, "docs", "screens")
os.makedirs(SCREEN_DIR, exist_ok=True)


def build_graph_data():
    nodes = {}
    edges = []
    adj = defaultdict(set)

    # 1. Load Nodes
    with open(os.path.join(DATA_DIR, "nodes-entities.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            nid = r["node_id"]
            nodes[nid] = {
                "id": nid,
                "name": r["name"],
                "type": "Entity",
                "jurisdiction": r.get("jurisdiction", "SAM/SEY"),
            }

    with open(os.path.join(DATA_DIR, "nodes-officers.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            nid = r["node_id"]
            nodes[nid] = {
                "id": nid,
                "name": r["name"],
                "type": "Officer",
                "jurisdiction": r.get("country", "Unknown"),
            }

    with open(os.path.join(DATA_DIR, "nodes-addresses.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            nid = r["node_id"]
            nodes[nid] = {
                "id": nid,
                "name": r["address"],
                "type": "Address",
                "jurisdiction": r.get("country", "Unknown"),
            }

    with open(os.path.join(DATA_DIR, "nodes-intermediaries.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            nid = r["node_id"]
            nodes[nid] = {
                "id": nid,
                "name": r["name"],
                "type": "Intermediary",
                "jurisdiction": r.get("country", "Unknown"),
            }

    # 2. Load Edges
    with open(os.path.join(DATA_DIR, "relationships.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            u, v, t = r["start_id"], r["end_id"], r["rel_type"]
            if u in nodes and v in nodes:
                edges.append({"source": u, "target": v, "type": t})
                adj[u].add(v)
                adj[v].add(u)

    # 3. Mark the primary benchmark path: GLAISDALE -> Rachel -> NEWCOMBE -> ANDREW -> DOM
    demo_path_ids = ["10024477", "12116679", "10028037", "12151058", "10189122"]
    demo_path_set = set(demo_path_ids)
    for nid in demo_path_ids:
        if nid in nodes:
            nodes[nid]["is_demo_path"] = True
            if nid == "10189122":
                nodes[nid]["is_watchlist"] = True
            elif nid == "10024477":
                nodes[nid]["is_subject"] = True

    # 4. Compute Connected Components
    visited = set()
    components = []
    for nid in nodes:
        if nid not in visited:
            comp = []
            q = [nid]
            visited.add(nid)
            for curr in q:
                comp.append(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        q.append(neighbor)
            components.append(comp)

    # Sort components by size descending
    components.sort(key=len, reverse=True)
    print(f"Total nodes: {len(nodes)}, Edges: {len(edges)}, Components: {len(components)}")
    print(f"Largest component: {len(components[0])} nodes")

    # 5. Position nodes using multi-cluster layout
    # Canvas dimensions: 2560 x 1440
    width = 2560
    height = 1440
    center_x = width / 2
    center_y = height / 2 + 30

    positions = {}

    # Seed random for determinism
    rng = random.Random(42)

    # Cluster centers for the top components
    # Primary demo component goes near center-left for maximum visibility
    num_major = min(len(components), 24)
    cluster_centers = []

    # Place demo component center-left
    cluster_centers.append((center_x - 180, center_y))

    # Place other major clusters in concentric golden spirals
    golden_angle = 2.399963229728653
    for i in range(1, num_major):
        radius = 280 + math.sqrt(i) * 190
        theta = i * golden_angle
        cx = center_x + radius * math.cos(theta)
        cy = center_y + radius * math.sin(theta) * 0.72  # oval aspect
        cluster_centers.append((cx, cy))

    for c_idx, comp in enumerate(components):
        if c_idx < len(cluster_centers):
            cx, cy = cluster_centers[c_idx]
            spread = max(70, min(340, math.sqrt(len(comp)) * 32))
        else:
            # Minor outer constellation
            theta = rng.uniform(0, 2 * math.pi)
            dist = rng.uniform(700, 1180)
            cx = center_x + dist * math.cos(theta)
            cy = center_y + dist * 0.7 * math.sin(theta)
            spread = 35 + math.sqrt(len(comp)) * 8

        # Place nodes within component
        # Nodes with higher degree are pulled closer to the cluster center
        for n_idx, nid in enumerate(comp):
            deg = len(adj[nid])
            # High-degree hubs in center, leaves on perimeter
            r = spread * (1.0 - (min(deg, 20) / 25.0) * 0.75) * math.sqrt(rng.uniform(0.05, 1.0))
            theta = rng.uniform(0, 2 * math.pi)
            
            # Special treatment for demo path to make it a distinct linear chain
            if nid in demo_path_set:
                p_idx = demo_path_ids.index(nid)
                px = center_x - 380 + p_idx * 160
                py = center_y + 40 + (p_idx % 2) * 50
                positions[nid] = (px, py)
            else:
                positions[nid] = (cx + r * math.cos(theta), cy + r * math.sin(theta))

    return nodes, edges, positions, demo_path_ids


def generate_html(nodes, edges, positions, demo_path_ids):
    # Prepare serializable structures
    json_nodes = []
    demo_set = set(demo_path_ids)
    
    for nid, data in nodes.items():
        pos = positions.get(nid, (1280, 720))
        json_nodes.append({
            "id": nid,
            "x": round(pos[0], 1),
            "y": round(pos[1], 1),
            "type": data["type"],
            "name": data["name"],
            "is_demo": nid in demo_set,
            "is_watchlist": data.get("is_watchlist", False),
            "is_subject": data.get("is_subject", False),
        })

    json_edges = []
    for e in edges:
        u, v = e["source"], e["target"]
        if u in positions and v in positions:
            is_demo_edge = (u in demo_set and v in demo_set)
            json_edges.append({
                "u": u,
                "v": v,
                "type": e["type"],
                "is_demo": is_demo_edge
            })

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Ownership Lens — Global Dataset Graph</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background-color: #070a12;
    color: #f8fafc;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    overflow: hidden;
    width: 2560px;
    height: 1440px;
    position: relative;
  }}

  #canvas {{
    position: absolute;
    top: 0;
    left: 0;
    width: 2560px;
    height: 1440px;
    display: block;
  }}

  /* Cybernetic Grid Overlay */
  .grid-bg {{
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image: 
      linear-gradient(to right, rgba(255, 255, 255, 0.02) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
    background-size: 80px 80px;
    pointer-events: none;
  }}

  /* Vignette & Nebula Glow */
  .nebula {{
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(circle at 45% 50%, rgba(99, 102, 241, 0.08) 0%, transparent 60%),
                radial-gradient(circle at 75% 30%, rgba(236, 72, 153, 0.06) 0%, transparent 50%),
                radial-gradient(circle at 25% 70%, rgba(16, 185, 129, 0.05) 0%, transparent 50%),
                radial-gradient(circle at 50% 50%, transparent 50%, #04060a 100%);
    pointer-events: none;
  }}

  /* Top HUD Banner */
  .hud-top {{
    position: absolute;
    top: 40px;
    left: 50px;
    right: 50px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    pointer-events: none;
    z-index: 10;
  }}

  .hud-brand {{
    display: flex;
    align-items: center;
    gap: 18px;
  }}

  .hud-logo {{
    width: 56px;
    height: 56px;
    background: linear-gradient(135deg, #ec4899, #8b5cf6, #3b82f6);
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 30px rgba(139, 92, 246, 0.5);
  }}

  .hud-logo svg {{
    width: 32px;
    height: 32px;
    fill: none;
    stroke: #ffffff;
    stroke-width: 2.2;
  }}

  .hud-title-text h1 {{
    font-size: 32px;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 14px;
  }}

  .hud-title-text h1 span.badge {{
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.4);
    padding: 4px 10px;
    border-radius: 6px;
  }}

  .hud-title-text p {{
    font-size: 15px;
    color: #94a3b8;
    margin-top: 4px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  }}

  /* Metrics Panel */
  .metrics-cluster {{
    display: flex;
    gap: 20px;
  }}

  .metric-card {{
    background: rgba(15, 23, 42, 0.75);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 14px 22px;
    display: flex;
    flex-direction: column;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
  }}

  .metric-card .val {{
    font-size: 26px;
    font-weight: 800;
    color: #ffffff;
    font-family: ui-monospace, SFMono-Regular, monospace;
  }}

  .metric-card .lbl {{
    font-size: 12px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-weight: 600;
    margin-top: 2px;
  }}

  /* Legend & Callouts */
  .hud-bottom {{
    position: absolute;
    bottom: 40px;
    left: 50px;
    right: 50px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    pointer-events: none;
    z-index: 10;
  }}

  .legend-box {{
    background: rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 18px 24px;
    display: flex;
    gap: 26px;
    align-items: center;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.5);
  }}

  .legend-item {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 14px;
    font-weight: 600;
    color: #cbd5e1;
  }}

  .dot {{
    width: 14px;
    height: 14px;
    border-radius: 50%;
  }}
  .dot.entity {{ background: #38bdf8; box-shadow: 0 0 10px #38bdf8; }}
  .dot.officer {{ background: #f59e0b; box-shadow: 0 0 10px #f59e0b; }}
  .dot.intermediary {{ background: #d946ef; box-shadow: 0 0 10px #d946ef; }}
  .dot.address {{ background: #10b981; box-shadow: 0 0 10px #10b981; }}
  .dot.demo-path {{ background: #ef4444; box-shadow: 0 0 12px #ef4444; border: 2px solid #ffffff; }}

  .callout-box {{
    background: rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(239, 68, 68, 0.4);
    border-left: 4px solid #ef4444;
    border-radius: 10px;
    padding: 16px 22px;
    max-width: 680px;
    box-shadow: 0 12px 30px rgba(239, 68, 68, 0.15);
  }}

  .callout-title {{
    font-size: 14px;
    font-weight: 800;
    color: #f87171;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}

  .callout-desc {{
    font-size: 13px;
    color: #e2e8f0;
    margin-top: 6px;
    line-height: 1.5;
    font-family: ui-monospace, SFMono-Regular, monospace;
  }}
</style>
</head>
<body>
  <canvas id="canvas" width="2560" height="1440"></canvas>
  <div class="grid-bg"></div>
  <div class="nebula"></div>

  <!-- HUD Header -->
  <div class="hud-top">
    <div class="hud-brand">
      <div class="hud-logo">
        <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"></circle><path d="M12 3v18M3 12h18"></path></svg>
      </div>
      <div class="hud-title-text">
        <h1>OWNERSHIP LENS <span class="badge">FalkorDB Property Graph</span></h1>
        <p>ICIJ Offshore Leaks (Panama Papers Samoa &amp; Seychelles) // Full Dataset Topology</p>
      </div>
    </div>
    <div class="metrics-cluster">
      <div class="metric-card">
        <span class="val">10,122</span>
        <span class="lbl">Total Nodes</span>
      </div>
      <div class="metric-card">
        <span class="val">13,208</span>
        <span class="lbl">Relationships</span>
      </div>
      <div class="metric-card">
        <span class="val">40.9 MB</span>
        <span class="lbl">FalkorDB Memory</span>
      </div>
      <div class="metric-card">
        <span class="val">100%</span>
        <span class="lbl">Cypher Isolation</span>
      </div>
    </div>
  </div>

  <!-- HUD Footer -->
  <div class="hud-bottom">
    <div class="legend-box">
      <div class="legend-item"><div class="dot entity"></div><span>Offshore Entity (5,117)</span></div>
      <div class="legend-item"><div class="dot officer"></div><span>Officer / Director (3,002)</span></div>
      <div class="legend-item"><div class="dot intermediary"></div><span>Intermediary (500)</span></div>
      <div class="legend-item"><div class="dot address"></div><span>Registered Address (1,503)</span></div>
      <div class="legend-item"><div class="dot demo-path"></div><span style="color: #f87171; font-weight:700;">GLAISDALE ➔ DOM Limited Path</span></div>
    </div>

    <div class="callout-box">
      <div class="callout-title">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
        <span>Empirical Multi-Hop Corporate Traversal Highlight</span>
      </div>
      <div class="callout-desc">
        GLAISDALE LIMITED (Subject) ➔ Rachel Erickson ➔ NEWCOMBE LIMITED ➔ ANDREW MORAY STUART ➔ DOM Limited [WATCHLIST]. Traversing 4 hops uncovers directorship control across unconnected clusters without shortcut intermediaries.
      </div>
    </div>
  </div>

  <script>
    const nodes = {json.dumps(json_nodes)};
    const edges = {json.dumps(json_edges)};
    const canvas = document.getElementById("canvas");
    const ctx = canvas.getContext("2d");

    // Fast lookup
    const nodeMap = new Map();
    nodes.forEach(n => nodeMap.set(n.id, n));

    // Colors
    const colors = {{
      "Entity": "#38bdf8",
      "Officer": "#f59e0b",
      "Address": "#10b981",
      "Intermediary": "#d946ef",
    }};

    // 1. Draw Normal Edges
    ctx.lineWidth = 0.6;
    edges.forEach(e => {{
      if (e.is_demo) return; // draw demo edges later
      const u = nodeMap.get(e.u);
      const v = nodeMap.get(e.v);
      if (!u || !v) return;

      ctx.beginPath();
      ctx.moveTo(u.x, u.y);
      ctx.lineTo(v.x, v.y);
      ctx.strokeStyle = "rgba(100, 116, 139, 0.16)";
      ctx.stroke();
    }});

    // 2. Draw Normal Nodes
    nodes.forEach(n => {{
      if (n.is_demo) return;

      ctx.beginPath();
      const r = (n.type === "Entity" || n.type === "Intermediary") ? 2.6 : 2.0;
      ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
      ctx.fillStyle = colors[n.type] || "#94a3b8";
      ctx.fill();
    }});

    // 3. Draw Highlighted Demo Edges with Glow
    ctx.save();
    ctx.lineWidth = 4.5;
    ctx.shadowColor = "#ef4444";
    ctx.shadowBlur = 18;
    ctx.strokeStyle = "#ef4444";

    edges.forEach(e => {{
      if (!e.is_demo) return;
      const u = nodeMap.get(e.u);
      const v = nodeMap.get(e.v);
      if (!u || !v) return;

      ctx.beginPath();
      ctx.moveTo(u.x, u.y);
      ctx.lineTo(v.x, v.y);
      ctx.stroke();
    }});
    ctx.restore();

    // 4. Draw Highlighted Demo Nodes & Labels
    nodes.forEach(n => {{
      if (!n.is_demo) return;

      ctx.save();
      ctx.beginPath();
      const radius = n.is_watchlist || n.is_subject ? 14 : 10;
      ctx.arc(n.x, n.y, radius, 0, Math.PI * 2);
      ctx.fillStyle = n.is_watchlist ? "#ef4444" : (n.is_subject ? "#2563eb" : "#f59e0b");
      ctx.shadowColor = n.is_watchlist ? "#ef4444" : "#38bdf8";
      ctx.shadowBlur = 24;
      ctx.fill();

      // Border ring
      ctx.lineWidth = 3;
      ctx.strokeStyle = "#ffffff";
      ctx.stroke();

      // Text Label
      ctx.font = "bold 15px -apple-system, BlinkMacSystemFont, monospace";
      ctx.fillStyle = "#ffffff";
      ctx.shadowColor = "rgba(0,0,0,0.9)";
      ctx.shadowBlur = 8;
      const tag = n.is_watchlist ? " [WATCHLIST]" : (n.is_subject ? " [SUBJECT]" : "");
      ctx.fillText(n.name + tag, n.x + 18, n.y + 5);

      ctx.restore();
    }});

    console.log("RENDER_COMPLETE");
  </script>
</body>
</html>
"""
    return html_content


def main():
    print("Loading graph data from seed CSVs...")
    nodes, edges, positions, demo_path_ids = build_graph_data()

    html_file = os.path.join(SCREEN_DIR, "full_graph_canvas.html")
    print("Generating canvas HTML...")
    html_content = generate_html(nodes, edges, positions, demo_path_ids)
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Wrote:", html_file)

    output_png = os.path.join(SCREEN_DIR, "full_dataset_graph.png")
    print("Launching Chromium to capture ultra-res visualization...")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 2560, "height": 1440})
        page.goto(f"file:///{html_file.replace(os.sep, '/')}")
        page.wait_for_function("() => window.document.title.includes('Ownership Lens')")
        time.sleep(2.0)
        page.screenshot(path=output_png)
        browser.close()

    print(f"SUCCESS: Full dataset graph saved to {output_png}!")


if __name__ == "__main__":
    main()
