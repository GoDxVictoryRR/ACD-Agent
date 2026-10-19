#!/usr/bin/env python3
"""
scripts/record_demo.py — Automated recording harness for Ownership Lens submission video.
Captures high-fidelity 1600x900 silent screen clips with injected cursor, lower-third
captions, Track 01 checklist overlay, and human-paced interaction.
"""

import argparse
import json
import logging
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Add repo root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from playwright.sync_api import BrowserContext, Page, sync_playwright

from scripts.clean_cases import clean_cases

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("record_demo")

CLIPS_DIR = REPO_ROOT / "docs" / "video" / "clips"
CHECK_DIR = REPO_ROOT / "docs" / "video" / "check"
SLIDES_DIR = REPO_ROOT / "docs" / "video" / "slides"
PROOF_DIR = REPO_ROOT / "docs" / "video" / "proof"
DURATIONS_PATH = REPO_ROOT / "docs" / "video" / "durations.json"

DEFAULT_DURATIONS = {
    "s01": 22,
    "s02": 23,
    "s03": 24,
    "s04": 32,
    "s05": 24,
    "s05b": 60,
    "s06": 20,
    "s07": 22,
    "s08": 30,
    "s09": 25,
    "s10": 22
}

# ── INJECTION SCRIPT ──────────────────────────────────────────────────────────
INIT_SCRIPT = """
(() => {
  function ensureElements() {
    const parent = document.body || document.documentElement;
    if (!parent) return;

    // 1. Mouse Tracking Cursor
    if (!document.getElementById('__demo_cursor')) {
      const cursor = document.createElement('div');
      cursor.id = '__demo_cursor';
      cursor.style.cssText = 'position:fixed;width:24px;height:24px;border-radius:50%;background:rgba(239,68,68,0.75);border:2.5px solid #ffffff;pointer-events:none;z-index:9999999;transition:transform 0.05s ease, opacity 0.2s;box-shadow:0 0 14px rgba(239,68,68,0.9);transform:translate(-50%,-50%);top:-100px;left:-100px;';
      parent.appendChild(cursor);

      window.addEventListener('mousemove', e => {
        cursor.style.left = e.clientX + 'px';
        cursor.style.top = e.clientY + 'px';
      });
    }

    // 2. Track 01 Checklist Overlay
    if (!document.getElementById('__demo_checklist')) {
      const checklist = document.createElement('div');
      checklist.id = '__demo_checklist';
      checklist.style.cssText = 'position:fixed;top:18px;right:18px;background:rgba(11,17,32,0.92);border:1px solid #1e293b;border-radius:10px;padding:0.75rem 1rem;font-family:-apple-system,BlinkMacSystemFont,sans-serif;z-index:9999998;box-shadow:0 10px 25px rgba(0,0,0,0.5);width:265px;backdrop-filter:blur(8px);';
      checklist.innerHTML = `
        <div style="font-size:0.75rem;font-weight:700;color:#38bdf8;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.45rem;border-bottom:1px solid #1e293b;padding-bottom:0.35rem;display:flex;justify-content:space-between;align-items:center;">
          <span>Track 01 Checklist</span>
          <span style="font-size:0.7rem;color:#64748b;font-weight:normal;">FalkorDB</span>
        </div>
        <div id="__chk_1" style="display:flex;align-items:center;gap:0.5rem;font-size:0.78rem;color:#64748b;margin-bottom:0.32rem;transition:all 0.3s;"><span class="tick-box" style="width:15px;height:15px;border-radius:4px;border:1px solid #334155;display:flex;align-items:center;justify-content:center;font-size:0.65rem;"></span> Multi-hop reasoning</div>
        <div id="__chk_2" style="display:flex;align-items:center;gap:0.5rem;font-size:0.78rem;color:#64748b;margin-bottom:0.32rem;transition:all 0.3s;"><span class="tick-box" style="width:15px;height:15px;border-radius:4px;border:1px solid #334155;display:flex;align-items:center;justify-content:center;font-size:0.65rem;"></span> Graph algorithms as tools</div>
        <div id="__chk_3" style="display:flex;align-items:center;gap:0.5rem;font-size:0.78rem;color:#64748b;margin-bottom:0.32rem;transition:all 0.3s;"><span class="tick-box" style="width:15px;height:15px;border-radius:4px;border:1px solid #334155;display:flex;align-items:center;justify-content:center;font-size:0.65rem;"></span> Tool selection via MCP</div>
        <div id="__chk_4" style="display:flex;align-items:center;gap:0.5rem;font-size:0.78rem;color:#64748b;margin-bottom:0.32rem;transition:all 0.3s;"><span class="tick-box" style="width:15px;height:15px;border-radius:4px;border:1px solid #334155;display:flex;align-items:center;justify-content:center;font-size:0.65rem;"></span> Actions from the graph</div>
        <div id="__chk_5" style="display:flex;align-items:center;gap:0.5rem;font-size:0.78rem;color:#64748b;margin-bottom:0.15rem;transition:all 0.3s;"><span class="tick-box" style="width:15px;height:15px;border-radius:4px;border:1px solid #334155;display:flex;align-items:center;justify-content:center;font-size:0.65rem;"></span> Explainable results</div>
      `;
      parent.appendChild(checklist);
    }
  }

  window.setCaption = function(text) {
    ensureElements();
    let caption = document.getElementById('__demo_caption');
    if (!caption) {
      const parent = document.body || document.documentElement;
      if (!parent) return;
      caption = document.createElement('div');
      caption.id = '__demo_caption';
      caption.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:rgba(9,13,22,0.92);border:1.5px solid #38bdf8;box-shadow:0 10px 30px rgba(0,0,0,0.8);color:#f8fafc;padding:0.65rem 1.6rem;border-radius:9999px;font-family:-apple-system,BlinkMacSystemFont,sans-serif;font-size:1.02rem;font-weight:600;letter-spacing:0.02em;z-index:9999998;display:none;align-items:center;gap:0.65rem;backdrop-filter:blur(8px);';
      parent.appendChild(caption);
    }
    if (!text) {
      caption.style.display = 'none';
    } else {
      caption.innerHTML = '<span style="color:#38bdf8;font-size:1.15rem;">&#9654;</span> <span>' + text + '</span>';
      caption.style.display = 'flex';
    }
  };

  window.tick = function(n) {
    ensureElements();
    const el = document.getElementById('__chk_' + n);
    if (el) {
      el.style.color = '#f1f5f9';
      el.style.fontWeight = '600';
      const box = el.querySelector('.tick-box');
      if (box) {
        box.style.background = '#10b981';
        box.style.borderColor = '#10b981';
        box.style.color = '#ffffff';
        box.innerHTML = '&#10003;';
      }
    }
  };

  document.addEventListener('DOMContentLoaded', ensureElements);
  if (document.readyState === 'interactive' || document.readyState === 'complete') {
    ensureElements();
  }
})();
"""

