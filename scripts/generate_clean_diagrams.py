#!/usr/bin/env python3
"""
generate_clean_diagrams.py — Renders 3 publication-grade, light-theme architectural
diagrams (Flow Chart, Work Flow Diagram, Data Flow Diagram) via HTML/SVG + Playwright
at 2x Retina DPI so they blend seamlessly onto the GIET University presentation template.
"""

from pathlib import Path
from playwright.sync_api import sync_playwright

OUT_DIR = Path("/home/aumpatro/Project_Crime_detection/docs/presentation")
OUT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR = Path("/home/aumpatro/.gemini/antigravity/brain/54b88550-132d-4e29-8288-14e473dd7fca")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

COMMON_CSS = """
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    background: transparent;
    color: #0f172a;
    -webkit-font-smoothing: antialiased;
  }
"""

# ---------------------------------------------------------------------------
# 1. FLOW CHART (3-Tier End-to-End Architecture Flow Chart)
# ---------------------------------------------------------------------------
FLOWCHART_HTML = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{COMMON_CSS}
.canvas {{
  width: 1120px;
  height: 560px;
  background: #ffffff;
  border: 2px solid #cbd5e1;
  border-radius: 16px;
  padding: 20px 26px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
  position: relative;
}}
.tier-banner {{
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #334155;
  margin-bottom: 6px;
}}
.tier-dot {{
  width: 10px;
  height: 10px;
  border-radius: 50%;
}}
.row {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}}
.node {{
  flex: 1;
  background: #f8fafc;
  border: 2px solid #94a3b8;
  border-radius: 12px;
  padding: 11px 13px;
  min-height: 98px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  box-shadow: 0 3px 8px rgba(15, 23, 42, 0.05);
  position: relative;
}}
.node-badge {{
  display: inline-block;
  font-size: 10px;
  font-weight: 800;
  padding: 2px 7px;
  border-radius: 999px;
  margin-bottom: 5px;
  width: fit-content;
  letter-spacing: 0.04em;
}}
.node-title {{
  font-size: 13.5px;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.25;
  margin-bottom: 4px;
}}
.node-sub {{
  font-size: 11.2px;
  color: #475569;
  line-height: 1.35;
  font-weight: 500;
}}
/* Color themes */
.theme-blue {{ background: #eff6ff; border-color: #2563eb; }}
.theme-blue .node-badge {{ background: #dbeafe; color: #1e40af; }}

.theme-teal {{ background: #f0fdfa; border-color: #0d9488; }}
.theme-teal .node-badge {{ background: #ccfbf1; color: #115e59; }}

.theme-amber {{ background: #fffbeb; border-color: #d97706; }}
.theme-amber .node-badge {{ background: #fef3c7; color: #92400e; }}

.theme-emerald {{ background: #f0fdf4; border-color: #16a34a; }}
.theme-emerald .node-badge {{ background: #dcfce7; color: #166534; }}

.theme-indigo {{ background: #eef2ff; border-color: #4f46e5; }}
.theme-indigo .node-badge {{ background: #e0e7ff; color: #3730a3; }}

.theme-purple {{ background: #faf5ff; border-color: #7c3aed; }}
.theme-purple .node-badge {{ background: #f3e8ff; color: #5b21b6; }}

.theme-rose {{ background: #fff1f2; border-color: #e11d48; }}
.theme-rose .node-badge {{ background: #ffe4e6; color: #9f1239; }}

.arrow {{
  font-size: 22px;
  font-weight: 900;
  color: #475569;
  flex: 0 0 22px;
  text-align: center;
}}
.down-connector {{
  display: flex;
  justify-content: flex-end;
  padding-right: 110px;
  color: #2563eb;
  font-size: 13px;
  font-weight: 800;
  align-items: center;
  gap: 6px;
}}
.down-connector-left {{
  display: flex;
  justify-content: flex-start;
  padding-left: 110px;
  color: #16a34a;
  font-size: 13px;
  font-weight: 800;
  align-items: center;
  gap: 6px;
}}
</style>
</head>
<body>
<div class="canvas">
  <!-- TIER 1 -->
  <div>
    <div class="tier-banner"><span class="tier-dot" style="background:#2563eb"></span> TIER 1: DATA INGESTION &amp; ZERO-PII PRIVACY SANITIZATION</div>
    <div class="row">
      <div class="node theme-blue">
        <span class="node-badge">STEP 1 • RAW ARCHIVES</span>
        <div class="node-title">Multi-Agency Crime Datasets</div>
        <div class="node-sub">NYPD, LAPD, UK Police, Houston, Chicago &amp; SF (<strong>20.37M+ Records</strong>)</div>
      </div>
      <div class="arrow">&rarr;</div>
      <div class="node theme-blue">
        <span class="node-badge">STEP 2 • STREAMING ETL</span>
        <div class="node-title">Chunked Ingestion Engine</div>
        <div class="node-sub">Memory-bounded streaming reader (&le;18 GB RAM) with coordinate validation</div>
      </div>
      <div class="arrow">&rarr;</div>
      <div class="node theme-teal">
        <span class="node-badge">STEP 3 • ON-PREMISE NER</span>
        <div class="node-title">Zero-PII Scrubbing Engine</div>
        <div class="node-sub">13 Regex rules + spaCy NER masking names, badges, phones &amp; addresses</div>
      </div>
      <div class="arrow">&rarr;</div>
      <div class="node theme-teal">
        <span class="node-badge">STEP 4 • CJIS COMPLIANT</span>
        <div class="node-title">Coreference-Preserved Text</div>
        <div class="node-sub">Consistent typed tokens (<code>Person_01</code>, <code>Officer_Alpha</code>) • <strong>100% Recall</strong></div>
      </div>
    </div>
  </div>

  <div class="down-connector">&darr; Sanitized Narratives Feed Teacher-Student Distillation &darr;</div>

  <!-- TIER 2 -->
  <div>
    <div class="tier-banner"><span class="tier-dot" style="background:#16a34a"></span> TIER 2: TEACHER-STUDENT KNOWLEDGE DISTILLATION &amp; FORENSIC M.O. EXTRACTION</div>
    <div class="row">
      <div class="node theme-emerald">
        <span class="node-badge">STEP 8 • BATCH &amp; LIVE CPU</span>
        <div class="node-title">High-Throughput Inference</div>
        <div class="node-sub">24-Core Xeon bfloat16 (<strong>1,285+ rec/s</strong> batch • <strong>18 ms</strong> real-time • $0 Cloud Cost)</div>
      </div>
      <div class="arrow">&larr;</div>
      <div class="node theme-emerald">
        <span class="node-badge">STEP 7 • STUDENT MODEL</span>
        <div class="node-title">Multi-Head DistilBERT (66M)</div>
        <div class="node-sub">Weapon (98.2%), Suspects (95.7%), Entry (94.4%), Target (91.1%) • <strong>94.85% Acc</strong></div>
      </div>
      <div class="arrow">&larr;</div>
      <div class="node theme-amber">
        <span class="node-badge">STEP 6 • BENCHMARK CORPUS</span>
        <div class="node-title">3,500 Gold + 1,000 Holdout</div>
        <div class="node-sub">Stratified multi-task training seeds + 1,000 unseen test records</div>
      </div>
      <div class="arrow">&larr;</div>
      <div class="node theme-amber">
        <span class="node-badge">STEP 5 • TEACHER LLM</span>
        <div class="node-title">LLaMA 3.3-70B (Groq LPU)</div>
        <div class="node-sub">Zero-temperature (T=0.0) forensic M.O. label generation (Offline-decapitated)</div>
      </div>
    </div>
  </div>

  <div class="down-connector-left">&darr; Enriched Parquet Matrix &amp; Probability Logits Feed Spatial GNN &amp; Reasoning &darr;</div>

  <!-- TIER 3 -->
  <div>
    <div class="tier-banner"><span class="tier-dot" style="background:#4f46e5"></span> TIER 3: SPATIOTEMPORAL GNN FORECASTING, FORENSIC THINKING &amp; TACTICAL CONSOLE</div>
    <div class="row">
      <div class="node theme-indigo">
        <span class="node-badge">STEP 9 • GEOSPATIAL FUSION</span>
        <div class="node-title">H3 + Census + NOAA + OSMnx</div>
        <div class="node-sub">Hexagonal indexing, demographics, weather &amp; street graphs (<strong>29,807 Chicago nodes</strong>)</div>
      </div>
      <div class="arrow">&rarr;</div>
      <div class="node theme-purple">
        <span class="node-badge">STEP 10 • GRAPH NEURAL NET</span>
        <div class="node-title">CrimeSTGCN Risk Forecaster</div>
        <div class="node-sub">Normalized Laplacian GraphConv + 2-Layer GRU • <strong>31.5% Top-15 Hit Rate (630&times; Lift)</strong></div>
      </div>
      <div class="arrow">&rarr;</div>
      <div class="node theme-purple">
        <span class="node-badge">STEP 11 • MATHEMATICAL AUDIT</span>
        <div class="node-title">Forensic Thinking Engine</div>
        <div class="node-sub">Softmax likelihood, Top-2 Margin (&Delta;) &amp; Shannon Entropy H(P) multi-hypothesis leads</div>
      </div>
      <div class="arrow">&rarr;</div>
      <div class="node theme-rose">
        <span class="node-badge">STEP 12 • DECISION SUPPORT</span>
        <div class="node-title">FastAPI &amp; Mapbox Web Console</div>
        <div class="node-sub">5-Tab interactive dashboard (:8008) for live M.O., Hotspot Radar &amp; PII Audit</div>
      </div>
    </div>
  </div>
</div>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# 2. WORK FLOW DIAGRAM (Staged Pipeline Architecture)
# ---------------------------------------------------------------------------
WORKFLOW_HTML = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{COMMON_CSS}
.canvas {{
  width: 1120px;
  height: 480px;
  background: #ffffff;
  border: 2px solid #cbd5e1;
  border-radius: 16px;
  padding: 22px 24px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
}}
.wf-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 10px;
}}
.wf-title {{
  font-size: 14px;
  font-weight: 800;
  color: #1e293b;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}}
.wf-kpis {{
  display: flex;
  gap: 10px;
}}
.kpi-pill {{
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 999px;
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}}
.pipeline-grid {{
  display: grid;
  grid-template-columns: 1fr 26px 1fr 26px 1.15fr 26px 1fr 26px 1.25fr;
  align-items: center;
  flex: 1;
  margin: 12px 0;
}}
.stage-card {{
  background: #f8fafc;
  border: 2px solid #cbd5e1;
  border-radius: 12px;
  padding: 14px 12px;
  height: 310px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 3px 10px rgba(15, 23, 42, 0.04);
}}
.stage-top {{
  display: flex;
  flex-direction: column;
  gap: 6px;
}}
.stage-num {{
  font-size: 10.5px;
  font-weight: 800;
  padding: 3px 8px;
  border-radius: 6px;
  width: fit-content;
  letter-spacing: 0.05em;
}}
.stage-name {{
  font-size: 14px;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.25;
}}
.stage-list {{
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 7px;
  margin-top: 6px;
}}
.stage-list li {{
  font-size: 11.2px;
  color: #334155;
  line-height: 1.35;
  padding-left: 12px;
  position: relative;
  font-weight: 500;
}}
.stage-list li::before {{
  content: "•";
  position: absolute;
  left: 0;
  font-weight: 900;
  color: #2563eb;
}}
.stage-footer {{
  font-size: 10.5px;
  font-weight: 700;
  padding: 6px 8px;
  border-radius: 6px;
  text-align: center;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  color: #0f172a;
}}
.split-stack {{
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 310px;
}}
.sub-card {{
  flex: 1;
  border: 2px solid #cbd5e1;
  border-radius: 12px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}}
.conn {{
  text-align: center;
  font-size: 22px;
  font-weight: 900;
  color: #475569;
}}
.wf-bottom-bar {{
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 8px 14px;
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  font-weight: 600;
  color: #334155;
}}
</style>
</head>
<body>
<div class="canvas">
  <div class="wf-header">
    <div class="wf-title">End-to-End Execution Workflow — From Raw Police Dispatch to Predictive Crime Intelligence</div>
    <div class="wf-kpis">
      <span class="kpi-pill">100% Offline Inference</span>
      <span class="kpi-pill" style="background:#eff6ff;color:#1e40af;border-color:#bfdbfe;">94.85% Holdout Accuracy</span>
      <span class="kpi-pill" style="background:#faf5ff;color:#6b21a8;border-color:#e9d5ff;">31.5% ST-GCN Hit Rate</span>
    </div>
  </div>

  <div class="pipeline-grid">
    <!-- Stage 1 -->
    <div class="stage-card" style="background:#eff6ff;border-color:#2563eb;">
      <div class="stage-top">
        <span class="stage-num" style="background:#2563eb;color:#fff;">STAGE 1 • INGEST</span>
        <div class="stage-name">Multi-Source Crime Ingestion</div>
        <ul class="stage-list">
          <li>6 National Archives (NYPD, UK, LAPD, Houston, Chicago, SF)</li>
          <li>Chunked streaming reader (50k rows/batch)</li>
          <li>Spatial bounding-box &amp; timestamp normalization</li>
        </ul>
      </div>
      <div class="stage-footer">20,373,839 Total Records</div>
    </div>

    <div class="conn">&rarr;</div>

    <!-- Stage 2 -->
    <div class="stage-card" style="background:#f0fdfa;border-color:#0d9488;">
      <div class="stage-top">
        <span class="stage-num" style="background:#0d9488;color:#fff;">STAGE 2 • PRIVACY</span>
        <div class="stage-name">Local Zero-PII Scrubbing</div>
        <ul class="stage-list">
          <li>13 Regex patterns (SSN, phone, badge, plates, addresses)</li>
          <li>spaCy NER person &amp; witness detection</li>
          <li>Deterministic coreference tokens (<code>Person_01</code>)</li>
        </ul>
      </div>
      <div class="stage-footer">100% Redaction (50/50 Tests)</div>
    </div>

    <div class="conn">&rarr;</div>

    <!-- Stage 3A / 3B -->
    <div class="split-stack">
      <div class="sub-card" style="background:#fffbeb;border-color:#d97706;">
        <div>
          <span class="stage-num" style="background:#d97706;color:#fff;">STAGE 3A • TEACHER</span>
          <div class="stage-name" style="margin-top:4px;font-size:13px;">LLaMA 3.3-70B Distillation</div>
          <div style="font-size:11px;color:#475569;margin-top:3px;">Groq LPU (T=0.0) extracts 3,500 Gold M.O. seeds + 1,000 unseen test records.</div>
        </div>
        <div class="stage-footer" style="font-size:10px;padding:4px;">Decapitated at Runtime ($0 Cost)</div>
      </div>
      <div class="sub-card" style="background:#f0fdf4;border-color:#16a34a;">
        <div>
          <span class="stage-num" style="background:#16a34a;color:#fff;">STAGE 3B • STUDENT</span>
          <div class="stage-name" style="margin-top:4px;font-size:13px;">Multi-Head DistilBERT (66M)</div>
          <div style="font-size:11px;color:#475569;margin-top:3px;">4 parallel classification heads trained via AdamW + Cosine LR over 5 epochs.</div>
        </div>
        <div class="stage-footer" style="font-size:10px;padding:4px;">94.85% Unseen Test Accuracy</div>
      </div>
    </div>

    <div class="conn">&rarr;</div>

    <!-- Stage 4 -->
    <div class="stage-card" style="background:#eef2ff;border-color:#4f46e5;">
      <div class="stage-top">
        <span class="stage-num" style="background:#4f46e5;color:#fff;">STAGE 4 • INFERENCE</span>
        <div class="stage-name">Batch &amp; Forensic Thinking</div>
        <ul class="stage-list">
          <li>24-Core Xeon CPU bfloat16 vector execution</li>
          <li>Softmax probability &amp; Top-2 Margin (&Delta;)</li>
          <li>Shannon Entropy H(P) flags conflicting witness clues</li>
        </ul>
      </div>
      <div class="stage-footer">18 ms Latency • Parquet Lake</div>
    </div>

    <div class="conn">&rarr;</div>

    <!-- Stage 5A / 5B -->
    <div class="split-stack">
      <div class="sub-card" style="background:#faf5ff;border-color:#7c3aed;">
        <div>
          <span class="stage-num" style="background:#7c3aed;color:#fff;">STAGE 5A • SPATIAL GNN</span>
          <div class="stage-name" style="margin-top:4px;font-size:13px;">H3 + OSMnx + CrimeSTGCN</div>
          <div style="font-size:11px;color:#475569;margin-top:3px;">Fuses H3, Census &amp; NOAA onto 29,807 Chicago &amp; 10,033 SF road intersections.</div>
        </div>
        <div class="stage-footer" style="font-size:10px;padding:4px;">31.5% Hotspot Hit Rate (630&times; Lift)</div>
      </div>
      <div class="sub-card" style="background:#fff1f2;border-color:#e11d48;">
        <div>
          <span class="stage-num" style="background:#e11d48;color:#fff;">STAGE 5B • WEB CONSOLE</span>
          <div class="stage-name" style="margin-top:4px;font-size:13px;">FastAPI + Mapbox Dashboard</div>
          <div style="font-size:11px;color:#475569;margin-top:3px;">5 interactive tabs: M.O. Matrix, Accuracy Proof, Hotspot Map, Leads &amp; PII Diff.</div>
        </div>
        <div class="stage-footer" style="font-size:10px;padding:4px;">Live Tactical Port :8008</div>
      </div>
    </div>
  </div>

  <div class="wf-bottom-bar">
    <span><strong>4 M.O. Taxonomy Heads:</strong> Weapon (98.20%) • Suspect Count (95.70%) • Point of Entry (94.40%) • Target Profile (91.10%)</span>
    <span><strong>Compliance:</strong> 100% Local CJIS / GDPR Safe</span>
  </div>
</div>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# 3. DATA FLOW DIAGRAM (Formal Level-1 DFD Notation)
# ---------------------------------------------------------------------------
DFD_HTML = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{COMMON_CSS}
.canvas {{
  width: 1120px;
  height: 480px;
  background: #ffffff;
  border: 2px solid #cbd5e1;
  border-radius: 16px;
  padding: 18px 22px;
  position: relative;
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}}
.dfd-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 8px;
}}
.dfd-title {{
  font-size: 13.5px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}}
.dfd-legend {{
  display: flex;
  gap: 14px;
  font-size: 11px;
  font-weight: 700;
  color: #334155;
  align-items: center;
}}
.leg-box {{
  display: inline-block;
  width: 16px;
  height: 12px;
  border: 2px solid #1e293b;
  background: #f1f5f9;
  vertical-align: middle;
  margin-right: 4px;
}}
.leg-proc {{
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid #2563eb;
  background: #eff6ff;
  vertical-align: middle;
  margin-right: 4px;
}}
.leg-store {{
  display: inline-block;
  width: 18px;
  height: 12px;
  border-top: 2px solid #7c3aed;
  border-bottom: 2px solid #7c3aed;
  background: #faf5ff;
  vertical-align: middle;
  margin-right: 4px;
}}
</style>
</head>
<body>
<div class="canvas">
  <div class="dfd-header">
    <div class="dfd-title">Level-1 Data Flow Diagram (DFD) — Entities, Processes &amp; Persistent Data Stores</div>
    <div class="dfd-legend">
      <span><span class="leg-box"></span>External Entity</span>
      <span><span class="leg-proc"></span>Process Node (P1–P5)</span>
      <span><span class="leg-store"></span>Data Store (D1–D4)</span>
    </div>
  </div>

  <!-- Crisp Vector SVG Data Flow Diagram -->
  <svg width="1072" height="385" viewBox="0 0 1072 385" xmlns="http://www.w3.org/2000/svg" style="font-family: 'Inter', sans-serif;">
    <defs>
      <marker id="arrow-blue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">
        <path d="M 0 1 L 10 5 L 0 9 z" fill="#2563eb"/>
      </marker>
      <marker id="arrow-slate" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">
        <path d="M 0 1 L 10 5 L 0 9 z" fill="#475569"/>
      </marker>
      <marker id="arrow-purple" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">
        <path d="M 0 1 L 10 5 L 0 9 z" fill="#7c3aed"/>
      </marker>
      <marker id="arrow-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">
        <path d="M 0 1 L 10 5 L 0 9 z" fill="#16a34a"/>
      </marker>
    </defs>

    <!-- EXTERNAL ENTITY 1: Police & CAD Sources -->
    <rect x="12" y="38" width="150" height="74" rx="6" fill="#f1f5f9" stroke="#1e293b" stroke-width="2.2"/>
    <text x="87" y="62" text-anchor="middle" font-size="11" font-weight="800" fill="#475569">EXTERNAL ENTITY</text>
    <text x="87" y="80" text-anchor="middle" font-size="13" font-weight="800" fill="#0f172a">Police &amp; CAD</text>
    <text x="87" y="97" text-anchor="middle" font-size="11.5" font-weight="600" fill="#334155">Archives (20.37M)</text>

    <!-- Arrow E1 -> P1 -->
    <line x1="162" y1="75" x2="225" y2="75" stroke="#2563eb" stroke-width="2.2" marker-end="url(#arrow-blue)"/>
    <text x="193" y="67" text-anchor="middle" font-size="10" font-weight="700" fill="#1e40af">Raw CSVs</text>

    <!-- PROCESS 1.0: Scrub PII -->
    <rect x="228" y="28" width="155" height="94" rx="45" fill="#eff6ff" stroke="#2563eb" stroke-width="2.4"/>
    <text x="305" y="53" text-anchor="middle" font-size="10.5" font-weight="800" fill="#1d4ed8">PROCESS 1.0</text>
    <text x="305" y="72" text-anchor="middle" font-size="13" font-weight="800" fill="#0f172a">Zero-PII Scrubber</text>
    <text x="305" y="89" text-anchor="middle" font-size="10.5" font-weight="600" fill="#334155">Regex + spaCy NER</text>
    <text x="305" y="104" text-anchor="middle" font-size="10" font-weight="700" fill="#0d9488">Coreference Tokens</text>

    <!-- Arrow P1 -> P3 (Top Direct Highway for 20.37M Clean Text) -->
    <path d="M 383 55 L 615 55" fill="none" stroke="#16a34a" stroke-width="2.2" marker-end="url(#arrow-green)"/>
    <rect x="440" y="38" width="135" height="18" rx="4" fill="#f0fdf4" stroke="#86efac" stroke-width="1"/>
    <text x="507" y="51" text-anchor="middle" font-size="10" font-weight="700" fill="#166534">Sanitized Stream (20.37M)</text>

    <!-- Arrow P1 -> P2 (Distillation Seed Sample) -->
    <path d="M 305 122 L 305 182" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow-slate)"/>
    <text x="355" y="156" text-anchor="middle" font-size="10" font-weight="700" fill="#334155">4,500 Seed Sample</text>

    <!-- PROCESS 2.0: Teacher-Student Distillation -->
    <rect x="218" y="185" width="175" height="92" rx="44" fill="#fffbeb" stroke="#d97706" stroke-width="2.4"/>
    <text x="305" y="210" text-anchor="middle" font-size="10.5" font-weight="800" fill="#b45309">PROCESS 2.0</text>
    <text x="305" y="229" text-anchor="middle" font-size="13" font-weight="800" fill="#0f172a">M.O. Distillation</text>
    <text x="305" y="246" text-anchor="middle" font-size="10.5" font-weight="600" fill="#334155">LLaMA-70B &rarr; DistilBERT</text>
    <text x="305" y="261" text-anchor="middle" font-size="10" font-weight="700" fill="#16a34a">94.85% Holdout Acc</text>

    <!-- DATA STORE D1: Gold Seeds (Left of P2) -->
    <line x1="12" y1="204" x2="162" y2="204" stroke="#7c3aed" stroke-width="2.5"/>
    <line x1="12" y1="260" x2="162" y2="260" stroke="#7c3aed" stroke-width="2.5"/>
    <line x1="12" y1="204" x2="12" y2="260" stroke="#7c3aed" stroke-width="2.5"/>
    <rect x="14" y="206" width="146" height="52" fill="#faf5ff"/>
    <text x="87" y="227" text-anchor="middle" font-size="11" font-weight="800" fill="#6b21a8">D1: Gold Seeds Store</text>
    <text x="87" y="245" text-anchor="middle" font-size="10.5" font-weight="600" fill="#475569">3,500 Train / 1,000 Test</text>

    <!-- Arrow P2 <-> D1 -->
    <line x1="218" y1="232" x2="165" y2="232" stroke="#7c3aed" stroke-width="2" marker-end="url(#arrow-purple)" marker-start="url(#arrow-purple)"/>

    <!-- DATA STORE D2: Student Model Weights (Right of P2) -->
    <line x1="445" y1="204" x2="595" y2="204" stroke="#7c3aed" stroke-width="2.5"/>
    <line x1="445" y1="260" x2="595" y2="260" stroke="#7c3aed" stroke-width="2.5"/>
    <line x1="445" y1="204" x2="445" y2="260" stroke="#7c3aed" stroke-width="2.5"/>
    <rect x="447" y="206" width="146" height="52" fill="#faf5ff"/>
    <text x="520" y="227" text-anchor="middle" font-size="11" font-weight="800" fill="#6b21a8">D2: Student Checkpoint</text>
    <text x="520" y="245" text-anchor="middle" font-size="10.5" font-weight="600" fill="#475569">DistilBERT 66M (model.pt)</text>

    <!-- Arrow P2 -> D2 -->
    <line x1="393" y1="232" x2="442" y2="232" stroke="#7c3aed" stroke-width="2" marker-end="url(#arrow-purple)"/>

    <!-- Arrow D2 -> P3 -->
    <path d="M 555 204 L 655 122" fill="none" stroke="#7c3aed" stroke-width="2" marker-end="url(#arrow-purple)"/>
    <text x="636" y="172" text-anchor="middle" font-size="10" font-weight="700" fill="#6b21a8">Weights</text>

    <!-- PROCESS 3.0: Multi-Head M.O. & Forensic Entropy Inference -->
    <rect x="618" y="28" width="180" height="94" rx="45" fill="#f0fdf4" stroke="#16a34a" stroke-width="2.4"/>
    <text x="708" y="52" text-anchor="middle" font-size="10.5" font-weight="800" fill="#15803d">PROCESS 3.0</text>
    <text x="708" y="71" text-anchor="middle" font-size="13" font-weight="800" fill="#0f172a">M.O. &amp; Entropy Engine</text>
    <text x="708" y="88" text-anchor="middle" font-size="10.5" font-weight="600" fill="#334155">4 Heads + Softmax + H(P)</text>
    <text x="708" y="103" text-anchor="middle" font-size="10" font-weight="700" fill="#15803d">1,285 rec/s • 18 ms Live</text>

    <!-- DATA STORE D3: Enriched Parquet Data Lake -->
    <line x1="860" y1="46" x2="1055" y2="46" stroke="#7c3aed" stroke-width="2.5"/>
    <line x1="860" y1="104" x2="1055" y2="104" stroke="#7c3aed" stroke-width="2.5"/>
    <line x1="860" y1="46" x2="860" y2="104" stroke="#7c3aed" stroke-width="2.5"/>
    <rect x="862" y="48" width="191" height="54" fill="#faf5ff"/>
    <text x="957" y="70" text-anchor="middle" font-size="11.5" font-weight="800" fill="#6b21a8">D3: Enriched Parquet Lake</text>
    <text x="957" y="88" text-anchor="middle" font-size="10.5" font-weight="600" fill="#475569">20.37M M.O.-Tagged Records</text>

    <!-- Arrow P3 -> D3 -->
    <line x1="798" y1="75" x2="857" y2="75" stroke="#16a34a" stroke-width="2.2" marker-end="url(#arrow-green)"/>
    <text x="828" y="66" text-anchor="middle" font-size="10" font-weight="700" fill="#166534">M.O. Vectors</text>

    <!-- EXTERNAL ENTITY 2: GIS, Census, NOAA & OSM -->
    <rect x="12" y="300" width="175" height="70" rx="6" fill="#f1f5f9" stroke="#1e293b" stroke-width="2.2"/>
    <text x="99" y="322" text-anchor="middle" font-size="10.5" font-weight="800" fill="#475569">EXTERNAL ENTITY</text>
    <text x="99" y="340" text-anchor="middle" font-size="12.5" font-weight="800" fill="#0f172a">OSMnx, Census &amp; NOAA</text>
    <text x="99" y="356" text-anchor="middle" font-size="10.5" font-weight="600" fill="#334155">Road Graphs, Tracts &amp; Weather</text>

    <!-- PROCESS 4.0: Spatial Fusion & CrimeSTGCN -->
    <rect x="618" y="185" width="180" height="92" rx="44" fill="#eef2ff" stroke="#4f46e5" stroke-width="2.4"/>
    <text x="708" y="209" text-anchor="middle" font-size="10.5" font-weight="800" fill="#4338ca">PROCESS 4.0</text>
    <text x="708" y="228" text-anchor="middle" font-size="13" font-weight="800" fill="#0f172a">Spatial &amp; ST-GCN</text>
    <text x="708" y="245" text-anchor="middle" font-size="10.5" font-weight="600" fill="#334155">Uber H3 + Road GraphConv</text>
    <text x="708" y="260" text-anchor="middle" font-size="10" font-weight="700" fill="#4338ca">31.5% Top-15 Hit Rate</text>

    <!-- Arrow E2 -> P4 -->
    <path d="M 187 335 L 650 335 L 675 280" fill="none" stroke="#475569" stroke-width="2" marker-end="url(#arrow-slate)"/>
    <text x="415" y="327" text-anchor="middle" font-size="10.5" font-weight="700" fill="#334155">Street Topology (29,807 Chicago / 10,033 SF Nodes) + Weather + Tracts</text>

    <!-- Arrow D3 -> P4 -->
    <path d="M 920 104 L 785 188" fill="none" stroke="#7c3aed" stroke-width="2" marker-end="url(#arrow-purple)"/>

    <!-- DATA STORE D4: PyG Road Graph Tensors -->
    <line x1="860" y1="202" x2="1055" y2="202" stroke="#7c3aed" stroke-width="2.5"/>
    <line x1="860" y1="260" x2="1055" y2="260" stroke="#7c3aed" stroke-width="2.5"/>
    <line x1="860" y1="202" x2="860" y2="260" stroke="#7c3aed" stroke-width="2.5"/>
    <rect x="862" y="204" width="191" height="54" fill="#faf5ff"/>
    <text x="957" y="226" text-anchor="middle" font-size="11.5" font-weight="800" fill="#6b21a8">D4: PyG Graph Tensors</text>
    <text x="957" y="244" text-anchor="middle" font-size="10.5" font-weight="600" fill="#475569">ST-GCN Weights &amp; Risk Maps</text>

    <!-- Arrow P4 <-> D4 -->
    <line x1="798" y1="231" x2="857" y2="231" stroke="#7c3aed" stroke-width="2" marker-end="url(#arrow-purple)" marker-start="url(#arrow-purple)"/>

    <!-- PROCESS 5.0: FastAPI Tactical Web Console -->
    <rect x="858" y="296" width="196" height="76" rx="12" fill="#fff1f2" stroke="#e11d48" stroke-width="2.4"/>
    <text x="956" y="318" text-anchor="middle" font-size="10.5" font-weight="800" fill="#be123c">PROCESS 5.0 • PORT :8008</text>
    <text x="956" y="337" text-anchor="middle" font-size="13" font-weight="800" fill="#0f172a">FastAPI Tactical Console</text>
    <text x="956" y="354" text-anchor="middle" font-size="10.5" font-weight="600" fill="#334155">M.O., Hotspots, Leads &amp; PII Audit</text>

    <!-- Arrow D4 -> P5 & P3 -> P5 -->
    <line x1="956" y1="260" x2="956" y2="293" stroke="#2563eb" stroke-width="2.2" marker-end="url(#arrow-blue)"/>
    <path d="M 745 122 L 870 296" fill="none" stroke="#16a34a" stroke-width="2" stroke-dasharray="4,3" marker-end="url(#arrow-green)"/>
  </svg>
</div>
</body>
</html>
"""

def render_html_to_png(page, html_str: str, width: int, height: int, filename: str):
    page.set_viewport_size({"width": width, "height": height})
    page.set_content(html_str, wait_until="load")
    out1 = OUT_DIR / filename
    out2 = ARTIFACT_DIR / filename
    page.screenshot(path=str(out1), omit_background=True)
    page.screenshot(path=str(out2), omit_background=True)
    print(f"Rendered {filename} ({out1.stat().st_size} bytes)")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(device_scale_factor=2.5)
        page = context.new_page()

        render_html_to_png(page, FLOWCHART_HTML, 1120, 560, "diagram_1_flowchart.png")
        render_html_to_png(page, WORKFLOW_HTML, 1120, 480, "diagram_2_workflow.png")
        render_html_to_png(page, DFD_HTML, 1120, 480, "diagram_3_dfd.png")

        browser.close()

if __name__ == "__main__":
    main()
