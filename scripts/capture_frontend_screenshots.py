#!/usr/bin/env python3
"""
capture_frontend_screenshots.py — Uses Playwright to render and capture high-resolution
screenshots of the clean light-theme frontend for Project D.H.A.R.M.A.
"""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright

DOCS_DIR = Path("/home/aumpatro/Project_Crime_detection/docs/presentation")
DOCS_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_DIR = Path("/home/aumpatro/.gemini/antigravity/brain/54b88550-132d-4e29-8288-14e473dd7fca")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

def capture():
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

        # 1. Capture initial clean landing view
        path_landing = DOCS_DIR / "frontend_light_initial.png"
        path_landing_art = ARTIFACT_DIR / "frontend_light_initial.png"
        page.screenshot(path=str(path_landing))
        page.screenshot(path=str(path_landing_art))
        print(f"Captured initial landing view: {path_landing}")

        # 2. Click the first preset template
        pills = page.query_selector_all(".preset-pill")
        if pills:
            print(f"Found {len(pills)} preset pills. Clicking first pill...")
            pills[0].click()
            time.sleep(0.5)

        # 3. Click 'Analyze Incident' button
        btn_analyze = page.query_selector("#btnAnalyze")
        if btn_analyze:
            print("Clicking Analyze Incident...")
            btn_analyze.click()
            # Wait for results to populate (ticker status becomes VERIFIED or COMPLETE)
            time.sleep(2.5)

        # 4. Capture Tab 1: M.O. Classification
        path_mo = DOCS_DIR / "frontend_tab1_mo_matrix.png"
        path_mo_art = ARTIFACT_DIR / "frontend_tab1_mo_matrix.png"
        page.screenshot(path=str(path_mo))
        page.screenshot(path=str(path_mo_art))
        print(f"Captured Tab 1 M.O. Matrix: {path_mo}")

        # 5. Capture Tab 2: Accuracy & Benchmark Proof
        btn_tab_acc = page.query_selector('button[data-tab="tab-accuracy"]')
        if btn_tab_acc:
            btn_tab_acc.click()
            time.sleep(0.8)
            path_acc = DOCS_DIR / "frontend_tab2_accuracy_proof.png"
            path_acc_art = ARTIFACT_DIR / "frontend_tab2_accuracy_proof.png"
            page.screenshot(path=str(path_acc))
            page.screenshot(path=str(path_acc_art))
            print(f"Captured Tab 2 Accuracy Proof: {path_acc}")

        # 6. Capture Tab 4: Forensic Leads & Scenarios
        btn_tab_reason = page.query_selector('button[data-tab="tab-reasoning"]')
        if btn_tab_reason:
            btn_tab_reason.click()
            time.sleep(0.8)
            path_reason = DOCS_DIR / "frontend_tab4_forensic_leads.png"
            path_reason_art = ARTIFACT_DIR / "frontend_tab4_forensic_leads.png"
            page.screenshot(path=str(path_reason))
            page.screenshot(path=str(path_reason_art))
            print(f"Captured Tab 4 Forensic Leads: {path_reason}")

        # 7. Capture Tab 5: Privacy & Redaction
        btn_tab_priv = page.query_selector('button[data-tab="tab-privacy"]')
        if btn_tab_priv:
            btn_tab_priv.click()
            time.sleep(0.8)
            path_priv = DOCS_DIR / "frontend_tab5_privacy_audit.png"
            path_priv_art = ARTIFACT_DIR / "frontend_tab5_privacy_audit.png"
            page.screenshot(path=str(path_priv))
            page.screenshot(path=str(path_priv_art))
            print(f"Captured Tab 5 Privacy Audit: {path_priv}")

        browser.close()
        print("All screenshots successfully captured!")

if __name__ == "__main__":
    capture()