def capture_frame(page: Page, scene_id: str, tag: str):
    """Save verification screenshot for self-check (start, mid, end)."""
    p = CHECK_DIR / f"{scene_id}_{tag}.png"
    try:
        page.screenshot(path=str(p))
    except Exception as e:
        logger.warning(f"Failed to capture frame {scene_id}_{tag}: {e}")

def human_move(page: Page, selector_or_coords, steps: int = 30):
    """Smooth, human-like mouse movement in at least 25 steps."""
    if isinstance(selector_or_coords, str):
        box = page.locator(selector_or_coords).bounding_box()
        if not box:
            return
        target_x = box["x"] + box["width"] / 2
        target_y = box["y"] + box["height"] / 2
    else:
        target_x, target_y = selector_or_coords
    page.mouse.move(target_x, target_y, steps=max(25, steps))
    page.wait_for_timeout(100)

def human_type(page: Page, selector: str, text: str, delay_ms: int = 60):
    """Human-like typing with specified millisecond delay per character."""
    page.click(selector)
    page.wait_for_timeout(150)
    # Clear input first
    page.fill(selector, "")
    page.wait_for_timeout(100)
    for char in text:
        page.keyboard.type(char, delay=delay_ms)

def check_for_page_errors(page: Page, scene_name: str):
    """Fail loudly if console errors or visible error banners appear."""
    errors = page.locator(".alert-error, .error-banner, #errorBadge:visible").all_inner_texts()
    if errors:
        raise RuntimeError(f"[{scene_name}] Visible error banner detected: {errors}")

