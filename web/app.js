// web/app.js — Ownership Lens Client Application Logic
// Institutional Forensic Interface with Interactive Cytoscape Graph Canvas

let cy = null;
let lastEvidence = null;
let cyCompareD1 = null;
let cyCompareD4 = null;
const apiBase = window.CONFIG?.API_BASE || "";

const SERVICE_PROVIDER_PATTERNS = [
  "MOSSACK", "FONSECA", "MOSSFON", "PORTCULLIS", "TRUST",
  "MANAGEMENT", "SERVICES", "NOMINEE", "NOMINEES", "CORPORATE SERVICES",
  "FIDUCIARY", "SECRETARIAL", "CONSULTING", "REGISTRARS", "AGENTS",
  "SOLICITORS", "LAW", "CHAMBERS", "LEGAL", "ADVISORY", "INTERCON"
];

function isServiceProvider(name) {
  if (!name) return true;
  const upper = name.trim().toUpperCase();
  if (upper === "BEARER" || upper === "THE BEARER" || upper.length === 0) return true;
  return SERVICE_PROVIDER_PATTERNS.some((p) => upper.includes(p));
}

function isAddressHub(node) {
  if (!node) return false;
  const label = (node.label || node.type || "").toLowerCase();
  return label === "address";
}

function formatGraphLabel(name) {
  if (!name) return "";
  const trimmed = name.trim();
  if (trimmed.length > 28) {
    return trimmed.slice(0, 26) + "…";
  }
  return trimmed;
}

function formatRelLabel(type) {
  if (!type) return "";
  const t = type.toUpperCase().replace(/\s+/g, "_");
  if (t === "OFFICER_OF") return "officer of";
  if (t === "INTERMEDIARY_OF") return "intermediary of";
  if (t === "REGISTERED_ADDRESS" || t === "ADDRESS_OF") return "registered address";
  if (t === "CONNECTED_TO") return "connected to";
  return t.toLowerCase().replace(/_/g, " ");
}

