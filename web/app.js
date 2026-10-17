// web/app.js — Ownership Lens Client Application Logic
// Institutional Forensic Interface with Interactive Cytoscape Graph Canvas

let cy = null;
const apiBase = window.CONFIG?.API_BASE || "";

document.addEventListener("DOMContentLoaded", () => {
  initCytoscape();
  checkHealth();
  loadDemoConfig();
  setupAutocomplete();
  setupEventListeners();
});

function initCytoscape() {
  cy = cytoscape({
    container: document.getElementById("cy"),
    style: [
      {
        selector: "node",
        style: {
          "label": "data(label)",
          "color": "#0f172a",
          "font-size": "11px",
          "font-weight": "700",
          "font-family": "Plus Jakarta Sans, sans-serif",
          "text-valign": "bottom",
          "text-margin-y": "6px",
          "background-color": "#059669",
          "border-color": "#10b981",
          "border-width": "2.5px",
          "width": "32px",
          "height": "32px",
          "text-background-color": "rgba(255, 255, 255, 0.95)",
          "text-background-opacity": 0.95,
          "text-background-padding": "3px 6px",
          "text-background-shape": "roundrectangle",
        },
      },
      {
        selector: "node[type = 'Officer']",
        style: {
          "background-color": "#d97706",
          "border-color": "#f59e0b",
          "border-width": "2.5px",
          "shape": "diamond",
          "width": "30px",
          "height": "30px",
        },
      },
      {
        selector: "node[type = 'Address']",
        style: {
          "background-color": "#7c3aed",
          "border-color": "#8b5cf6",
          "border-width": "2.5px",
          "shape": "round-rectangle",
          "width": "28px",
          "height": "28px",
        },
      },
      {
        selector: "node[type = 'Intermediary']",
        style: {
          "background-color": "#db2777",
          "border-color": "#ec4899",
          "border-width": "2.5px",
          "shape": "hexagon",
          "width": "32px",
          "height": "32px",
        },
      },
      {
        selector: "node[?isWatchlist]",
        style: {
          "background-color": "#e11d48",
          "border-color": "#be123c",
          "border-width": "4px",
          "width": "40px",
          "height": "40px",
          "color": "#9f1239",
          "font-weight": "800",
          "text-background-color": "rgba(254, 226, 226, 0.98)",
        },
      },
      {
        selector: "edge",
        style: {
          "width": 2,
          "line-color": "#64748b",
          "target-arrow-color": "#475569",
          "target-arrow-shape": "triangle",
          "arrow-scale": 0.95,
          "curve-style": "bezier",
          "label": "data(type)",
          "font-size": "8.5px",
          "font-family": "JetBrains Mono, monospace",
          "font-weight": "600",
          "color": "#1e293b",
          "text-rotation": "autorotate",
          "text-margin-y": "-4px",
          "text-background-color": "rgba(255, 255, 255, 0.95)",
          "text-background-opacity": 0.95,
          "text-background-padding": "1px 4px",
        },
      },
      {
        selector: "edge[?isWatchlistPath]",
        style: {
          "line-color": "#e11d48",
          "target-arrow-color": "#e11d48",
          "width": 3.6,
          "color": "#be123c",
          "font-weight": "bold",
          "text-background-color": "rgba(254, 205, 211, 0.98)",
          "text-background-opacity": 0.98,
        },
      },
      {
        selector: ":selected",
        style: {
          "border-width": "4px",
          "border-color": "#7c3aed",
        },
      },
    ],
    layout: {
      name: "cose",
      animate: false,
    },
  });

  // Tap node event for details inspection
  cy.on("tap", "node", (evt) => {
    const nodeData = evt.target.data();
    showNodeDetails(nodeData);
  });

  // Tap background clears inspection prompt
  cy.on("tap", (evt) => {
    if (evt.target === cy) {
      resetNodeInspector();
    }
  });
}

