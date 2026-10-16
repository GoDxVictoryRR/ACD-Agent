// web/app.js — Ownership Lens client application logic

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
          "color": "#e2e8f0",
          "font-size": "11px",
          "text-valign": "bottom",
          "text-margin-y": "4px",
          "background-color": "#3b82f6",
          "width": "28px",
          "height": "28px",
        },
      },
      {
        selector: "node[type = 'Officer']",
        style: {
          "background-color": "#eab308",
          "shape": "diamond",
        },
      },
      {
        selector: "node[type = 'Address']",
        style: {
          "background-color": "#a855f7",
          "shape": "round-rectangle",
        },
      },
      {
        selector: "node[type = 'Intermediary']",
        style: {
          "background-color": "#f97316",
          "shape": "hexagon",
        },
      },
      {
        selector: "node[?isWatchlist]",
        style: {
          "background-color": "#ef4444",
          "border-color": "#fca5a5",
          "border-width": "3px",
          "width": "36px",
          "height": "36px",
        },
      },
      {
        selector: "edge",
        style: {
          "width": 2,
          "line-color": "#475569",
          "target-arrow-color": "#475569",
          "target-arrow-shape": "triangle",
          "curve-style": "bezier",
          "label": "data(type)",
          "font-size": "8px",
          "color": "#94a3b8",
        },
      },
      {
        selector: "edge[?isWatchlistPath]",
        style: {
          "line-color": "#ef4444",
          "target-arrow-color": "#ef4444",
          "width": 3,
        },
      },
    ],
    layout: {
      name: "cose",
      animate: false,
    },
  });
}

async function checkHealth() {
  const dot = document.getElementById("healthDot");
  const text = document.getElementById("healthText");
  try {
    const res = await fetch(`${apiBase}/health`);
    if (!res.ok) throw new Error("Health check failed");
    const data = await res.json();
    dot.className = `health-dot ${data.db === "ok" ? "ok" : "down"}`;
    const llmStatus = data.llm_key ? "LLM: live" : "LLM: fallback";
    const dataLabel = data.data_source === "icij" ? "Data: ICIJ" : "Data: synthetic";
    text.textContent = `DB: ${data.db} | Graph: ${data.graph} | ${llmStatus} | ${dataLabel} | Mode: ${data.mode}`;
    text.title = data.data_disclaimer || "";
  } catch (err) {
    dot.className = "health-dot down";
    text.textContent = "Backend offline (starting up...)";
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
      const btn = document.createElement("button");
      btn.className = "quick-pick-btn";
      btn.textContent = `🏢 ${item.name}`;
      btn.title = item.description || "";
      btn.addEventListener("click", () => {
        document.getElementById("entityInput").value = item.name;
      });
      picksContainer.appendChild(btn);
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
        candidates.slice(0, 4).forEach((c) => {
          const item = document.createElement("div");
          item.style.padding = "0.25rem 0.5rem";
          item.style.background = "var(--bg-secondary)";
          item.style.border = "1px solid var(--border-color)";
          item.style.borderRadius = "3px";
          item.style.cursor = "pointer";
          item.style.fontSize = "0.75rem";
          item.textContent = `${c.name} (${c.jurisdiction || c.label})`;
          item.addEventListener("click", () => {
            input.value = c.name;
            suggestionsBox.innerHTML = "";
          });
          suggestionsBox.appendChild(item);
        });
      } catch (err) {
        console.debug("Autocomplete error:", err);
      }
    }, 250);
  });
}

function setupEventListeners() {
  document.getElementById("btnRun").addEventListener("click", () => runSingleInvestigation());
  document.getElementById("btnCompare").addEventListener("click", () => runDepthComparison());
}

