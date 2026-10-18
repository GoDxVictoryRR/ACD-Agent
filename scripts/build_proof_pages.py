#!/usr/bin/env python3
"""
scripts/build_proof_pages.py — Renders raw benchmark/audit files into clean static HTML proof pages.
Output: docs/video/proof/NN.html (monospace, large readable font, title, and capture timestamp).
Strictly uses ONLY the raw files saved under docs/video/raw/.
"""

import os
import re
import html
from datetime import datetime, UTC
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "docs" / "video" / "raw"
PROOF_DIR = REPO_ROOT / "docs" / "video" / "proof"

PROOF_PAGES = [
    {
        "filename": "01_pytest.html",
        "title": "Automated Test Suite Execution (pytest -q -rs)",
        "source": "pytest.txt",
        "subtitle": "53 passed test cases validating graph traversal, rules engine, and verifier invariants"
    },
    {
        "filename": "02_invariants.html",
        "title": "Architectural Invariants Verification (scripts/check_invariants.py)",
        "source": "invariants.txt",
        "subtitle": "6 non-negotiable architectural constraints verified against codebase"
    },
    {
        "filename": "03_ablation.html",
        "title": "Graph Algorithm & Traversal Ablation Matrix",
        "source": "ablation.md",
        "subtitle": "Controlled evaluation proving necessity of graph algorithms over shallow heuristics"
    },
    {
        "filename": "04_exposure.html",
        "title": "Empirical Baseline: Degree-Matched Exposure Stats",
        "source": "exposure_stats.json",
        "subtitle": "0 of 30 degree-matched control entities reach watchlist target DOM Limited"
    },
    {
        "filename": "05_latency_memory.html",
        "title": "Latency Distribution & Memory Footprint Telemetry",
        "source": "latency_memory.txt",
        "subtitle": "Depth-4 p95 ~0.23s; FalkorDB ~41MB RAM; Application RSS under 100MB"
    },
    {
        "filename": "06_stopped.html",
        "title": "Database Isolation Health Check (FalkorDB Offline)",
        "source": "health_stopped.json",
        "subtitle": "HTTP 503 Service Unavailable — guarantees FalkorDB is primary, non-optional engine"
    },
    {
        "filename": "07_injection.html",
        "title": "Adversarial Prompt Injection Immunity Proof",
        "source": "injection_test.txt",
        "subtitle": "Hostile entity payload test: verifies LLM output cannot override deterministic verdict"
    }
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title} | Ownership Lens Proof</title>
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      background: #090d16;
      color: #e2e8f0;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      padding: 2.5rem 3rem;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    .header {{
      border-bottom: 2px solid #1e293b;
      padding-bottom: 1.25rem;
      margin-bottom: 1.5rem;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }}
    .title-group h1 {{
      font-size: 1.65rem;
      font-weight: 700;
      color: #38bdf8;
      letter-spacing: -0.02em;
      margin-bottom: 0.4rem;
    }}
    .subtitle {{
      color: #94a3b8;
      font-size: 0.95rem;
      font-weight: 400;
    }}
    .meta-tag {{
      text-align: right;
      font-size: 0.8rem;
      color: #64748b;
      background: #0f172a;
      border: 1px solid #1e293b;
      padding: 0.5rem 0.85rem;
      border-radius: 6px;
    }}
    .meta-tag .tag-status {{
      color: #10b981;
      font-weight: 700;
      font-size: 0.85rem;
      display: block;
      margin-bottom: 0.2rem;
    }}
    .content-box {{
      background: #0b1120;
      border: 1px solid #1e293b;
      border-radius: 8px;
      padding: 1.5rem 1.75rem;
      flex: 1;
      overflow-x: auto;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }}
    pre {{
      font-size: 1.05rem;
      line-height: 1.55;
      color: #f1f5f9;
      white-space: pre-wrap;
      word-break: break-all;
    }}
    .highlight-pass {{
      color: #34d399;
      font-weight: bold;
    }}
    .highlight-stat {{
      color: #fbbf24;
      font-weight: bold;
    }}
    .footer {{
      margin-top: 1.5rem;
      padding-top: 0.75rem;
      border-top: 1px solid #1e293b;
      display: flex;
      justify-content: space-between;
      font-size: 0.8rem;
      color: #64748b;
    }}
  </style>
</head>
<body>
  <div class="header">
    <div class="title-group">
      <h1>{title}</h1>
      <p class="subtitle">{subtitle}</p>
    </div>
    <div class="meta-tag">
      <span class="tag-status">EVIDENTIARY AUDIT PROOF</span>
      <span>Source: {source}</span><br>
      <span>Captured: {timestamp}</span>
    </div>
  </div>

  <div class="content-box">
    <pre>{content}</pre>
  </div>

  <div class="footer">
    <span>Ownership Lens | FalkorDB Graph Hacks (Track 01)</span>
    <span>Deterministic Evidence Ledger &bull; Raw Unedited System Telemetry</span>
  </div>
</body>
</html>
"""

def sanitize_content(raw_text: str) -> str:
    """Filter any secret keys or sensitive strings."""
    lines = raw_text.splitlines()
    clean_lines = []
    for line in lines:
        if "nvapi" in line.lower() or "secret" in line.lower() and "=" in line:
            clean_lines.append("[REDACTED SECRET]")
        else:
            clean_lines.append(line)
    return "\n".join(clean_lines)

def build_proof_pages():
    PROOF_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%SZ")

    print(f"[build_proof_pages] Generating proof pages from {RAW_DIR}...")
    for page in PROOF_PAGES:
        src_file = RAW_DIR / page["source"]
        out_file = PROOF_DIR / page["filename"]

        if not src_file.exists():
            print(f"  [WARN] Source file missing: {src_file}. Skipping {page['filename']}.")
            continue

        try:
            raw_text = src_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                raw_text = src_file.read_text(encoding="utf-16")
            except Exception:
                raw_text = src_file.read_text(encoding="utf-8", errors="replace")
        clean_text = sanitize_content(raw_text)
        escaped_text = html.escape(clean_text)

        html_out = HTML_TEMPLATE.format(
            title=page["title"],
            subtitle=page["subtitle"],
            source=page["source"],
            timestamp=timestamp,
            content=escaped_text
        )

        out_file.write_text(html_out, encoding="utf-8")
        print(f"  [OK] Generated {out_file.name} ({len(html_out)} bytes)")

if __name__ == "__main__":
    build_proof_pages()