function getCyStyles(isMobile) {
  return [
    {
      selector: "node",
      style: {
        "shape": "ellipse",
        "width": isMobile ? "30px" : "36px",
        "height": isMobile ? "30px" : "36px",
        "background-color": "#ffffff",
        "border-color": "#dc2626",
        "border-width": "3.5px",
        "label": "data(label)",
        "color": "#0f172a",
        "font-size": isMobile ? "10px" : "11px",
        "font-weight": "700",
        "font-family": "Plus Jakarta Sans, sans-serif",
        "text-wrap": "wrap",
        "text-max-width": "110px",
        "text-valign": isMobile ? "center" : "bottom",
        "text-halign": isMobile ? "right" : "center",
        "text-margin-y": isMobile ? "0px" : "10px",
        "text-margin-x": isMobile ? "14px" : "0px",
        "text-background-color": "#ffffff",
        "text-background-opacity": 0.92,
        "text-background-padding": "3px",
        "text-background-shape": "roundrectangle",
      },
    },
    {
      selector: "node[type = 'Officer']",
      style: {
        "shape": "diamond",
        "width": isMobile ? "28px" : "34px",
        "height": isMobile ? "28px" : "34px",
        "background-color": "#f8fafc",
        "border-color": "#dc2626",
      },
    },
    {
      selector: "node[type = 'Intermediary']",
      style: {
        "shape": "hexagon",
        "width": isMobile ? "30px" : "36px",
        "height": isMobile ? "30px" : "36px",
        "background-color": "#f8fafc",
        "border-color": "#dc2626",
      },
    },
    {
      selector: "node[type = 'Address']",
      style: {
        "shape": "rectangle",
        "width": isMobile ? "26px" : "32px",
        "height": isMobile ? "26px" : "32px",
        "background-color": "#f8fafc",
        "border-color": "#dc2626",
      },
    },
    {
      selector: "node[?isSubject]",
      style: {
        "background-color": "#ffffff",
        "border-color": "#2563eb",
        "border-width": "4.5px",
        "outline-width": "3px",
        "outline-color": "#93c5fd",
        "outline-opacity": 0.8,
        "width": isMobile ? "34px" : "40px",
        "height": isMobile ? "34px" : "40px",
        "color": "#1e40af",
      },
    },
    {
      selector: "node[?isWatchlistTarget]",
      style: {
        "background-color": "#dc2626",
        "border-color": "#991b1b",
        "border-width": "4px",
        "width": isMobile ? "34px" : "40px",
        "height": isMobile ? "34px" : "40px",
        "color": "#991b1b",
        "text-background-color": "#fee2e2",
        "text-background-opacity": 0.98,
        "text-border-color": "#dc2626",
        "text-border-width": "1px",
        "text-border-opacity": 0.8,
      },
    },
    {
      selector: "node[?isContext]",
      style: {
        "background-color": "#94a3b8",
        "border-color": "#cbd5e1",
        "border-width": "2px",
        "opacity": 0.35,
        "width": "18px",
        "height": "18px",
        "label": "",
      },
    },
    {
      selector: "node[?isContext]:hover",
      style: {
        "opacity": 0.95,
        "label": "data(label)",
        "font-size": "9px",
        "text-background-opacity": 0.95,
      },
    },
    {
      selector: "edge",
      style: {
        "width": 1.5,
        "line-color": "#cbd5e1",
        "curve-style": "straight",
        "target-arrow-shape": "none",
        "label": "",
      },
    },
    {
      selector: "edge[?isPathEdge]",
      style: {
        "width": 4,
        "line-color": "#dc2626",
        "target-arrow-shape": "triangle",
        "target-arrow-color": "#dc2626",
        "arrow-scale": 1.2,
        "curve-style": "straight",
        "label": "data(label)",
        "edge-text-rotation": "none",
        "font-size": isMobile ? "8.5px" : "9.5px",
        "font-family": "JetBrains Mono, monospace",
        "font-weight": "600",
        "color": "#991b1b",
        "text-background-color": "#ffffff",
        "text-background-opacity": 0.95,
        "text-background-padding": "3px",
        "text-background-shape": "roundrectangle",
        "text-border-color": "#fca5a5",
        "text-border-width": "1px",
        "text-border-opacity": 0.8,
      },
    },
    {
      selector: ":selected",
      style: {
        "border-width": "5px",
        "border-color": "#7c3aed",
      },
    },
  ];
}

document.addEventListener("DOMContentLoaded", () => {
  initCytoscape();
  checkHealth();
  loadDemoConfig();
  setupAutocomplete();
  setupEventListeners();
});