function showNodeDetails(data) {
  const inspector = document.getElementById("nodeInspector");
  if (!inspector) return;

  const nodeType = data.type || "Entity";
  const label = data.fullLabel || data.label || data.id;
  const isWatchlist = data.isWatchlist ? "<span style='color: #ef4444; font-weight: 700;'>[WATCHLIST TARGET]</span>" : "";

  inspector.innerHTML = `
    <div class="inspector-meta">
      <div><strong>${label}</strong> ${isWatchlist}</div>
      <div style="display: flex; gap: 0.5rem; align-items: center;">
        <span class="inspector-tag">${nodeType}</span>
        <span class="inspector-tag">ID: ${data.id}</span>
      </div>
    </div>
    <div style="font-size: 0.72rem; color: var(--text-tertiary);">Click graph canvas to reset.</div>
  `;
}

function resetNodeInspector() {
  const inspector = document.getElementById("nodeInspector");
  if (!inspector) return;
  inspector.innerHTML = `
    <span id="inspectorPrompt">Click any node in the graph to view attributes, internal node ID, and jurisdiction.</span>
  `;
}

async function checkHealth() {
  const dot = document.getElementById("healthDot");
  const text = document.getElementById("healthText");
  try {
    const res = await fetch(`${apiBase}/health`);
    if (!res.ok) throw new Error("Health check failed");
    const data = await res.json();
    dot.className = `health-dot ${data.db === "ok" ? "ok" : "down"}`;
    const llmStatus = data.llm_key ? "NVIDIA LLM: Connected" : "LLM: Fallback";
    const dataLabel = data.data_source === "icij" ? "Panama Papers (SAM/SEY)" : "Synthetic Data";
    text.textContent = `FalkorDB: Ready • ${dataLabel} • ${llmStatus}`;
    text.title = data.data_disclaimer || "";
  } catch (err) {
    dot.className = "health-dot down";
    text.textContent = "Backend offline (starting up…)";
  }
}

async function loadDemoConfig() {
  try {
    const res = await fetch(`${apiBase}/demo`);
    if (!res.ok) return;
    const data = await res.json();

    if (data.watchlist && data.watchlist.length > 0) {
      document.getElementById("watchlistInput").value = data.watchlist.join(", ");
    }

    const picksContainer = document.getElementById("demoPicks");
    picksContainer.innerHTML = "";
    (data.demo_entities || []).forEach((item) => {
      const card = document.createElement("div");
      card.className = "demo-dossier-card";
      card.tabIndex = 0;
      card.role = "button";

      const flipPill = (item.expected_depth_1 && item.expected_depth_3)
        ? `<span class="demo-dossier-pill">${item.expected_depth_1.toUpperCase()} → ${item.expected_depth_3.toUpperCase()}</span>`
        : "";

      card.innerHTML = `
        <div class="demo-dossier-top">
          <span class="demo-dossier-name" title="${item.name}">${item.name}</span>
          ${flipPill}
        </div>
        <div class="demo-dossier-desc">${item.description || "Offshore entity investigation scenario."}</div>
      `;

      card.addEventListener("click", () => {
        document.getElementById("entityInput").value = item.name;
        // Visual select highlight
        document.querySelectorAll(".demo-dossier-card").forEach((c) => c.classList.remove("selected"));
        card.classList.add("selected");
      });

      card.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          card.click();
        }
      });

      picksContainer.appendChild(card);
    });
  } catch (err) {
    console.error("Failed to load demo config:", err);
  }
}

