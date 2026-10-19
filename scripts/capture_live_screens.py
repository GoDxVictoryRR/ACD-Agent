#!/usr/bin/env python3
"""Capture high-resolution screenshots from the live deployed Ownership Lens application."""

import os
import time
from playwright.sync_api import sync_playwright

SCREEN_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "screens")
os.makedirs(SCREEN_DIR, exist_ok=True)


def capture():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1500, "height": 1300})
        print("Navigating to live deployed app: https://acd-agent-3hz7.onrender.com/")
        page.goto("https://acd-agent-3hz7.onrender.com/")
        page.wait_for_load_state("networkidle")
        time.sleep(1.5)

        # 1. Primary Investigation Screenshot
        print("Submitting investigation for GLAISDALE LIMITED (Depth 4)...")
        page.fill("#entityInput", "GLAISDALE LIMITED")
        page.fill("#watchlistInput", "DOM Limited")
        page.select_option("#depthSelect", "4")
        page.click("#btnRun")

        page.wait_for_selector("#btnRun:not([disabled])", timeout=30000)
        page.wait_for_function("() => window.cy && window.cy.nodes().length > 0", timeout=15000)
        time.sleep(2.0)
        page.evaluate("() => window.cy && window.cy.fit(null, 40)")
        time.sleep(1.0)

        # Scroll down slightly so the entire investigation dashboard (verdict + graph) fits comfortably in view
        page.evaluate("() => window.scrollTo(0, 120)")
        time.sleep(0.5)

        # Capture primary investigation view
        inv_path = os.path.join(SCREEN_DIR, "desktop_investigation.png")
        page.screenshot(path=inv_path)
        print("Saved:", inv_path)

        # Capture focused graph topology canvas
        cy_el = page.query_selector(".card:has(#cy)")
        if cy_el:
            graph_path = os.path.join(SCREEN_DIR, "graph_focused.png")
            cy_el.screenshot(path=graph_path)
            print("Saved:", graph_path)

        # 2. Depth 1 vs Depth 4 Comparison Screenshot
        print("Running depth comparison (D1 vs D4)...")
        page.click("#btnCompare")

        # Wait for comparison SSE stream to complete both D1 and D4
        page.wait_for_function(
            "() => {"
            "  const badge = document.querySelector('#contrastD4Badge .badge');"
            "  return badge && !badge.textContent.includes('RUNNING');"
            "}",
            timeout=30000,
        )
        time.sleep(2.0)

        # Scroll contrast card into clean view
        page.evaluate("() => document.getElementById('contrastCard').scrollIntoView({ behavior: 'instant', block: 'start' })")
        time.sleep(1.0)

        comp_path = os.path.join(SCREEN_DIR, "desktop_comparison.png")
        page.screenshot(path=comp_path)
        print("Saved:", comp_path)

        browser.close()
        print("ALL SCREENSHOTS CAPTURED SUCCESSFULLY!")


if __name__ == "__main__":
    capture()