function initCytoscape() {
  const isMobile = window.innerWidth <= 600;
  cy = cytoscape({
    container: document.getElementById("cy"),
    style: getCyStyles(isMobile),
    minZoom: 0.25,
    maxZoom: 2.0,
    layout: {
      name: "preset",
    },
  });
  window.cy = cy;

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
  const name = data.fullLabel || data.name || data.id;
  const tagHtml = data.isSubject
    ? `<span class="inspector-badge-subject">SUBJECT</span>`
    : data.isWatchlistTarget
    ? `<span class="inspector-badge-watchlist">WATCHLIST (demo)</span>`
    : "";

  inspector.innerHTML = `
    <div class="inspector-card">
      <div class="inspector-header">
        <strong class="inspector-name">${name}</strong>
        ${tagHtml}
      </div>
      <div class="inspector-grid">
        <div class="inspector-field"><span>Type:</span> <strong>${nodeType}</strong></div>
        <div class="inspector-field"><span>Node ID:</span> <code>${data.node_id || data.id}</code></div>
        <div class="inspector-field"><span>Jurisdiction:</span> <strong>${data.jurisdiction || "N/A"}</strong></div>
        <div class="inspector-field"><span>Source:</span> <strong>${data.source || "Panama Papers"}</strong></div>
        <div class="inspector-field"><span>Status:</span> <strong>${data.status || "Active"}</strong></div>
      </div>
    </div>
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

      const d1 = item.expected_depth_1 ? item.expected_depth_1.toUpperCase() : "";
      const d4 = (item.expected_depth_4 || item.expected_depth_3)
        ? (item.expected_depth_4 || item.expected_depth_3).toUpperCase()
        : "";
      let flipPill = "";
      if (d1 && d4) {
        if (d1 === d4) {
          flipPill = `<span class="demo-dossier-pill">${d1}</span>`;
        } else {
          flipPill = `<span class="demo-dossier-pill">${d1} → ${d4}</span>`;
        }
      } else if (d1) {
        flipPill = `<span class="demo-dossier-pill">${d1}</span>`;
      }

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

  // Context nodes toggle
  const toggleContext = document.getElementById("toggleContext");
  if (toggleContext) {
    toggleContext.addEventListener("change", () => {
      if (lastEvidence) renderGraph(lastEvidence);
    });
  }

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
      if (cy) {
        cy.resize();
        cy.fit(cy.elements(), 80);
        cy.center();
      }
    });
  }
  if (btnResetGraph) {
    btnResetGraph.addEventListener("click", () => {
      if (cy && lastEvidence) {
        renderGraph(lastEvidence);
      } else if (cy) {
        cy.resize();
        cy.fit(cy.elements(), 80);
        cy.center();
      }
    });
  }

  // Auto-refit graph on browser resize
  let resizeDebounceTimer;
  window.addEventListener("resize", () => {
    clearTimeout(resizeDebounceTimer);
    resizeDebounceTimer = setTimeout(() => {
      if (cy && lastEvidence) {
        cy.resize();
        renderGraph(lastEvidence);
      }
    }, 150);
  });

  // Window resize to handle mobile/desktop layout transition
  let resizeTimer;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      if (cy && lastEvidence) {
        renderGraph(lastEvidence);
      }
    }, 150);
  });
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

  const urlParams = new URLSearchParams(window.location.search);
  const toggleAi = document.getElementById("toggleAiMode");
  // Default to deterministic mode (~1s) per H1. Only use LLM if toggle checked or ?mode=ai
  let useAi = toggleAi ? toggleAi.checked : false;
  if (urlParams.get("mode") === "ai") {
    useAi = true;
    if (toggleAi) toggleAi.checked = true;
  }
  if (urlParams.get("no_llm") === "true" || urlParams.get("deterministic") === "true") {
    useAi = false;
    if (toggleAi) toggleAi.checked = false;
  }
  const noLlm = !useAi;

  const aiNotice = document.getElementById("aiModeNotice");
  const aiTimer = document.getElementById("aiElapsedTimer");
  if (useAi && aiNotice && aiTimer) {
    aiNotice.style.display = "block";
    aiTimer.textContent = "0.0s";
  } else if (aiNotice) {
    aiNotice.style.display = "none";
  }

  const btn = document.getElementById("btnRun");
  btn.disabled = true;
  const btnLabel = useAi ? "AI Investigating (~1m)…" : "Investigating…";
  btn.innerHTML = `
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="animation: spin 1s linear infinite;">
      <circle cx="12" cy="12" r="10"></circle>
      <path d="M12 2a10 10 0 0 1 10 10"></path>
    </svg>
    <span>${btnLabel}</span>
  `;

  const traceList = document.getElementById("traceList");
  traceList.innerHTML = "";

  document.getElementById("verdictBadge").className = "badge badge-insufficient_evidence";
  document.getElementById("verdictBadge").textContent = "ANALYZING GRAPH…";
  document.getElementById("memoText").textContent = "Traversing beneficial ownership and control paths in FalkorDB…";

  const t0 = performance.now();
  let timerInterval = null;
  if (useAi && aiTimer) {
    timerInterval = setInterval(() => {
      const sec = ((performance.now() - t0) / 1000).toFixed(1);
      aiTimer.textContent = `${sec}s`;
    }, 200);
  }

  try {
    const res = await fetch(`${apiBase}/investigate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entity: entityName, watchlist, depth, no_llm: noLlm }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Investigation request failed");
    }

    const { run_id } = await res.json();
    listenToStream(run_id, t0, timerInterval);
  } catch (err) {
    if (timerInterval) clearInterval(timerInterval);
    if (aiNotice) aiNotice.style.display = "none";
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

function listenToStream(runId, startTime, timerInterval = null) {
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
    if (timerInterval) clearInterval(timerInterval);

    const elapsed = ((performance.now() - startTime) / 1000).toFixed(2);
    document.getElementById("investigationTime").textContent = `Elapsed: ${elapsed}s`;

    const aiTimer = document.getElementById("aiElapsedTimer");
    if (aiTimer) aiTimer.textContent = `${elapsed}s`;

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
    if (timerInterval) clearInterval(timerInterval);
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
  if (!evidence) return;
  lastEvidence = evidence;
  if (!cy) return;

  const cyContainer = document.getElementById("cy");
  const isMobile = (cyContainer && cyContainer.clientWidth <= 600) || window.innerWidth <= 600;

  // Set responsive orientation stylesheet
  cy.style(getCyStyles(isMobile));

  const elements = [];
  const addedNodes = new Set();
  const addedEdges = new Set();

  // 1. Identify Primary Evidence Path
  let pathNodes = [];
  let pathRels = [];
  let isWatchlistFound = false;

  if (evidence.paths_to_watchlist && evidence.paths_to_watchlist.length > 0) {
    const wp = evidence.paths_to_watchlist[0];
    pathNodes = wp.nodes || [];
    pathRels = wp.relationships || [];
    isWatchlistFound = true;
  } else if (evidence.ownership_chain && evidence.ownership_chain.length > 0) {
    let bestChain = evidence.ownership_chain[0];
    for (const c of evidence.ownership_chain) {
      if ((c.nodes || []).length > (bestChain.nodes || []).length) {
        bestChain = c;
      }
    }
    pathNodes = bestChain.nodes || [];
    pathRels = bestChain.relationships || [];
  } else if (evidence.resolved_entity) {
    pathNodes = [evidence.resolved_entity];
    pathRels = [];
  }

  const pathNodeIds = new Set(pathNodes.map((n) => String(n.id)));
  const subjectId = String(evidence.resolved_entity?.id || (pathNodes[0] ? pathNodes[0].id : ""));
  const targetId = isWatchlistFound && pathNodes.length > 0 ? String(pathNodes[pathNodes.length - 1].id) : null;

  // 2. Fixed spacing coordinates: Left-to-Right (desktop) or Top-to-Bottom (mobile)
  const desktopSpacing = 220;
  const mobileSpacing = 135;

  pathNodes.forEach((n, idx) => {
    const sId = String(n.id);
    addedNodes.add(sId);
    const isSubject = sId === subjectId;
    const isWatchlistTarget = sId === targetId;

    const baseLabel = formatGraphLabel(n.name || n.address || n.id);
    let displayLabel = baseLabel;
    if (isSubject) {
      displayLabel = `${baseLabel}\n[SUBJECT]`;
    } else if (isWatchlistTarget) {
      displayLabel = `${baseLabel}\n[WATCHLIST (demo)]`;
    }

    const pos = isMobile
      ? { x: 85, y: 70 + idx * mobileSpacing }
      : { x: 100 + idx * desktopSpacing, y: 200 };

    elements.push({
      group: "nodes",
      data: {
        id: sId,
        node_id: n.id,
        name: n.name || n.id,
        label: displayLabel,
        fullLabel: n.name || n.address || n.id,
        type: n.label || n.type || "Entity",
        jurisdiction: n.jurisdiction || "N/A",
        source: n.source || "Panama Papers",
        status: n.status || "Active",
        isSubject,
        isWatchlistTarget,
        isPathNode: true,
      },
      position: pos,
    });
  });

  // 3. Path Edges with Readable Pill Labels
  for (let i = 0; i < pathNodes.length - 1; i++) {
    const srcId = String(pathNodes[i].id);
    const dstId = String(pathNodes[i + 1].id);
    const rel = pathRels[i] || {};
    const relType = rel.type || "OFFICER_OF";
    const edgeKey = `path_${srcId}_${dstId}`;
    addedEdges.add(edgeKey);

    elements.push({
      group: "edges",
      data: {
        id: edgeKey,
        source: srcId,
        target: dstId,
        type: relType,
        label: formatRelLabel(relType),
        isPathEdge: true,
      },
    });
  }

  // 4. Filter Service Providers, Placeholders, Address Hubs & Cap Context Nodes
  let hiddenProvidersCount = 0;
  const rawContextCandidates = [];

  const allCandidatePaths = [
    ...(evidence.ownership_chain || []),
    ...(evidence.shared_links || []).map((l) => ({
      nodes: [
        evidence.resolved_entity,
        { id: l.hub_id, name: l.hub_name, label: l.hub_type || "Intermediary" },
      ],
      relationships: [{ type: "SHARED_HUB" }],
    })),
  ];

  allCandidatePaths.forEach((path) => {
    const nodes = path.nodes || [];
    const rels = path.relationships || [];
    for (let i = 0; i < nodes.length; i++) {
      const node = nodes[i];
      if (!node || !node.id) continue;
      const sId = String(node.id);
      if (pathNodeIds.has(sId)) continue;

      if (isServiceProvider(node.name) || isAddressHub(node)) {
        hiddenProvidersCount++;
      } else {
        const connectedPathNode = (i > 0 && pathNodeIds.has(String(nodes[i - 1].id)))
          ? String(nodes[i - 1].id)
          : (i < nodes.length - 1 && pathNodeIds.has(String(nodes[i + 1].id)))
          ? String(nodes[i + 1].id)
          : subjectId;

        const relType = (i > 0 ? rels[i - 1]?.type : rels[i]?.type) || "CONNECTED_TO";

        rawContextCandidates.push({
          node,
          connectedPathNode,
          relType,
        });
      }
    }
  });

  // Badge for hidden service providers
  const hiddenBadge = document.getElementById("hiddenProvidersBadge");
  if (hiddenBadge) {
    if (hiddenProvidersCount > 0) {
      hiddenBadge.textContent = `${hiddenProvidersCount} more links via service providers (hidden)`;
      hiddenBadge.style.display = "inline-flex";
    } else {
      hiddenBadge.style.display = "none";
    }
  }

  // 5. Context Nodes Toggle (Default Off, Capped at 8, Opacity 0.35, No Labels)
  const showContext = document.getElementById("toggleContext")?.checked || false;
  const cappedContext = rawContextCandidates.slice(0, 8);

  if (showContext) {
    cappedContext.forEach((cand, idx) => {
      const n = cand.node;
      const sId = String(n.id);
      if (addedNodes.has(sId)) return;
      addedNodes.add(sId);

      const parentNode = elements.find((el) => el.group === "nodes" && el.data.id === cand.connectedPathNode);
      const parentPos = parentNode ? parentNode.position : { x: 100, y: 200 };

      const side = idx % 2 === 0 ? 1 : -1;
      const pos = isMobile
        ? { x: parentPos.x + side * 50, y: parentPos.y + (idx % 3 - 1) * 20 }
        : { x: parentPos.x + (idx % 3 - 1) * 25, y: parentPos.y + side * 85 };

      elements.push({
        group: "nodes",
        data: {
          id: sId,
          node_id: n.id,
          name: n.name || n.id,
          label: formatGraphLabel(n.name || n.id),
          fullLabel: n.name || n.id,
          type: n.label || n.type || "Entity",
          jurisdiction: n.jurisdiction || "N/A",
          source: n.source || "Panama Papers",
          status: n.status || "Active",
          isContext: true,
        },
        position: pos,
      });

      const edgeKey = `ctx_${cand.connectedPathNode}_${sId}`;
      if (!addedEdges.has(edgeKey)) {
        addedEdges.add(edgeKey);
        elements.push({
          group: "edges",
          data: {
            id: edgeKey,
            source: cand.connectedPathNode,
            target: sId,
            type: cand.relType,
            label: "",
            isContextEdge: true,
          },
        });
      }
    });
  }

  // 6. Hop-Chain Text Line Above Graph
  const hopChainBanner = document.getElementById("hopChainBanner");
  if (hopChainBanner) {
    if (pathNodes.length > 1) {
      const hopParts = [];
      for (let i = 0; i < pathNodes.length; i++) {
        hopParts.push(`<span class="hop-node">${pathNodes[i].name}</span>`);
        if (i < pathNodes.length - 1) {
          const relText = formatRelLabel(pathRels[i]?.type || "officer of");
          hopParts.push(`<span class="hop-rel">-[${relText}]-&gt;</span>`);
        }
      }
      hopChainBanner.innerHTML = hopParts.join(" ");
      hopChainBanner.style.display = "flex";
    } else {
      hopChainBanner.style.display = "none";
    }
  }

  cy.elements().remove();
  cy.add(elements);
  cy.resize();
  cy.layout({ name: "preset" }).run();
  cy.fit(cy.elements(), 80);
  if (cy.zoom() > 1.15) cy.zoom(1.15);
  cy.center();
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
    alert("Please enter an entity name to compare depth 1 vs 4.");
    return;
  }

  const contrastCard = document.getElementById("contrastCard");
  contrastCard.style.display = "block";

  const d1Badge = document.getElementById("contrastD1Badge");
  const d1Memo = document.getElementById("contrastD1Memo");
  const d4Badge = document.getElementById("contrastD4Badge");
  const d4Memo = document.getElementById("contrastD4Memo");

  d1Badge.innerHTML = `<span class="badge badge-insufficient_evidence">RUNNING DEPTH 1…</span>`;
  d1Memo.textContent = "Executing single-hop neighborhood exploration…";
  d4Badge.innerHTML = `<span class="badge badge-insufficient_evidence">AWAITING…</span>`;
  d4Memo.textContent = "Awaiting depth 1 completion before starting multi-hop traversal…";

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

    d1Badge.innerHTML = `<span class="badge badge-clear">NO INDICATORS FOUND WITHIN DEPTH 1</span>`;
    d1Memo.textContent = "No indicators found within depth 1. Subject appears clean under shallow relational review.";

    // Render Depth 1 comparison graph in #cyD1
    renderMiniCompareGraph("cyD1", r1Data.evidence, true);

    // Run Depth 4
    d4Badge.innerHTML = `<span class="badge badge-insufficient_evidence">RUNNING DEPTH 4…</span>`;
    d4Memo.textContent = "Traversing 4 hops across corporate directorship chains in FalkorDB…";

    const res4 = await fetch(`${apiBase}/investigate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entity: entityName, watchlist, depth: 4, no_llm: true }),
    });
    const run4 = await res4.json();
    const r4Data = await awaitRunComplete(run4.run_id);

    d4Badge.innerHTML = `<span class="badge badge-${r4Data.verdict}">${r4Data.verdict.toUpperCase()}</span>`;
    d4Memo.textContent = r4Data.memo || "Depth 4 completed.";

    // Render Depth 4 comparison graph in #cyD4
    renderMiniCompareGraph("cyD4", r4Data.evidence, false);

    // Update main graph with Depth 4 view
    renderGraph(r4Data.evidence);
    updateVerdictUI(r4Data.verdict, r4Data.evaluation);
    document.getElementById("memoText").textContent = r4Data.memo;
    document.getElementById("memoSource").textContent = "Source: DEPTH COMPARISON ENGINE";
  } catch (err) {
    alert(`Comparison failed: ${err.message}`);
  }
}

function renderMiniCompareGraph(containerId, evidence, isDepth1) {
  const container = document.getElementById(containerId);
  if (!container || !evidence) return;

  const isMobile = container.clientWidth <= 600 || window.innerWidth <= 600;
  const elements = [];

  if (isDepth1) {
    const subject = evidence.resolved_entity;
    if (subject) {
      elements.push({
        group: "nodes",
        data: {
          id: String(subject.id),
          label: `${formatGraphLabel(subject.name)}\n[SUBJECT]`,
          isSubject: true,
          type: "Entity",
        },
        position: isMobile ? { x: 85, y: 70 } : { x: 120, y: 140 },
      });

      let ctxCount = 0;
      (evidence.ownership_chain || []).forEach((chain) => {
        const nodes = chain.nodes || [];
        if (nodes.length > 1 && ctxCount < 3) {
          const neighbor = nodes[1];
          if (!isServiceProvider(neighbor.name) && !isAddressHub(neighbor)) {
            const nId = String(neighbor.id);
            ctxCount++;
            const pos = isMobile
              ? { x: 85, y: 70 + ctxCount * 80 }
              : { x: 120 + ctxCount * 130, y: 140 };
            elements.push({
              group: "nodes",
              data: {
                id: nId,
                label: formatGraphLabel(neighbor.name),
                type: neighbor.label || "Officer",
                isContext: true,
              },
              position: pos,
            });
            elements.push({
              group: "edges",
              data: {
                id: `e_${subject.id}_${nId}`,
                source: String(subject.id),
                target: nId,
                label: "",
              },
            });
          }
        }
      });
    }
  } else {
    let pathNodes = [];
    let pathRels = [];
    if (evidence.paths_to_watchlist && evidence.paths_to_watchlist.length > 0) {
      pathNodes = evidence.paths_to_watchlist[0].nodes || [];
      pathRels = evidence.paths_to_watchlist[0].relationships || [];
    }
    const targetId = pathNodes.length > 0 ? String(pathNodes[pathNodes.length - 1].id) : null;
    const subjectId = String(evidence.resolved_entity?.id || (pathNodes[0]?.id));

    const spacing = isMobile ? 80 : 130;
    pathNodes.forEach((n, idx) => {
      const sId = String(n.id);
      const isSub = sId === subjectId;
      const isTgt = sId === targetId;
      let lbl = formatGraphLabel(n.name);
      if (isSub) lbl += "\n[SUBJECT]";
      if (isTgt) lbl += "\n[WATCHLIST (demo)]";

      elements.push({
        group: "nodes",
        data: {
          id: sId,
          label: lbl,
          type: n.label || "Entity",
          isSubject: isSub,
          isWatchlistTarget: isTgt,
          isPathNode: true,
        },
        position: isMobile
          ? { x: 85, y: 50 + idx * spacing }
          : { x: 70 + idx * spacing, y: 140 },
      });
    });

    for (let i = 0; i < pathNodes.length - 1; i++) {
      elements.push({
        group: "edges",
        data: {
          id: `pe_${pathNodes[i].id}_${pathNodes[i + 1].id}`,
          source: String(pathNodes[i].id),
          target: String(pathNodes[i + 1].id),
          label: formatRelLabel(pathRels[i]?.type || "officer of"),
          isPathEdge: true,
        },
      });
    }
  }

  const miniCy = cytoscape({
    container,
    elements,
    style: getCyStyles(isMobile),
    layout: { name: "preset" },
  });
  miniCy.fit(miniCy.elements(), 45);
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