function setupAutocomplete() {
  const input = document.getElementById("entityInput");
  const suggestionsBox = document.getElementById("suggestions");
  let debounceTimer;

  input.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    const query = input.value.trim();
    if (query.length < 2) {
      suggestionsBox.innerHTML = "";
      return;
    }

    debounceTimer = setTimeout(async () => {
      try {
        const res = await fetch(`${apiBase}/entities/search?q=${encodeURIComponent(query)}`);
        if (!res.ok) return;
        const candidates = await res.json();
        suggestionsBox.innerHTML = "";
        candidates.slice(0, 5).forEach((c) => {
          const item = document.createElement("div");
          item.className = "suggestion-item";
          item.innerHTML = `
            <div class="suggestion-title">
              <span>${c.name}</span>
              <span class="suggestion-id">${c.node_id}</span>
            </div>
            <div class="suggestion-meta">
              ${c.jurisdiction || 'N/A'} • ${c.source || 'N/A'} • ${c.status || 'Active'}
            </div>
          `;
          item.addEventListener("click", () => {
            input.value = c.node_id;
            suggestionsBox.innerHTML = "";
          });
          suggestionsBox.appendChild(item);
        });
      } catch (err) {
        console.debug("Autocomplete error:", err);
      }
    }, 220);
  });

  // Hide suggestions when clicking outside
  document.addEventListener("click", (e) => {
    if (!suggestionsBox.contains(e.target) && e.target !== input) {
      suggestionsBox.innerHTML = "";
    }
  });
}

function setupEventListeners() {
  document.getElementById("btnRun").addEventListener("click", () => runSingleInvestigation());
  document.getElementById("btnCompare").addEventListener("click", () => runDepthComparison());

  // Graph canvas controls
  const btnZoomIn = document.getElementById("btnZoomIn");
  const btnZoomOut = document.getElementById("btnZoomOut");
  const btnFitGraph = document.getElementById("btnFitGraph");
  const btnResetGraph = document.getElementById("btnResetGraph");

  if (btnZoomIn) {
    btnZoomIn.addEventListener("click", () => {
      if (cy) cy.zoom({ level: cy.zoom() * 1.3, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } });
    });
  }
  if (btnZoomOut) {
    btnZoomOut.addEventListener("click", () => {
      if (cy) cy.zoom({ level: cy.zoom() * 0.77, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } });
    });
  }
  if (btnFitGraph) {
    btnFitGraph.addEventListener("click", () => {
      if (cy) cy.fit(null, 35);
    });
  }
  if (btnResetGraph) {
    btnResetGraph.addEventListener("click", () => {
      if (cy) cy.layout({ name: "cose", animate: true, padding: 35 }).run();
    });
  }
}

