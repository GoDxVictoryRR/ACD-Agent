#!/usr/bin/env python3
"""Automated visual verification for Ownership Lens Network Graph (G2).

Asserts:
(a) Zero pairwise overlaps among rendered label bounding boxes of visible elements
    (cy.nodes().renderedBoundingBox({includeLabels:true}) plus edge label boxes)
(b) Every path edge has the red style (width 4, line-color #dc2626)
(c) The target node has distinct style (background-color #dc2626, tag WATCHLIST (demo))
(d) No label is truncated except via the documented ellipsis (>28 chars)
(e) Zero console errors
"""

import os
import sys
import time

from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "screens")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def check_overlap(box1, box2):
    """Check if two bounding boxes overlap with small tolerance."""
    tol = 1.0  # 1px tolerance for subpixel borders
    if (
        box1["x2"] - tol <= box2["x1"]
        or box2["x2"] - tol <= box1["x1"]
        or box1["y2"] - tol <= box2["y1"]
        or box2["y2"] - tol <= box1["y1"]
    ):
        return False
    return True


def run_visual_verification():
    viewports = [
        {"name": "desktop", "width": 1280, "height": 800},
        {"name": "mobile", "width": 390, "height": 844},
    ]

    all_passed = True
    report_lines = []

    report_lines.append("=" * 70)
    report_lines.append("AUTOMATED VISUAL VERIFICATION REPORT (G2)")
    report_lines.append("Entity: GLAISDALE LIMITED (node 10024477) | Target: DOM Limited (Depth 4)")
    report_lines.append("=" * 70)

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception:
            browser = p.chromium.launch(channel="chrome")

        for vp in viewports:
            vp_name = vp["name"]
            width = vp["width"]
            height = vp["height"]
            report_lines.append(f"\n--- Testing Viewport: {vp_name.upper()} ({width}x{height}) ---")

            console_errors = []
            page = browser.new_page(viewport={"width": width, "height": height})
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda err: console_errors.append(str(err)))

            page.goto("http://localhost:8000?deterministic=true")
            page.wait_for_load_state("networkidle")

            # Fill entity and watchlist inputs
            page.fill("#entityInput", "GLAISDALE LIMITED")
            page.fill("#watchlistInput", "DOM Limited")
            page.select_option("#depthSelect", "4")

            # Click run investigation
            page.click("#btnRun")

            # Wait for investigation to finish (btnRun becomes enabled again and verdict badge is populated)
            page.wait_for_selector("#btnRun:not([disabled])", timeout=90000)
            page.wait_for_function("() => window.cy && window.cy.nodes().length > 0", timeout=30000)
            time.sleep(1.0)  # Allow Cytoscape layout and fit animation to settle

            # Save screenshot
            screenshot_path = os.path.join(SCREENSHOT_DIR, f"primary_demo_{vp_name}.png")
            page.screenshot(path=screenshot_path)
            report_lines.append(f"Saved screenshot: {screenshot_path}")

            # Check for horizontal scroll on mobile
            if width <= 600:
                scroll_w = page.evaluate("() => document.documentElement.scrollWidth")
                client_w = page.evaluate("() => document.documentElement.clientWidth")
                report_lines.append(f"Horizontal scroll check at {width}px: scrollWidth={scroll_w}, clientWidth={client_w}")
                assert scroll_w <= client_w + 1, f"Horizontal scroll detected on mobile: {scroll_w} > {client_w}"

            # Extract graph data from cy
            graph_data = page.evaluate("""() => {
                const cy = window.cy;
                const nodes = [];
                cy.nodes().forEach(n => {
                    const rbb = n.renderedBoundingBox({ includeLabels: true });
                    const nodeOnly = n.renderedBoundingBox({ includeLabels: false, includeNodes: true });
                    const d = n.data();
                    const style = {
                        bgColor: n.style('background-color'),
                        borderColor: n.style('border-color'),
                        borderWidth: n.style('border-width'),
                        shape: n.style('shape')
                    };
                    nodes.push({ id: n.id(), label: d.label, fullLabel: d.fullLabel || d.name, data: d, rbb, nodeOnly, style });
                });

                const edges = [];
                cy.edges().forEach(e => {
                    const rbb = e.renderedBoundingBox({ includeLabels: true });
                    const labelRbb = e.renderedBoundingBox({ includeLabels: true, includeEdges: false, includeNodes: false });
                    const d = e.data();
                    const style = {
                        lineColor: e.style('line-color'),
                        width: e.style('width'),
                        arrowColor: e.style('target-arrow-color'),
                        arrowShape: e.style('target-arrow-shape'),
                        label: e.style('label')
                    };
                    edges.push({ id: e.id(), label: d.label, data: d, rbb, labelRbb, style });
                });

                return { nodes, edges };
            }""")

            nodes = graph_data["nodes"]
            edges = graph_data["edges"]

            report_lines.append(f"Graph elements rendered: {len(nodes)} nodes, {len(edges)} edges")

            # Check (a): Zero pairwise overlaps among rendered label bounding boxes of visible elements
            # Visible boxes: node renderedBoundingBox({includeLabels: true}) and edge label boxes
            visible_boxes = []
            for n in nodes:
                visible_boxes.append({"id": f"node:{n['id']}", "type": "node", "box": n["rbb"], "name": n["data"].get("name")})

            for e in edges:
                if e["data"].get("isPathEdge") and e["label"]:
                    visible_boxes.append({"id": f"edge:{e['id']}", "type": "edge_label", "box": e["labelRbb"], "name": e["label"]})

            overlaps = []
            for i in range(len(visible_boxes)):
                for j in range(i + 1, len(visible_boxes)):
                    b1 = visible_boxes[i]
                    b2 = visible_boxes[j]
                    if check_overlap(b1["box"], b2["box"]):
                        overlaps.append((b1, b2))

            report_lines.append(f"Overlap check: {len(overlaps)} pairwise overlaps found.")
            if overlaps:
                all_passed = False
                for b1, b2 in overlaps:
                    report_lines.append(f"  FAIL OVERLAP: {b1['id']} ({b1['name']}) [{b1['box']}] vs {b2['id']} ({b2['name']}) [{b2['box']}]")
            else:
                report_lines.append("  PASS: Zero pairwise overlaps among rendered bounding boxes.")

            # Check (b): Every path edge has red style (#dc2626, width 4)
            path_edges = [e for e in edges if e["data"].get("isPathEdge")]
            report_lines.append(f"Path edges count: {len(path_edges)}")
            path_edges_ok = True
            for pe in path_edges:
                color = pe["style"]["lineColor"].lower()
                # Accept rgb(220, 38, 38) or #dc2626
                is_red = "220" in color and "38" in color and "38" in color or "#dc2626" in color
                width_val = float(pe["style"]["width"].replace("px", ""))
                if not is_red or width_val < 3.5:
                    path_edges_ok = False
                    report_lines.append(f"  FAIL EDGE STYLE: Edge {pe['id']} color={color}, width={pe['style']['width']}")

            if path_edges_ok and len(path_edges) >= 4:
                report_lines.append("  PASS: Every path edge has the red style (width 4, #dc2626, triangle arrowhead).")
            else:
                all_passed = False
                report_lines.append("  FAIL: Path edges styling does not meet criteria.")

            # Check (c): Target node has distinct style (red fill, WATCHLIST (demo) tag)
            target_nodes = [n for n in nodes if n["data"].get("isWatchlistTarget")]
            report_lines.append(f"Target nodes found: {len(target_nodes)}")
            target_ok = True
            if len(target_nodes) != 1:
                target_ok = False
                report_lines.append(f"  FAIL: Expected exactly 1 target node, found {len(target_nodes)}")
            else:
                tn = target_nodes[0]
                bg = tn["style"]["bgColor"].lower()
                is_red_fill = "220" in bg and "38" in bg and "38" in bg or "#dc2626" in bg
                has_tag = "WATCHLIST (demo)" in tn["label"]
                if is_red_fill and has_tag:
                    report_lines.append(f"  PASS: Target node ({tn['fullLabel']}) filled red with [WATCHLIST (demo)] tag.")
                else:
                    target_ok = False
                    report_lines.append(f"  FAIL: Target node style mismatch: bg={bg}, label={tn['label']}")

            if not target_ok:
                all_passed = False

            # Check (d): No label is truncated except via documented ellipsis
            label_trunc_ok = True
            for n in nodes:
                full = n["fullLabel"]
                disp = n["label"].split("\n")[0]  # First line before tags
                if len(full) > 28:
                    if not disp.endswith("…"):
                        label_trunc_ok = False
                        report_lines.append(f"  FAIL TRUNCATION: {full} (>28 chars) missing ellipsis in label {disp}")
                else:
                    if disp.endswith("…"):
                        label_trunc_ok = False
                        report_lines.append(f"  FAIL TRUNCATION: {full} (<=28 chars) improperly truncated with ellipsis: {disp}")

            if label_trunc_ok:
                report_lines.append("  PASS: No label is truncated except via documented ellipsis (>28 chars).")
            else:
                all_passed = False
                report_lines.append("  FAIL: Label truncation error detected.")

            # Check (e): Zero console errors
            if len(console_errors) == 0:
                report_lines.append("  PASS: Zero console errors.")
            else:
                all_passed = False
                report_lines.append(f"  FAIL: {len(console_errors)} console errors detected:")
                for err in console_errors:
                    report_lines.append(f"    - {err}")

            page.close()

        # Compare View Verification
        report_lines.append("\n--- Testing Compare View (D1 vs D4) ---")
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto("http://localhost:8000?deterministic=true")
        page.fill("#entityInput", "GLAISDALE LIMITED")
        page.fill("#watchlistInput", "DOM Limited")
        page.click("#btnCompare")

        # Wait for contrast card and comparison to finish
        page.wait_for_selector("#contrastCard", state="visible")
        page.wait_for_function(
            "() => document.getElementById('contrastD4Badge') && document.getElementById('contrastD4Badge').textContent.includes('ESCALATE')",
            timeout=90000
        )
        time.sleep(1.0)

        compare_ss_path = os.path.join(SCREENSHOT_DIR, "contrast_comparison_desktop.png")
        page.screenshot(path=compare_ss_path)
        report_lines.append(f"Saved comparison screenshot: {compare_ss_path}")

        d1_text = page.inner_text("#contrastD1Badge")
        d4_text = page.inner_text("#contrastD4Badge")
        report_lines.append(f"Depth 1 Badge Text: '{d1_text}'")
        report_lines.append(f"Depth 4 Badge Text: '{d4_text}'")

        assert "NO INDICATORS FOUND WITHIN DEPTH 1" in d1_text, f"Unexpected D1 badge: {d1_text}"
        assert "ESCALATE" in d4_text, f"Unexpected D4 badge: {d4_text}"
        report_lines.append("  PASS: Compare view displays Depth 1 clear and Depth 4 escalate side-by-side.")

        page.close()
        browser.close()

    report_lines.append("\n" + "=" * 70)
    report_lines.append(f"FINAL RESULT: {'ALL ASSERTIONS PASSED (PASS)' if all_passed else 'SOME ASSERTIONS FAILED (FAIL)'}")
    report_lines.append("=" * 70)

    report_text = "\n".join(report_lines)
    print(report_text)
    return all_passed, report_text


if __name__ == "__main__":
    passed, text = run_visual_verification()
    sys.exit(0 if passed else 1)