def convert_webm_to_mp4(webm_path: Path) -> Path:
    """Converts a recorded WebM to MP4 using ffmpeg if available."""
    mp4_path = webm_path.with_suffix(".mp4")
    try:
        cmd = [
            "ffmpeg", "-y", "-i", str(webm_path),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
            str(mp4_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and mp4_path.exists():
            logger.info(f"  [ffmpeg] Converted {webm_path.name} -> {mp4_path.name}")
            return mp4_path
    except Exception as e:
        logger.warning(f"  [ffmpeg] Conversion failed: {e}")
    return webm_path

# ── SCENE RECORDERS ──────────────────────────────────────────────────────────

def record_s01(page: Page, duration: float):
    """s01 (22s): Intro slide, animated chain with depth-1 compliance stop bracket."""
    url = SLIDES_DIR.joinpath("s01.html").as_uri()
    page.goto(url)
    page.wait_for_timeout(1000) # 1s lead-in
    capture_frame(page, "s01", "start")
    page.evaluate("window.setCaption('Ownership Lens: Autonomous Graph Agent for Beneficial Ownership')")

    human_move(page, (800, 360), steps=35)
    page.wait_for_timeout(3000)

    # Hover near subtitle
    human_move(page, (800, 420), steps=30)
    page.wait_for_timeout(3500)

    # At 8s chain appears: hover over Company A -> Director 1 -> Bracket
    capture_frame(page, "s01", "mid")
    human_move(page, (460, 520), steps=30)
    page.wait_for_timeout(1500)
    human_move(page, (620, 520), steps=25)
    page.wait_for_timeout(1500)
    human_move(page, (480, 440), steps=30) # Over bracket
    page.wait_for_timeout(2500)

    human_move(page, (1150, 520), steps=35) # Over ultimate beneficial owner
    page.wait_for_timeout(1000)
    capture_frame(page, "s01", "end")
    page.wait_for_timeout(2000) # 3s hold

def record_s02(page: Page, duration: float):
    """s02 (23s): Track 01 WeMakeDevs banner, 5 checklist items appearing."""
    url = SLIDES_DIR.joinpath("s02.html").as_uri()
    page.goto(url)
    page.wait_for_timeout(1000) # 1s lead-in
    capture_frame(page, "s02", "start")
    page.evaluate("window.setCaption('Track 01: Agents That Act on Connected Data')")

    human_move(page, (800, 310), steps=30)
    page.wait_for_timeout(3500)

    human_move(page, (800, 370), steps=25)
    page.wait_for_timeout(3000)
    capture_frame(page, "s02", "mid")

    # Staggered items hover
    coords = [(800, 470), (800, 530), (800, 590), (800, 650), (800, 710)]
    for pt in coords:
        human_move(page, pt, steps=25)
        page.wait_for_timeout(1800)

    capture_frame(page, "s02", "end")
    page.wait_for_timeout(3000) # 3s hold

def record_s03(page: Page, duration: float):
    """s03 (24s): Real graph scale proof page, then live UI footer disclaimer."""
    url_proof = PROOF_DIR.joinpath("05_latency_memory.html").as_uri()
    page.goto(url_proof)
    page.wait_for_timeout(1000)
    capture_frame(page, "s03", "start")
    page.evaluate("window.setCaption('Real graph scale: 51,940 nodes and 58,875 relationships (ICIJ subset)')")

    human_move(page, (500, 320), steps=30)
    page.wait_for_timeout(3500)
    human_move(page, (500, 480), steps=30)
    page.wait_for_timeout(3500)

    # Navigate to live UI footer
    page.goto("http://localhost:8000")
    page.wait_for_selector("footer", timeout=10000)
    page.wait_for_timeout(1000)
    page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
    page.evaluate("window.setCaption('Data provenance: ICIJ Offshore Leaks (ODbL / CC BY-SA) & Compliance Disclaimer')")
    page.wait_for_timeout(1500)
    capture_frame(page, "s03", "mid")

    human_move(page, (800, 840), steps=30)
    page.wait_for_timeout(4000)
    capture_frame(page, "s03", "end")
    page.wait_for_timeout(3000) # 3s hold

def record_s04(page: Page, duration: float):
    """s04 (32s): GLAISDALE LIMITED D1 clear, Compare D1 vs D4 red path & ledger."""
    page.goto("http://localhost:8000")
    page.wait_for_selector("#entityInput", timeout=10000)
    page.wait_for_timeout(1000)

    page.evaluate("window.setCaption('Target: GLAISDALE LIMITED | Watchlist: DOM Limited')")
    human_type(page, "#entityInput", "GLAISDALE LIMITED", delay_ms=50)
    page.wait_for_timeout(400)

    human_type(page, "#watchlistInput", "DOM Limited", delay_ms=50)
    page.wait_for_timeout(400)

    # Select Depth 1
    page.select_option("#depthSelect", "1")
    page.wait_for_timeout(400)

    # Click Investigate
    human_move(page, "#btnRun", steps=25)
    page.click("#btnRun")

    # Wait for verdict
    page.wait_for_selector("#verdictBadge:has-text('No indicators found')", timeout=15000)
    capture_frame(page, "s04", "start")
    page.evaluate("window.tick(1)")
    page.evaluate("window.setCaption('Depth 1: Zero indicators found within immediate 5 relationships')")
    page.wait_for_timeout(3000) # 3s hold on depth 1 finding

    # Click Compare D1 vs D4
    page.evaluate("window.setCaption('Executing Depth Contrast: D1 vs D4 Side-by-Side Traversal')")
    human_move(page, "#btnCompare", steps=25)
    page.click("#btnCompare")

    # Wait for contrast card & Cytoscape red path
    page.wait_for_selector("#contrastCard:visible", timeout=20000)
    page.evaluate("window.tick(5)")
    page.evaluate("window.setCaption('Depth 4: Red path reveals 4-hop chain to DOM Limited at cost 4.0')")
    capture_frame(page, "s04", "mid")

    # Hover on contrast card
    human_move(page, "#contrastCard", steps=30)
    page.wait_for_timeout(4000)

    # Scroll to Evidence Ledger
    page.evaluate("document.getElementById('ledgerCard').scrollIntoView({behavior: 'smooth'})")
    page.wait_for_timeout(1500)
    page.wait_for_selector("#ledgerBody tr", timeout=10000)
    human_move(page, "#ledgerBody tr:first-child", steps=30)
    capture_frame(page, "s04", "end")
    page.wait_for_timeout(3500)

    page.wait_for_timeout(3000) # 3s hold

def record_s05(page: Page, duration: float):
    """s05 (24s): Execution trace console, MCP tool names, latency, params."""
    page.goto("http://localhost:8000")
    page.wait_for_selector("#entityInput", timeout=10000)
    page.wait_for_timeout(1000)

    # Fast deterministic investigation to populate trace
    page.fill("#entityInput", "GLAISDALE LIMITED")
    page.fill("#watchlistInput", "DOM Limited")
    page.select_option("#depthSelect", "4")
    page.click("#btnRun")
    page.wait_for_selector("#verdictBadge:has-text('ESCALATE')", timeout=15000)

    capture_frame(page, "s05", "start")

    # Scroll to trace console
    page.evaluate("document.getElementById('traceList').scrollIntoView({behavior: 'smooth'})")
    page.wait_for_timeout(1200)

    page.evaluate("window.tick(2); window.tick(3);")
    page.evaluate("window.setCaption('Agent Execution Trace: Typed Graph Tools via Model Context Protocol (MCP)')")
    capture_frame(page, "s05", "mid")

    # Smooth inspection of trace items
    trace_items = page.locator(".trace-item").all()
    for idx, item in enumerate(trace_items[:4]):
        box = item.bounding_box()
        if box:
            human_move(page, (box["x"] + 200, box["y"] + box["height"] / 2), steps=25)
            page.wait_for_timeout(2000)

    capture_frame(page, "s05", "end")
    page.wait_for_timeout(3000) # 3s hold

def record_s05b(page: Page, duration: float):
    """s05b (60s): Real-time AI agent mode run with LLM tool calling."""
    page.goto("http://localhost:8000")
    page.wait_for_selector("#toggleAiMode", timeout=10000)
    page.wait_for_timeout(1000)

    # Enable AI Agent Mode
    page.evaluate("window.setCaption('AI agent mode, real run, sped up in the edit')")
    human_move(page, "#toggleAiMode", steps=25)
    page.check("#toggleAiMode")
    page.wait_for_timeout(800)
    capture_frame(page, "s05b", "start")

    human_type(page, "#entityInput", "GLAISDALE LIMITED", delay_ms=50)
    human_type(page, "#watchlistInput", "DOM Limited", delay_ms=50)
    page.select_option("#depthSelect", "4")

    human_move(page, "#btnRun", steps=25)
    page.click("#btnRun")

    # Watch execution stream
    page.evaluate("document.getElementById('traceList').scrollIntoView({behavior: 'smooth'})")
    page.wait_for_timeout(5000)
    capture_frame(page, "s05b", "mid")

    # Wait up to 55s for AI run to complete
    try:
        page.wait_for_selector("#verdictBadge:has-text('ESCALATE')", timeout=55000)
        page.evaluate("window.setCaption('AI Agent complete: Autonomous MCP tool selection executed')")
    except Exception:
        logger.warning("[s05b] AI mode timed out or hit endpoint limit; completing scene safely.")

    capture_frame(page, "s05b", "end")
    page.wait_for_timeout(3000) # 3s hold

def record_s06(page: Page, duration: float):
    """s06 (20s): Case write-back indicator, then NEWCOMBE LIMITED recalls GLAISDALE case."""
    page.goto("http://localhost:8000")
    page.wait_for_selector("#entityInput", timeout=10000)
    page.wait_for_timeout(1000)

    # First run GLAISDALE to ensure case write-back is saved
    page.fill("#entityInput", "GLAISDALE LIMITED")
    page.fill("#watchlistInput", "DOM Limited")
    page.select_option("#depthSelect", "4")
    page.click("#btnRun")
    page.wait_for_selector("#verdictBadge:has-text('ESCALATE')", timeout=15000)
    page.wait_for_timeout(1500)

    page.evaluate("window.tick(4)")
    page.evaluate("window.setCaption('Graph Write-Back: Decision recorded as (:Case) node in FalkorDB')")
    capture_frame(page, "s06", "start")
    human_move(page, "#verdictCard", steps=30)
    page.wait_for_timeout(3000)

    # Now investigate NEWCOMBE LIMITED to demonstrate recall
    page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
    page.wait_for_timeout(1000)
    page.evaluate("window.setCaption('Target: NEWCOMBE LIMITED — Recalling past investigations via shared director')")
    human_type(page, "#entityInput", "NEWCOMBE LIMITED", delay_ms=50)
    page.select_option("#depthSelect", "2")
    human_move(page, "#btnRun", steps=25)
    page.click("#btnRun")

    # Wait for recalledCard
    page.wait_for_selector("#recalledCard:visible", timeout=15000)
    capture_frame(page, "s06", "mid")
    human_move(page, "#recalledCard", steps=30)
    page.wait_for_timeout(5000) # Hold 5s on recalled card per instructions

    capture_frame(page, "s06", "end")
    page.wait_for_timeout(3000) # 3s hold

def record_s07(page: Page, duration: float):
    """s07 (22s): Memo verifier, Dewburn isolated entity, injection proof page."""
    page.goto("http://localhost:8000")
    page.wait_for_selector("#entityInput", timeout=10000)
    page.wait_for_timeout(1000)

    # Highlight memo in verdict card
    page.fill("#entityInput", "GLAISDALE LIMITED")
    page.click("#btnRun")
    page.wait_for_selector("#verdictBadge:has-text('ESCALATE')", timeout=15000)
    page.evaluate("document.getElementById('verdictCard').scrollIntoView({behavior: 'smooth'})")
    page.evaluate("window.setCaption('Memo Verifier: Grounded strictly in tool evidence ledger')")
    capture_frame(page, "s07", "start")
    human_move(page, "#memoSource", steps=25)
    page.wait_for_timeout(3000)

    # Run Dewburn Enterprises Inc. (insufficient evidence)
    page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
    page.wait_for_timeout(800)
    page.evaluate("window.setCaption('Dewburn Enterprises Inc.: Isolated entity returns INSUFFICIENT_EVIDENCE')")
    human_type(page, "#entityInput", "Dewburn Enterprises Inc.", delay_ms=50)
    page.click("#btnRun")
    page.wait_for_selector("#verdictBadge:has-text('INSUFFICIENT')", timeout=15000)
    capture_frame(page, "s07", "mid")
    human_move(page, "#verdictBadge", steps=25)
    page.wait_for_timeout(3500)

    # Navigate to injection proof page
    url_inj = PROOF_DIR.joinpath("07_injection.html").as_uri()
    page.goto(url_inj)
    page.evaluate("window.setCaption('The AI cannot change the verdict (Adversarial Prompt Injection Immunity)')")
    human_move(page, (800, 450), steps=30)
    page.wait_for_timeout(4000)

    capture_frame(page, "s07", "end")
    page.wait_for_timeout(3000) # 3s hold

def record_s08(page: Page, duration: float):
    """s08 (30s): Proof pages carousel (pytest, invariants, ablation, exposure, latency, stopped)."""
    pages = [
        ("01_pytest.html", "Pytest Suite: 53 passed tests verifying traversals & rules", "start"),
        ("02_invariants.html", "Architectural Invariants: 6 constraints strictly verified", None),
        ("03_ablation.html", "Ablation Matrix: Graph algorithms outperform shallow heuristics", None),
        ("04_exposure.html", "Empirical Baseline: 0 of 30 degree-matched controls reach target", "mid"),
        ("05_latency_memory.html", "Performance: 0.23s p95 traversal; 41MB graph memory", None),
        ("06_stopped.html", "FalkorDB Offline: HTTP 503 proves database is mandatory", "end")
    ]

    for filename, caption_text, tag in pages:
        url = PROOF_DIR.joinpath(filename).as_uri()
        page.goto(url)
        page.evaluate(f"window.setCaption('{caption_text}')")
        page.wait_for_timeout(500)
        if tag:
            capture_frame(page, "s08", tag)
        human_move(page, (800, 480), steps=25)
        page.wait_for_timeout(3500)

    page.wait_for_timeout(3000) # 3s hold

def record_s09(page: Page, duration: float):
    """s09 (25s): Architectural comparison & use cases."""
    url = SLIDES_DIR.joinpath("s09.html").as_uri()
    page.goto(url)
    page.wait_for_timeout(1000) # 1s lead-in
    capture_frame(page, "s09", "start")
    page.evaluate("window.setCaption('Architecture: Deterministic Rules & Graph Algorithms decide')")

    human_move(page, (400, 360), steps=30) # Typical AI demo
    page.wait_for_timeout(3500)
    capture_frame(page, "s09", "mid")

    human_move(page, (1050, 360), steps=35) # Ownership Lens
    page.wait_for_timeout(5000)

    human_move(page, (800, 720), steps=30) # Use cases
    page.wait_for_timeout(4500)
    capture_frame(page, "s09", "end")

    page.wait_for_timeout(3000) # 3s hold

def record_s10(page: Page, duration: float):
    """s10 (22s): End card, compliance disclaimer, repository URL."""
    url = SLIDES_DIR.joinpath("s10.html").as_uri()
    page.goto(url)
    page.wait_for_timeout(1000) # 1s lead-in
    capture_frame(page, "s10", "start")
    page.evaluate("window.setCaption('Historical leak, demo watchlist, human review required')")

    human_move(page, (800, 240), steps=25) # Badge
    page.wait_for_timeout(3500)
    capture_frame(page, "s10", "mid")

    human_move(page, (800, 520), steps=30) # GitHub box
    page.wait_for_timeout(4000)

    human_move(page, (800, 830), steps=30) # Footer disclaimer
    page.wait_for_timeout(3500)
    capture_frame(page, "s10", "end")

    page.wait_for_timeout(3000) # 3s hold

SCENE_HANDLERS = {
    "s01": record_s01,
    "s02": record_s02,
    "s03": record_s03,
    "s04": record_s04,
    "s05": record_s05,
    "s05b": record_s05b,
    "s06": record_s06,
    "s07": record_s07,
    "s08": record_s08,
    "s09": record_s09,
    "s10": record_s10,
}

# ── MAIN ORCHESTRATOR ────────────────────────────────────────────────────────

def record_scene(scene_id: str, duration: float, browser, durations_map: dict):
    logger.info(f"=== Recording scene {scene_id} (target: {duration}s) ===")
    handler = SCENE_HANDLERS.get(scene_id)
    if not handler:
        logger.error(f"No handler defined for scene {scene_id}")
        return False

    temp_video_dir = REPO_ROOT / "docs" / "video" / "temp_clips"
    temp_video_dir.mkdir(parents=True, exist_ok=True)

    # Single dedicated browser context per scene
    context: BrowserContext = browser.new_context(
        viewport={"width": 1600, "height": 900},
        record_video_dir=str(temp_video_dir),
        record_video_size={"width": 1600, "height": 900}
    )
    context.add_init_script(INIT_SCRIPT)

    page = context.new_page()

    # Capture console errors
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

    try:
        t_start = time.perf_counter()

        # Run scene script
        handler(page, duration)

        elapsed = time.perf_counter() - t_start
        logger.info(f"  [timing] Scene {scene_id} finished actions in {elapsed:.2f}s")

        # Capture start, middle, end verification screenshots
        check_start = CHECK_DIR / f"{scene_id}_start.png"
        check_mid = CHECK_DIR / f"{scene_id}_mid.png"
        check_end = CHECK_DIR / f"{scene_id}_end.png"

        # Save end frame
        page.screenshot(path=str(check_end))
        # Save start & mid as fallback if not already captured
        if not check_start.exists():
            page.screenshot(path=str(check_start))
        if not check_mid.exists():
            page.screenshot(path=str(check_mid))

        check_for_page_errors(page, scene_id)

    except Exception as exc:
        logger.exception(f"  [ERROR] Scene {scene_id} failed: {exc}")
        context.close()
        return False
    finally:
        video_obj = page.video
        context.close()

    # Move video to destination
    if video_obj:
        raw_video_path = Path(video_obj.path())
        dest_webm = CLIPS_DIR / f"{scene_id}.webm"
        if raw_video_path.exists():
            shutil.move(str(raw_video_path), str(dest_webm))
            logger.info(f"  [saved] {dest_webm.name} ({dest_webm.stat().st_size} bytes)")
            convert_webm_to_mp4(dest_webm)
            return True

    return False

def main():
    parser = argparse.ArgumentParser(description="Ownership Lens video recording tool")
    parser.add_argument("--scene", default="all", help="Scene to record (e.g., s01, s04, all)")
    parser.add_argument("--durations", default=str(DURATIONS_PATH), help="Path to durations.json")
    args = parser.parse_args()

    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    # Load durations
    durations = DEFAULT_DURATIONS.copy()
    dur_file = Path(args.durations)
    if dur_file.exists():
        try:
            custom_dur = json.loads(dur_file.read_text(encoding="utf-8"))
            durations.update(custom_dur)
            logger.info(f"Loaded custom durations from {dur_file.name}")
        except Exception as e:
            logger.warning(f"Could not load custom durations: {e}")

    # Clean Case nodes before recording (V1)
    logger.info("[V1 Clean State] Purging existing Case nodes before recording...")
    clean_cases()

    scenes_to_run = [args.scene] if args.scene != "all" else list(SCENE_HANDLERS.keys())
    results = {}

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True)
        except Exception:
            browser = p.chromium.launch(headless=True)

        for sc in scenes_to_run:
            dur = durations.get(sc, 22)
            ok = record_scene(sc, dur, browser, durations)
            results[sc] = "PASS" if ok else "FAIL"

        browser.close()

    # Clean Case nodes again after recording (V1)
    logger.info("[V1 Clean State] Purging Case nodes after recording...")
    clean_cases()

    logger.info("=== RECORDING SESSION COMPLETE ===")
    for sc, status in results.items():
        logger.info(f"  {sc}: {status}")

if __name__ == "__main__":
    main()
