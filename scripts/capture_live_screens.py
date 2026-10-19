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
        # 1600x1200 high-res viewport
        page = browser.new_page(viewport={"width": 1600, "height": 1200})
        print("Navigating to live deployed app: https://acd-agent-3hz7.onrender.com/")
        page.goto("https://acd-agent-3hz7.onrender.com/")
        page.wait_for_load_state("networkidle")
        time.sleep(1.5)

        # -------------------------------------------------------------
        # 1. Primary Investigation (GLAISDALE LIMITED, Depth 4)
        # -------------------------------------------------------------
        print("Submitting investigation for GLAISDALE LIMITED (Depth 4)...")
        page.fill("#entityInput", "GLAISDALE LIMITED")
        page.fill("#watchlistInput", "DOM Limited")
        page.select_option("#depthSelect", "4")
        page.click("#btnRun")

        print("Waiting for investigation run to finish...")
        page.wait_for_selector("#btnRun:not([disabled])", timeout=35000)
        page.wait_for_function("() => window.cy && window.cy.nodes().length > 0", timeout=15000)
        time.sleep(2.0)

        # Fit graph nicely with comfortable padding
        page.evaluate("() => window.cy && window.cy.fit(null, 50)")
        time.sleep(1.0)

        # A. COMPLETE FULL GRAPH SCREENSHOT
        # Capture the entire Network Topology View card (including toolbar, hop-banner, legend, and cy canvas)
        graph_card = page.query_selector(".card:has(#cy)")
        if graph_card:
            graph_card.scroll_into_view_if_needed()
            time.sleep(0.5)
            full_graph_path = os.path.join(SCREEN_DIR, "complete_full_graph.png")
            graph_card.screenshot(path=full_graph_path)
            print("Saved complete full graph:", full_graph_path)

        # B. DESKTOP INVESTIGATION DASHBOARD SCREENSHOT
        # Scroll up to show the Parameters + Findings Memo + Network Topology together
        page.evaluate("() => window.scrollTo(0, 160)")
        time.sleep(0.5)
        inv_path = os.path.join(SCREEN_DIR, "desktop_investigation.png")
        page.screenshot(path=inv_path)
        print("Saved investigation dashboard:", inv_path)

        # -------------------------------------------------------------
        # 2. Depth 1 vs Depth 4 Comparison (MUST WAIT FOR FULL COMPLETION)
        # -------------------------------------------------------------
        print("Triggering Depth Comparison (D1 vs D4)...")
        page.evaluate("() => window.scrollTo(0, 0)")
        time.sleep(0.5)
        page.click("#btnCompare")

        print("Waiting for BOTH Depth 1 and Depth 4 to completely finish...")
        page.wait_for_function(
            "() => {"
            "  const b1 = document.querySelector('#contrastD1Badge .badge');"
            "  const b4 = document.querySelector('#contrastD4Badge .badge');"
            "  const hasD1 = b1 && b1.textContent.includes('NO INDICATORS');"
            "  const hasD4 = b4 && b4.textContent.includes('ESCALATE');"
            "  return hasD1 && hasD4;"
            "}",
            timeout=60000,
        )
        print("Both D1 (CLEAR) and D4 (ESCALATE) completed!")
        time.sleep(3.0)  # Crucial: allow cytoscape to layout, calculate positions, and render canvases

        contrast_card = page.query_selector("#contrastCard")
        if contrast_card:
            contrast_card.scroll_into_view_if_needed()
            time.sleep(1.0)
            comp_path = os.path.join(SCREEN_DIR, "desktop_comparison.png")
            contrast_card.screenshot(path=comp_path)
            print("Saved completed comparison:", comp_path)

        browser.close()
        print("ALL SCREENSHOTS SUCCESSFULLY CAPTURED AND SAVED!")


if __name__ == "__main__":
    capture()