async function runSingleInvestigation(depthOverride = null) {
  const entityName = document.getElementById("entityInput").value.trim();
  if (!entityName) {
    alert("Please enter an entity name.");
    return;
  }

  const depth = depthOverride || parseInt(document.getElementById("depthSelect").value, 10);
  const watchlistRaw = document.getElementById("watchlistInput").value;
  const watchlist = watchlistRaw.split(",").map((s) => s.trim()).filter(Boolean);

  const btn = document.getElementById("btnRun");
  btn.disabled = true;
  btn.textContent = "Investigating...";

  const traceList = document.getElementById("traceList");
  traceList.innerHTML = "";

  document.getElementById("verdictBadge").className = "badge badge-insufficient_evidence";
  document.getElementById("verdictBadge").textContent = "RUNNING...";
  document.getElementById("memoText").textContent = "Gathering graph evidence...";

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
    btn.textContent = "Investigate";
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
      <div>
        <span class="trace-tool">${step.tool}</span>
        <span style="color: var(--text-muted); font-size: 0.75rem;">(${step.status})</span>
      </div>
      <div>
        <span style="color: var(--text-muted); margin-right: 0.5rem;">${step.elapsed_ms}ms</span>
        <span class="trace-source">${step.source}</span>
      </div>
    `;
    traceList.prepend(item);
  });

  eventSource.addEventListener("verdict", (e) => {
    const data = JSON.parse(e.data);
    updateVerdictUI(data.verdict, data.evaluation);
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
    btn.textContent = "Investigate";

    renderGraph(finalResult.evidence);
    renderRecalledCases(finalResult.evidence?.recalled_cases || []);
  });

  eventSource.addEventListener("error", (e) => {
    eventSource.close();
    const btn = document.getElementById("btnRun");
    btn.disabled = false;
    btn.textContent = "Investigate";
  });
}

function updateVerdictUI(verdict, evaluation) {
  const badge = document.getElementById("verdictBadge");
  badge.className = `badge badge-${verdict}`;
  badge.textContent = verdict.toUpperCase();

  const tbody = document.getElementById("ledgerBody");
  tbody.innerHTML = "";

  const findings = evaluation?.findings || [];
  if (findings.length === 0) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="3" style="text-align: center; color: var(--text-muted);">No risk findings. Clean evaluation.</td>`;
    tbody.appendChild(tr);
    return;
  }

  findings.forEach((f) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="font-family: var(--font-mono); font-weight: 600;">${f.rule_id}</td>
      <td><span class="badge badge-${f.severity === 'high' ? 'escalate' : f.severity === 'medium' ? 'review' : 'insufficient_evidence'}">${f.severity.toUpperCase()}</span></td>
      <td>${f.text}</td>
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
    // Use name for Entity/Officer/Intermediary; address for Address nodes
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

  // 2. Ownership chain — use actual rel types from data
  (evidence.ownership_chain || []).forEach((path) => {
    const nodes = path.nodes || [];
    const rels = path.relationships || [];
    nodes.forEach((n) => addNode(n));
    for (let i = 0; i < nodes.length - 1; i++) {
      const relType = rels[i]?.type || "CONNECTED_TO";
      addEdge(nodes[i].id, nodes[i + 1].id, relType, false);
    }
  });

  // 3. Watchlist paths — actual rel types, red highlight
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
  cy.layout({ name: "cose", animate: true, padding: 30, randomize: false }).run();
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
    div.style.background = "var(--bg-secondary)";
    div.style.padding = "0.5rem";
    div.style.borderRadius = "4px";
    div.style.border = "1px solid var(--border-color)";
    div.innerHTML = `
      <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
        <span style="font-family: var(--font-mono); font-size: 0.75rem;">${c.case_id}</span>
        <span class="badge badge-${c.verdict}">${c.verdict.toUpperCase()}</span>
      </div>
      <div style="font-size: 0.75rem; color: var(--text-muted);">
        Shared nodes: ${(c.shared_nodes || []).join(", ") || "Direct"}
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

  d1Badge.innerHTML = `<span class="badge badge-insufficient_evidence">RUNNING DEPTH 1...</span>`;
  d1Memo.textContent = "Executing single-hop exploration...";
  d3Badge.innerHTML = `<span class="badge badge-insufficient_evidence">AWAITING...</span>`;
  d3Memo.textContent = "Awaiting depth 1 completion...";

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

    d1Badge.innerHTML = `<span class="badge badge-${r1Data.verdict}">${r1Data.verdict.toUpperCase()}</span>`;
    d1Memo.textContent = r1Data.memo || "Depth 1 found no immediate watchlist connections.";

    // Run Depth 3
    d3Badge.innerHTML = `<span class="badge badge-insufficient_evidence">RUNNING DEPTH 3...</span>`;
    d3Memo.textContent = "Traversing 3 hops across nominee hubs and intermediaries...";

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
    document.getElementById("memoSource").textContent = "Source: DEPTH COMPARISON";
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
    es.addEventListener("error", (e) => {
      es.close();
      reject(new Error("Stream terminated"));
    });
  });
}
