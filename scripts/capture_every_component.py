#!/usr/bin/env python3
"""
capture_every_component.py — Captures comprehensive, high-resolution screenshots
of EVERY tab, panel, card, table, and component on the frontend with the new title:
"Tracing Criminal Behavior Through Movement and Modus Operandi".
"""

import time
import os
import shutil
import zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path("/home/aumpatro/Project_Crime_detection")
SCREENSHOTS_DIR = ROOT / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

DOCS_DIR = ROOT / "docs" / "presentation"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_DIR = Path("/home/aumpatro/.gemini/antigravity/brain/54b88550-132d-4e29-8288-14e473dd7fca")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

def save_screenshot(element_or_page, name: str):
    path_main = SCREENSHOTS_DIR / name
    path_docs = DOCS_DIR / name
    path_art = ARTIFACT_DIR / name
    
    element_or_page.screenshot(path=str(path_main))
    shutil.copy2(path_main, path_docs)
    shutil.copy2(path_main, path_art)
    print(f"Captured: {name}")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1560, "height": 980},
            device_scale_factor=2
        )
        page = context.new_page()

        print("Navigating to http://localhost:8008/...")
        page.goto("http://localhost:8008/", wait_until="networkidle")
        time.sleep(1.5)

        # 01. Full initial dashboard with new title
        save_screenshot(page, "01_full_dashboard_new_title.png")

        # 02. Header Component close-up
        header = page.query_selector(".top-header")
        if header:
            save_screenshot(header, "02_component_header_branding.png")

        # 03. Presets bar close-up
        presets = page.query_selector(".preset-section")
        if presets:
            save_screenshot(presets, "03_component_preset_templates_bar.png")

        # Click first preset and populate
        pills = page.query_selector_all(".preset-pill")
        if pills:
            pills[0].click()
            time.sleep(0.5)

        # 04. Left Input Panel close-up (with narrative and location controls)
        left_panel = page.query_selector(".panel-input")
        if left_panel:
            save_screenshot(left_panel, "04_component_input_narrative_panel.png")

        # Click Analyze Incident
        btn_analyze = page.query_selector("#btnAnalyze")
        if btn_analyze:
            btn_analyze.click()
            time.sleep(2.5)

        # 05. Tab 1 Full View (M.O. Classification)
        save_screenshot(page, "05_tab1_mo_classification_full.png")

        # 06. Component: Primary Findings Banner
        banner = page.query_selector(".mo-summary-banner")
        if banner:
            save_screenshot(banner, "06_component_primary_finding_banner.png")

        # 07. Component: 4 M.O. Cards Grid
        mo_grid = page.query_selector(".mo-heads-grid")
        if mo_grid:
            save_screenshot(mo_grid, "07_component_mo_cards_grid.png")

        # 08. Tab 2 Full View (Accuracy & Benchmark Proof)
        btn_tab2 = page.query_selector('button[data-tab="tab-accuracy"]')
        if btn_tab2:
            btn_tab2.click()
            time.sleep(1.0)
            save_screenshot(page, "08_tab2_accuracy_benchmark_proof.png")

            # 09. Component: Accuracy Banner & Stats
            acc_banner = page.query_selector(".accuracy-banner")
            if acc_banner:
                save_screenshot(acc_banner, "09_component_accuracy_summary_stats.png")

            # 10. Component: Holdout Accuracy Table (1,000 cases)
            tables = page.query_selector_all(".math-formulas-card")
            if len(tables) > 0:
                save_screenshot(tables[0], "10_component_holdout_accuracy_table.png")
            if len(tables) > 1:
                save_screenshot(tables[1], "11_component_gnn_road_graph_table.png")
            if len(tables) > 2:
                save_screenshot(tables[2], "12_component_math_decision_formulas.png")

        # 13. Tab 3 Full View (Incident Map & Hotspots)
        btn_tab3 = page.query_selector('button[data-tab="tab-spatial"]')
        if btn_tab3:
            btn_tab3.click()
            time.sleep(1.5)
            save_screenshot(page, "13_tab3_incident_map_and_hotspots.png")

            sp_stats = page.query_selector(".spatial-overview-grid")
            if sp_stats:
                save_screenshot(sp_stats, "14_component_spatial_overview_stats.png")

            hotspots = page.query_selector(".hotspots-card")
            if hotspots:
                save_screenshot(hotspots, "15_component_regional_hotspots_table.png")

        # 16. Tab 4 Full View (Forensic Leads & Scenarios)
        btn_tab4 = page.query_selector('button[data-tab="tab-reasoning"]')
        if btn_tab4:
            btn_tab4.click()
            time.sleep(1.0)
            save_screenshot(page, "16_tab4_forensic_leads_and_scenarios.png")

            entropy = page.query_selector(".entropy-dashboard-card")
            if entropy:
                save_screenshot(entropy, "17_component_clarity_entropy_meters.png")

            scenarios = page.query_selector(".scenarios-container")
            if scenarios:
                save_screenshot(scenarios, "18_component_ranked_hypotheses_cards.png")

        # 19. Tab 5 Full View (Privacy & Redaction)
        btn_tab5 = page.query_selector('button[data-tab="tab-privacy"]')
        if btn_tab5:
            btn_tab5.click()
            time.sleep(1.0)
            save_screenshot(page, "19_tab5_privacy_and_redaction_audit.png")

            priv_stats = page.query_selector(".privacy-stats-row")
            if priv_stats:
                save_screenshot(priv_stats, "20_component_privacy_metrics_cards.png")

            diff = page.query_selector(".diff-comparison-box")
            if diff:
                save_screenshot(diff, "21_component_side_by_side_diff.png")

            entities = page.query_selector(".entity-audit-table-card")
            if entities:
                save_screenshot(entities, "22_component_detected_entities_chips.png")

        browser.close()

    # Also copy the 5 academic evaluation charts into screenshots dir
    academic_charts = {
        "23_model_classification_accuracy_f1_barchart.png": DOCS_DIR / "model_classification_accuracy_f1.png",
        "24_heads_classification_accuracy_f1_barchart.png": DOCS_DIR / "heads_classification_accuracy_f1.png",
        "25_learning_curves_across_5_architectures.png": DOCS_DIR / "learning_curves_across_5_architectures.png",
        "26_standalone_accuracy_benchmark_barchart.png": DOCS_DIR / "model_accuracy_barchart.png",
        "27_comprehensive_academic_model_audit_dashboard.png": DOCS_DIR / "full_model_audit_dashboard.png",
    }
    for dest_name, src_path in academic_charts.items():
        if src_path.exists():
            shutil.copy2(src_path, SCREENSHOTS_DIR / dest_name)
            shutil.copy2(src_path, ARTIFACT_DIR / dest_name)
            print(f"Copied chart: {dest_name}")

    # Re-build master ZIP
    zip_path = ROOT / "Project_Screenshots_and_Charts.zip"
    all_files = sorted(os.listdir(SCREENSHOTS_DIR))
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for fname in all_files:
            if fname.endswith(".png"):
                zf.write(SCREENSHOTS_DIR / fname, arcname=fname)
    
    # Copy to static for direct download
    static_zip = ROOT / "static" / "screenshots.zip"
    shutil.copy2(zip_path, static_zip)
    print(f"Updated ZIP at {zip_path} ({len(all_files)} files, {zip_path.stat().st_size} bytes)")

if __name__ == "__main__":
    run()