async function runSingleInvestigation(depthOverride = null) {
  const entityName = document.getElementById("entityInput").value.trim();
  if (!entityName) {
    alert("Please enter an entity name or node ID.");
    return;
  }

  const depth = depthOverride || parseInt(document.getElementById("depthSelect").value, 10);
  const watchlistRaw = document.getElementById("watchlistInput").value;
  const watchlist = watchlistRaw.split(",").map((s) => s.trim()).filter(Boolean);

  const btn = document.getElementById("btnRun");
  btn.disabled = true;
  btn.innerHTML = `
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="animation: spin 1s linear infinite;">
      <circle cx="12" cy="12" r="10"></circle>
      <path d="M12 2a10 10 0 0 1 10 10"></path>
    </svg>
    <span>Investigating…</span>
  `;

  const traceList = document.getElementById("traceList");
  traceList.innerHTML = "";

  document.getElementById("verdictBadge").className = "badge badge-insufficient_evidence";
  document.getElementById("verdictBadge").textContent = "ANALYZING GRAPH…";
  document.getElementById("memoText").textContent = "Traversing beneficial ownership and control paths in FalkorDB…";

  const t0 = performance.now();

  try {
    const res = await fetch(`${apiBase}/investigate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entity: entityName, watchlist, depth }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Investigation request failed");
    }

    const { run_id } = await res.json();
    listenToStream(run_id, t0);
  } catch (err) {
    alert(`Error: ${err.message}`);
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
      </svg>
      <span>Investigate</span>
    `;
  }
}

function listenToStream(runId, startTime) {
  const eventSource = new EventSource(`${apiBase}/stream/${runId}`);
  const traceList = document.getElementById("traceList");

  eventSource.addEventListener("step", (e) => {
    const step = JSON.parse(e.data);
    const item = document.createElement("div");
    item.className = "trace-item";
    item.innerHTML = `
      <div style="display: flex; align-items: center; gap: 0.5rem;">
        <span class="trace-tool">${step.tool}</span>
        <span style="color: var(--text-tertiary); font-size: 0.72rem;">(${step.status})</span>
      </div>
      <div style="display: flex; align-items: center; gap: 0.5rem;">
        <span style="color: var(--text-tertiary); font-size: 0.72rem;">${step.elapsed_ms}ms</span>
        <span class="trace-source">${step.source}</span>
      </div>
    `;
    traceList.prepend(item);
  });

  eventSource.addEventListener("verdict", (e) => {
    const data = JSON.parse(e.data);
    updateVerdictUI(data.verdict, data.evaluation, data.candidates, data.status, data.display_verdict);
  });

  eventSource.addEventListener("memo", (e) => {
    const data = JSON.parse(e.data);
    document.getElementById("memoText").textContent = data.memo;
    document.getElementById("memoSource").textContent = `Source: ${data.memo_source.toUpperCase()}`;
  });

  eventSource.addEventListener("done", (e) => {
    const finalResult = JSON.parse(e.data);
    eventSource.close();

    const elapsed = ((performance.now() - startTime) / 1000).toFixed(2);
    document.getElementById("investigationTime").textContent = `Elapsed: ${elapsed}s`;

    const btn = document.getElementById("btnRun");
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
      </svg>
      <span>Investigate</span>
    `;

    renderGraph(finalResult.evidence);
    renderRecalledCases(finalResult.evidence?.recalled_cases || []);
  });

  eventSource.addEventListener("error", () => {
    eventSource.close();
    const btn = document.getElementById("btnRun");
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
      </svg>
      <span>Investigate</span>
    `;
  });
}

function updateVerdictUI(verdict, evaluation, candidates = [], status = null, displayVerdict = null) {
  const badge = document.getElementById("verdictBadge");
  badge.className = `badge badge-${verdict}`;
  const depth = document.getElementById("depthSelect") ? document.getElementById("depthSelect").value : "2";

  if (displayVerdict) {
    badge.textContent = displayVerdict.toUpperCase();
  } else if (verdict === "clear") {
    badge.textContent = `NO INDICATORS FOUND WITHIN DEPTH ${depth}`;
  } else {
    badge.textContent = verdict.toUpperCase();
  }

  const tbody = document.getElementById("ledgerBody");
  tbody.innerHTML = "";

  // Ambiguous disambiguation handler
  if (status === "ambiguous" && candidates && candidates.length > 0) {
    const trPrompt = document.createElement("tr");
    trPrompt.innerHTML = `
      <td colspan="3" style="background: rgba(245, 158, 11, 0.08); border-left: 3px solid #f59e0b; padding: 0.85rem;">
        <strong style="color: #fbbf24;">Ambiguous Entity: Multiple Registrations Found</strong><br>
        <span style="font-size: 0.78rem; color: var(--text-secondary);">Select the precise target by internal Node ID:</span>
        <div id="disambiguationList" style="display: flex; flex-direction: column; gap: 0.4rem; margin-top: 0.6rem;"></div>
      </td>
    `;
    tbody.appendChild(trPrompt);

    const listDiv = trPrompt.querySelector("#disambiguationList");
    candidates.forEach((cand) => {
      const btn = document.createElement("button");
      btn.className = "demo-dossier-card";
      btn.style.textAlign = "left";
      btn.innerHTML = `<strong>${cand.name}</strong> — Node ID: <code>${cand.node_id}</code> (${cand.jurisdiction || 'N/A'}, ${cand.source || 'N/A'}, ${cand.status || 'Active'})`;
      btn.addEventListener("click", () => {
        document.getElementById("entityInput").value = cand.node_id;
        runSingleInvestigation();
      });
      listDiv.appendChild(btn);
    });
    return;
  }

  const findings = evaluation?.findings || [];
  if (findings.length === 0) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="3" style="text-align: center; color: var(--text-tertiary); padding: 1.5rem;">No exposure indicators found. Evaluation returned clean within specified depth.</td>`;
    tbody.appendChild(tr);
    return;
  }

  findings.forEach((f) => {
    const tr = document.createElement("tr");
    const severityBadge = f.severity === 'high' ? 'escalate' : f.severity === 'medium' ? 'review' : 'insufficient_evidence';
    tr.innerHTML = `
      <td class="rule-cell">${f.rule_id}</td>
      <td><span class="badge badge-${severityBadge}" style="padding: 0.2rem 0.5rem; font-size: 0.7rem;">${f.severity.toUpperCase()}</span></td>
      <td style="color: #cbd5e1; font-size: 0.82rem; line-height: 1.45;">${f.text}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderGraph(evidence) {
  if (!cy || !evidence) return;
  cy.elements().remove();

  const elements = [];
  const addedNodes = new Set();
  const addedEdges = new Set();

  function addNode(n, isWatchlist = false) {
    if (!n || !n.id || addedNodes.has(n.id)) return;
    addedNodes.add(n.id);
    const label = n.name || n.address || n.id;
    elements.push({
      data: {
        id: n.id,
        label: label.length > 28 ? label.slice(0, 26) + "…" : label,
        fullLabel: label,
        type: n.label || "Entity",
        isWatchlist,
      },
    });
  }

  function addEdge(srcId, dstId, relType, isWatchlistPath = false) {
    const edgeKey = `${srcId}_${dstId}_${relType}`;
    if (addedEdges.has(edgeKey)) return;
    addedEdges.add(edgeKey);
    elements.push({
      data: {
        id: `e_${edgeKey}`,
        source: srcId,
        target: dstId,
        type: relType,
        isWatchlistPath,
      },
    });
  }

  // 1. Target node
  if (evidence.resolved_entity) {
    addNode(evidence.resolved_entity);
  }

  // 2. Ownership chain
  (evidence.ownership_chain || []).forEach((path) => {
    const nodes = path.nodes || [];
    const rels = path.relationships || [];
    nodes.forEach((n) => addNode(n));
    for (let i = 0; i < nodes.length - 1; i++) {
      const relType = rels[i]?.type || "CONNECTED_TO";
      addEdge(nodes[i].id, nodes[i + 1].id, relType, false);
    }
  });

  // 3. Watchlist paths
  (evidence.paths_to_watchlist || []).forEach((wp) => {
    const nodes = wp.nodes || [];
    const rels = wp.relationships || [];
    nodes.forEach((n, idx) => addNode(n, idx === nodes.length - 1));
    for (let i = 0; i < nodes.length - 1; i++) {
      const relType = rels[i]?.type || "CONNECTED_TO";
      addEdge(nodes[i].id, nodes[i + 1].id, relType, true);
    }
  });

  // 4. Shared link hubs
  (evidence.shared_links || []).forEach((hub) => {
    if (!hub.hub_id || !evidence.resolved_entity?.id) return;
    addNode({ id: hub.hub_id, name: hub.hub_name, label: hub.hub_type });
    addEdge(evidence.resolved_entity.id, hub.hub_id, "SHARED_HUB", false);
  });

  cy.add(elements);
  cy.layout({ name: "cose", animate: true, padding: 35, randomize: false }).run();
}

function renderRecalledCases(cases) {
  const card = document.getElementById("recalledCard");
  const list = document.getElementById("recalledList");
  if (!cases || cases.length === 0) {
    card.style.display = "none";
    return;
  }

  card.style.display = "block";
  list.innerHTML = "";

  cases.forEach((c) => {
    const div = document.createElement("div");
    div.className = "recalled-item";
    div.innerHTML = `
      <div class="recalled-header">
        <span class="recalled-case-id">${c.case_id}</span>
        <span class="badge badge-${c.verdict}" style="padding: 0.15rem 0.45rem; font-size: 0.68rem;">${c.verdict.toUpperCase()}</span>
      </div>
      <div style="font-size: 0.74rem; color: var(--text-secondary);">
        Shared graph nodes: ${(c.shared_nodes || []).join(", ") || "Direct entity link"}
      </div>
    `;
    list.appendChild(div);
  });
}

async function runDepthComparison() {
  const entityName = document.getElementById("entityInput").value.trim();
  if (!entityName) {
    alert("Please enter an entity name to compare depth 1 vs 3.");
    return;
  }

  const contrastCard = document.getElementById("contrastCard");
  contrastCard.style.display = "block";

  const d1Badge = document.getElementById("contrastD1Badge");
  const d1Memo = document.getElementById("contrastD1Memo");
  const d3Badge = document.getElementById("contrastD3Badge");
  const d3Memo = document.getElementById("contrastD3Memo");

  d1Badge.innerHTML = `<span class="badge badge-insufficient_evidence">RUNNING DEPTH 1…</span>`;
  d1Memo.textContent = "Executing single-hop neighborhood exploration…";
  d3Badge.innerHTML = `<span class="badge badge-insufficient_evidence">AWAITING…</span>`;
  d3Memo.textContent = "Awaiting depth 1 completion before starting multi-hop traversal…";

  const watchlistRaw = document.getElementById("watchlistInput").value;
  const watchlist = watchlistRaw.split(",").map((s) => s.trim()).filter(Boolean);

  try {
    // Run Depth 1
    const res1 = await fetch(`${apiBase}/investigate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entity: entityName, watchlist, depth: 1, no_llm: true }),
    });
    const run1 = await res1.json();
    const r1Data = await awaitRunComplete(run1.run_id);

    const d1Text = r1Data.verdict === "clear" ? "NO INDICATORS FOUND WITHIN DEPTH 1" : r1Data.verdict.toUpperCase();
    d1Badge.innerHTML = `<span class="badge badge-${r1Data.verdict}">${d1Text}</span>`;
    d1Memo.textContent = r1Data.memo || "Depth 1 found no immediate watchlist connections.";

    // Run Depth 3
    d3Badge.innerHTML = `<span class="badge badge-insufficient_evidence">RUNNING DEPTH 3…</span>`;
    d3Memo.textContent = "Traversing 3 hops across nominee hubs and intermediary layers in FalkorDB…";

    const res3 = await fetch(`${apiBase}/investigate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entity: entityName, watchlist, depth: 3, no_llm: true }),
    });
    const run3 = await res3.json();
    const r3Data = await awaitRunComplete(run3.run_id);

    d3Badge.innerHTML = `<span class="badge badge-${r3Data.verdict}">${r3Data.verdict.toUpperCase()}</span>`;
    d3Memo.textContent = r3Data.memo || "Depth 3 completed.";

    // Update main graph with Depth 3 view
    renderGraph(r3Data.evidence);
    updateVerdictUI(r3Data.verdict, r3Data.evaluation);
    document.getElementById("memoText").textContent = r3Data.memo;
    document.getElementById("memoSource").textContent = "Source: DEPTH COMPARISON ENGINE";
  } catch (err) {
    alert(`Comparison failed: ${err.message}`);
  }
}

function awaitRunComplete(runId) {
  return new Promise((resolve, reject) => {
    const es = new EventSource(`${apiBase}/stream/${runId}`);
    es.addEventListener("done", (e) => {
      es.close();
      resolve(JSON.parse(e.data));
    });
    es.addEventListener("error", () => {
      es.close();
      reject(new Error("Stream terminated"));
    });
  });
}
