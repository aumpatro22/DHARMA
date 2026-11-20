import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    # 16:9 Widescreen dimensions
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6] # Blank slide layout

    # Color Palette (Dark High-Tech Forensic Theme)
    BG_COLOR = RGBColor(15, 23, 42)       # Slate 900
    CARD_BG = RGBColor(30, 41, 59)        # Slate 800
    CARD_BORDER = RGBColor(51, 65, 85)    # Slate 700
    ACCENT_CYAN = RGBColor(56, 189, 248)  # Cyan 400
    ACCENT_BLUE = RGBColor(99, 102, 241)  # Indigo 500
    ACCENT_GREEN = RGBColor(52, 211, 153) # Emerald 400
    TEXT_WHITE = RGBColor(248, 250, 252)  # Slate 50
    TEXT_MUTED = RGBColor(148, 163, 184)  # Slate 400
    TEXT_GOLD = RGBColor(251, 191, 36)    # Amber 400

    def set_slide_background(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_COLOR
        bg.line.color.rgb = BG_COLOR
        return bg

    def add_header(slide, title_text, category_text="PROJECT D.H.A.R.M.A. | CRIME PATTERN DETECTION"):
        # Category label
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = ACCENT_CYAN
        p_cat.font.name = "Arial"

        # Main Slide Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.6))
        tf = title_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.size = Pt(24)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        p.font.name = "Arial"

    def add_card(slide, left, top, width, height, title=None, border_color=CARD_BORDER, bg_color=CARD_BG):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1.5)

        if title:
            tb = slide.shapes.add_textbox(Inches(left + 0.2), Inches(top + 0.15), Inches(width - 0.4), Inches(0.4))
            tf = tb.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = title
            p.font.size = Pt(14)
            p.font.bold = True
            p.font.color.rgb = ACCENT_CYAN
            p.font.name = "Arial"

        return card

    # =========================================================================
    # SLIDE 1: TITLE SLIDE
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)

    # Accent decorative banner
    banner = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.8), Inches(11.733), Inches(5.9))
    banner.fill.solid()
    banner.fill.fore_color.rgb = CARD_BG
    banner.line.color.rgb = ACCENT_BLUE
    banner.line.width = Pt(2)

    # Badge
    badge = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.3), Inches(1.3), Inches(4.2), Inches(0.45))
    badge.fill.solid()
    badge.fill.fore_color.rgb = RGBColor(49, 46, 129)
    badge.line.color.rgb = ACCENT_CYAN
    badge_tf = badge.text_frame
    bp = badge_tf.paragraphs[0]
    bp.alignment = PP_ALIGN.CENTER
    bp.text = "NATIONAL CRIME PATTERN DETECTION PLATFORM"
    bp.font.size = Pt(10)
    bp.font.bold = True
    bp.font.color.rgb = ACCENT_CYAN

    # Title
    t_box = s1.shapes.add_textbox(Inches(1.3), Inches(1.9), Inches(10.7), Inches(1.5))
    tf1 = t_box.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "PROJECT D.H.A.R.M.A."
    p1.font.size = Pt(38)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_WHITE
    p1.font.name = "Arial"

    p2 = tf1.add_paragraph()
    p2.text = "Dynamic Hierarchical Anonymized Real-Time Modus-Operandi Analytics"
    p2.font.size = Pt(17)
    p2.font.color.rgb = ACCENT_CYAN
    p2.font.name = "Arial"

    # Subtitle / Abstract
    desc_box = s1.shapes.add_textbox(Inches(1.3), Inches(3.5), Inches(10.7), Inches(1.1))
    tf_desc = desc_box.text_frame
    tf_desc.word_wrap = True
    pd = tf_desc.paragraphs[0]
    pd.text = "A privacy-preserving AI framework integrating zero-PII knowledge distillation, multi-task DistilBERT classification, high-throughput 20M+ batch inference, and spatiotemporal graph topology for forensic crime detection."
    pd.font.size = Pt(13)
    pd.font.color.rgb = TEXT_MUTED
    pd.font.name = "Arial"

    # Team Members Footer Box
    team_box = s1.shapes.add_textbox(Inches(1.3), Inches(4.8), Inches(10.7), Inches(1.5))
    tf_team = team_box.text_frame
    tf_team.word_wrap = True
    pt_h = tf_team.paragraphs[0]
    pt_h.text = "CORE PROJECT TEAM & ARCHITECTURE ROLES:"
    pt_h.font.size = Pt(12)
    pt_h.font.bold = True
    pt_h.font.color.rgb = TEXT_GOLD

    pt1 = tf_team.add_paragraph()
    pt1.text = "• Aum Patro — Chief ML/NLP Architect & Privacy Pipeline Engineer (PII Engine, DistilBERT Distillation & 20M Batch Streaming)"
    pt1.font.size = Pt(11)
    pt1.font.color.rgb = TEXT_WHITE

    pt2 = tf_team.add_paragraph()
    pt2.text = "• Ashoutosh Mohanty — Geospatial Analytics & GNN Engineer (H3 Indexing, Census Joins, Weather & OSMnx Road Graph Builder)"
    pt2.font.size = Pt(11)
    pt2.font.color.rgb = TEXT_WHITE

    pt3 = tf_team.add_paragraph()
    pt3.text = "• Sai Dhanush — Full-Stack CAD Ingestion & Operations Engineer (Real-Time CAD Stream, Qdrant Retrieval & Command Dashboard)"
    pt3.font.size = Pt(11)
    pt3.font.color.rgb = TEXT_WHITE

    # =========================================================================
    # SLIDE 2: PROBLEM STATEMENT & MOTIVATION
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "Problem Statement & Industry Challenges")

    # 3 Column Cards
    col_w = 3.65
    gap = 0.38
    start_x = 0.8
    y_top = 1.5
    c_h = 5.2

    # Card 1: Data Silos & PII Risks
    add_card(s2, start_x, y_top, col_w, c_h, "1. Privacy & Data Silos")
    tb = s2.shapes.add_textbox(Inches(start_x + 0.2), Inches(y_top + 0.6), Inches(col_w - 0.4), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "• Strict CJIS Privacy Mandates:\nLaw enforcement agencies are legally restricted from sending raw citizen and officer PII (names, badges, phone numbers, addresses) to third-party cloud LLMs.\n\n• Inter-Agency Data Silos:\nPolice departments (NYPD, LAPD, UK) maintain isolated databases, preventing automated tracking of cross-border serial criminal patterns."
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_MUTED

    # Card 2: Scale & Latency Bottlenecks
    add_card(s2, start_x + col_w + gap, y_top, col_w, c_h, "2. Scale & Cost Bottlenecks")
    tb = s2.shapes.add_textbox(Inches(start_x + col_w + gap + 0.2), Inches(y_top + 0.6), Inches(col_w - 0.4), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "• Massive Dataset Volume:\nNational historical archives exceed 20+ million records. Calling commercial cloud LLM APIs at this scale costs hundreds of thousands of dollars and hits strict rate limits (HTTP 429).\n\n• Unacceptable Latency:\nEmergency dispatchers require real-time narrative inference in <15ms, impossible with multi-second cloud API calls."
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_MUTED

    # Card 3: Missing Spatial-Environmental Context
    add_card(s2, start_x + (col_w + gap) * 2, y_top, col_w, c_h, "3. Environmental Isolation")
    tb = s2.shapes.add_textbox(Inches(start_x + (col_w + gap) * 2 + 0.2), Inches(y_top + 0.6), Inches(col_w - 0.4), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "• Disconnected Spatial Analysis:\nConventional crime analytics treat incident coordinates as simple point pins without considering physical road networks, escape choke-points, or transit proximity.\n\n• Omission of Weather Dynamics:\nCrime variations linked to micro-climate variables (precipitation, extreme heat) are typically omitted from predictive risk algorithms."
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 3: SYSTEM ARCHITECTURE & PIPELINE
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "System Architecture: End-to-End Pipeline Flow")

    # 4 Architecture Stage Cards
    s_w = 2.7
    s_gap = 0.3
    s_top = 1.5
    s_h = 5.2

    stages = [
        ("STAGE 1: PRIVACY", "Local PII Scrubbing Engine", "local_anonymizer.py", [
            "Hybrid Regex + spaCy NER",
            "Zero cloud PII transmission",
            "Deterministic coreference mapping (PERSON_Alpha_01)",
            "Preserves grammatical syntax for downstream NLP"
        ]),
        ("STAGE 2: DISTILLATION", "Teacher-Student Distillation", "groq_mo_extractor.py & train_student_model.py", [
            "Teacher: Groq LPU LLaMA 3.3-70B",
            "Gold Seed ground truth (2,000 samples)",
            "Multi-Head DistilBERT fine-tuning",
            "100.0% validation accuracy across all 4 M.O. targets"
        ]),
        ("STAGE 3: BATCH ENGINE", "National Streaming Parquet", "batch_infer_student_maxram.py", [
            "24-core Intel Xeon CPU optimization",
            "Intel AMX bfloat16 mixed-precision",
            "Streaming 1M chunk execution",
            "20.37M records processed @ 1,285 recs/sec"
        ]),
        ("STAGE 4: GEOSPATIAL", "Spatial & Graph Fusion", "spatial_fuser.py & network_graph_builder.py", [
            "Uber H3 Indexing (Res 7 & 8)",
            "Census Tract/Block Group joins",
            "NOAA weather & transit KDTree",
            "OSMnx Road Graph PyG tensors (.pt)"
        ])
    ]

    for idx, (badge_t, title_t, file_t, bullets) in enumerate(stages):
        x = start_x + idx * (s_w + s_gap)
        add_card(s3, x, s_top, s_w, s_h, title_t)
        
        # Badge
        b = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x + 0.15), Inches(s_top + 0.12), Inches(s_w - 0.3), Inches(0.3))
        b.fill.solid()
        b.fill.fore_color.rgb = RGBColor(49, 46, 129)
        b.line.color.rgb = ACCENT_CYAN
        btf = b.text_frame
        bp = btf.paragraphs[0]
        bp.alignment = PP_ALIGN.CENTER
        bp.text = badge_t
        bp.font.size = Pt(8.5)
        bp.font.bold = True
        bp.font.color.rgb = ACCENT_CYAN

        # Subtitle File
        tb_f = s3.shapes.add_textbox(Inches(x + 0.15), Inches(s_top + 0.8), Inches(s_w - 0.3), Inches(0.4))
        tf_f = tb_f.text_frame
        tf_f.word_wrap = True
        pf = tf_f.paragraphs[0]
        pf.text = f"File: {file_t}"
        pf.font.size = Pt(9.5)
        pf.font.color.rgb = TEXT_GOLD

        # Bullets
        tb_b = s3.shapes.add_textbox(Inches(x + 0.15), Inches(s_top + 1.3), Inches(s_w - 0.3), Inches(3.7))
        tf_b = tb_b.text_frame
        tf_b.word_wrap = True
        tf_b.margin_left = Inches(0.05)
        for b_idx, bullet in enumerate(bullets):
            p = tf_b.paragraphs[0] if b_idx == 0 else tf_b.add_paragraph()
            p.text = f"• {bullet}"
            p.font.size = Pt(11)
            p.font.color.rgb = TEXT_MUTED
            p.space_after = Pt(8)

    # =========================================================================
    # SLIDE 4: PRIVACY ENGINE & COREFERENCE SCRUBBING
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "Privacy Engine: Zero-PII Scrubbing & Coreference Preservation")

    # Left: Methodology Box
    add_card(s4, 0.8, 1.5, 5.6, 5.2, "Dual-Stage Anonymization Architecture")
    tb4_l = s4.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(5.2), Inches(4.4))
    tf4_l = tb4_l.text_frame
    tf4_l.word_wrap = True
    
    p = tf4_l.paragraphs[0]
    p.text = "1. Regex Structured Identifier Pre-Pass:"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN

    p = tf4_l.add_paragraph()
    p.text = "Scans and replaces high-entropy structured identifiers: US/UK Phone Numbers, Police Badge IDs, Vehicle License Plates, and exact Street Addresses with Greek-alphabet indexing."
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_MUTED

    p = tf4_l.add_paragraph()
    p.text = "\n2. spaCy Named Entity Recognition (NER):"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN

    p = tf4_l.add_paragraph()
    p.text = "Identifies person names, victim names, suspect aliases, and commercial entities using a custom English transformer pipeline."
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_MUTED

    p = tf4_l.add_paragraph()
    p.text = "\n3. Deterministic Coreference Entity Mapping:"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN

    p = tf4_l.add_paragraph()
    p.text = "Repeated mentions of the same individual are mapped to identical tokens (e.g. PERSON_Alpha_01), preserving actor-victim roles for downstream M.O. classification."
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_MUTED

    # Right: Before/After Transformation Card
    add_card(s4, 6.7, 1.5, 5.8, 5.2, "Narrative Sanitization Example")
    tb4_r = s4.shapes.add_textbox(Inches(6.9), Inches(2.1), Inches(5.4), Inches(4.4))
    tf4_r = tb4_r.text_frame
    tf4_r.word_wrap = True

    p = tf4_r.paragraphs[0]
    p.text = "RAW INCIDENT NARRATIVE (BEFORE):"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = RGBColor(239, 68, 68) # Red

    p = tf4_r.add_paragraph()
    p.text = '\"On 2026-07-15, Officer Michael Johnson (Badge #4821) responded to Walmart at 1044 Market St. Store manager David Brown reported that suspect James Smith smashed the rear window with a crowbar and stole cash. Phone: 415-555-0192.\"'
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_MUTED

    p = tf4_r.add_paragraph()
    p.text = "\nSANITIZED ZERO-PII NARRATIVE (AFTER):"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN

    p = tf4_r.add_paragraph()
    p.text = '\"On [DATE_01], Officer PERSON_Alpha_01 (BADGE_01) responded to STORE_01 at ADDRESS_01. Store manager PERSON_Beta_01 reported that suspect PERSON_Gamma_01 smashed the rear window with a crowbar and stole cash. Phone: PHONE_01.\"'
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_MUTED

    p = tf4_r.add_paragraph()
    p.text = "\n✅ Result: 0% PII Leakage | 100% Coreference & Grammatical Integrity"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = TEXT_GOLD

    # =========================================================================
    # SLIDE 5: TEACHER-STUDENT DISTILLATION & MODEL RESULTS
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "Teacher-Student Distillation & Multi-Head Classification")

    # Left: Multi-Head Taxonomy Schema
    add_card(s5, 0.8, 1.5, 5.6, 5.2, "4-Head Modus Operandi Taxonomy")
    tb5_l = s5.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(5.2), Inches(4.4))
    tf5_l = tb5_l.text_frame
    tf5_l.word_wrap = True

    p = tf5_l.paragraphs[0]
    p.text = "1. Weapon Classification (6 classes):"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    p = tf5_l.add_paragraph()
    p.text = "• FIREARM, BLADED, BLUNT_FORCE, MELEE_OTHER, NONE, UNKNOWN"
    p.font.size = Pt(10.5)
    p.font.color.rgb = TEXT_MUTED

    p = tf5_l.add_paragraph()
    p.text = "\n2. Point of Entry (7 classes):"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    p = tf5_l.add_paragraph()
    p.text = "• FRONT_DOOR, REAR_DOOR, WINDOW, GARAGE, ROOF_VENT, NOT_APPLICABLE, UNKNOWN"
    p.font.size = Pt(10.5)
    p.font.color.rgb = TEXT_MUTED

    p = tf5_l.add_paragraph()
    p.text = "\n3. Target Profile (6 classes):"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    p = tf5_l.add_paragraph()
    p.text = "• COMMERCIAL, RESIDENTIAL, INDIVIDUAL, VEHICLE, INFRASTRUCTURE, UNKNOWN"
    p.font.size = Pt(10.5)
    p.font.color.rgb = TEXT_MUTED

    p = tf5_l.add_paragraph()
    p.text = "\n4. Suspect Count Estimate (4 classes):"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    p = tf5_l.add_paragraph()
    p.text = "• SOLO (1), PAIR (2), GROUP (3+), UNKNOWN"
    p.font.size = Pt(10.5)
    p.font.color.rgb = TEXT_MUTED

    # Right: Training Performance Table Card
    add_card(s5, 6.7, 1.5, 5.8, 5.2, "DistilBERT Student Fine-Tuning Performance")
    
    # Table inside right card
    rows, cols = 6, 4
    t_left, t_top, t_w, t_h = Inches(6.9), Inches(2.2), Inches(5.4), Inches(2.8)
    table_shape = s5.shapes.add_table(rows, cols, t_left, t_top, t_w, t_h)
    table = table_shape.table
    table.columns[0].width = Inches(1.1)
    table.columns[1].width = Inches(1.4)
    table.columns[2].width = Inches(1.4)
    table.columns[3].width = Inches(1.5)

    headers = ["Epoch", "Train Loss", "Val Loss", "Val Accuracy"]
    for c_idx, h in enumerate(headers):
        cell = table.cell(0, c_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(49, 46, 129)
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_CYAN
        p.alignment = PP_ALIGN.CENTER

    data = [
        ["Epoch 1", "5.4275", "3.1878", "81.39%"],
        ["Epoch 2", "2.3081", "1.2111", "100.0%"],
        ["Epoch 3", "1.0855", "0.5900", "100.0%"],
        ["Epoch 4", "0.6327", "0.3796", "100.0%"],
        ["Epoch 5", "0.4845", "0.3278", "100.0%"]
    ]
    for r_idx, row in enumerate(data):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx + 1, c_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_BG if r_idx % 2 == 0 else RGBColor(20, 29, 46)
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(10)
            p.font.color.rgb = TEXT_GOLD if c_idx == 3 else TEXT_WHITE
            p.alignment = PP_ALIGN.CENTER

    tb5_sub = s5.shapes.add_textbox(Inches(6.9), Inches(5.3), Inches(5.4), Inches(1.2))
    tf5_sub = tb5_sub.text_frame
    tf5_sub.word_wrap = True
    p = tf5_sub.paragraphs[0]
    p.text = "⚡ Hardware Optimization: Intel Xeon 24-core CPU (OMP/MKL threads = 24). Fast local convergence with 0% cloud inference cost and sub-millisecond per-sample execution."
    p.font.size = Pt(10.5)
    p.font.color.rgb = ACCENT_GREEN

    # =========================================================================
    # SLIDE 6: HIGH-THROUGHPUT NATIONAL BATCH INFERENCE
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, "High-Throughput National Batch Streaming (20.37M Records)")

    # Full Width Table Card
    add_card(s6, 0.8, 1.5, 11.7, 5.2, "National-Scale Parquet Dataset Ingestion Metrics")

    rows, cols = 7, 6
    t_left, t_top, t_w, t_h = Inches(1.0), Inches(2.2), Inches(11.3), Inches(3.2)
    table_shape = s6.shapes.add_table(rows, cols, t_left, t_top, t_w, t_h)
    table = table_shape.table
    table.columns[0].width = Inches(1.0)
    table.columns[1].width = Inches(2.8)
    table.columns[2].width = Inches(1.8)
    table.columns[3].width = Inches(1.8)
    table.columns[4].width = Inches(2.3)
    table.columns[5].width = Inches(1.6)

    h_list = ["Stage", "National Dataset", "Total Records", "Throughput", "Output Parquet Matrix", "Status"]
    for c_idx, h in enumerate(h_list):
        cell = table.cell(0, c_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(49, 46, 129)
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_CYAN
        p.alignment = PP_ALIGN.CENTER

    batch_data = [
        ["Stage 1", "NYPD Historical Arrests", "5,986,025 rows", "714.2 recs/s", "nypd_mo_full.parquet (237.8 MB)", "COMPLETED"],
        ["Stage 2", "UK National Police Forces", "9,720,395 rows", "1,285.8 recs/s", "uk_mo_full.parquet (711.0 MB)", "COMPLETED"],
        ["Stage 3", "LAPD Crime Data", "3,138,335 rows", "122.6 recs/s", "lapd_mo_full.parquet (132.9 MB)", "COMPLETED"],
        ["Stage 4", "Houston NIBRS Logs", "1,526,084 rows", "737.3 recs/s", "houston_mo_full.parquet (38.0 MB)", "COMPLETED"],
        ["Stage 5", "San Francisco Crimes", "10,000 rows", "450.0 recs/s", "sf_fused_matrix.parquet (630 KB)", "COMPLETED"],
        ["Stage 6", "Chicago Crimes", "10,000 rows", "480.0 recs/s", "chicago_fused_matrix.parquet (668 KB)", "COMPLETED"]
    ]
    for r_idx, row in enumerate(batch_data):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx + 1, c_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_BG if r_idx % 2 == 0 else RGBColor(20, 29, 46)
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(10)
            p.alignment = PP_ALIGN.CENTER if c_idx in [0, 2, 3, 5] else PP_ALIGN.LEFT
            if c_idx == 5:
                p.font.bold = True
                p.font.color.rgb = ACCENT_GREEN
            elif c_idx == 2:
                p.font.color.rgb = TEXT_GOLD
            else:
                p.font.color.rgb = TEXT_WHITE

    tb6_foot = s6.shapes.add_textbox(Inches(1.0), Inches(5.6), Inches(11.3), Inches(0.9))
    tf6_foot = tb6_foot.text_frame
    tf6_foot.word_wrap = True
    p = tf6_foot.paragraphs[0]
    p.text = "🎯 Cumulative Ingestion Milestone: 20,373,839 Total Records Processed. PyArrow Parquet streaming in 1,000,000-row chunks + Intel AMX bfloat16 execution bounded RAM consumption strictly below 18 GB with zero memory leaks."
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN

    # =========================================================================
    # SLIDE 7: GEOSPATIAL & ROAD NETWORK GRAPH FUSION
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, "Geospatial-Environmental & Road Network Graph Fusion")

    # Left: Spatial Fuser
    add_card(s7, 0.8, 1.5, 5.6, 5.2, "Spatial & Environmental Fusion Engine")
    tb7_l = s7.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(5.2), Inches(4.4))
    tf7_l = tb7_l.text_frame
    tf7_l.word_wrap = True

    p = tf7_l.paragraphs[0]
    p.text = "1. Uber H3 Spatial Indexing (Res 7 & 8):"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    p = tf7_l.add_paragraph()
    p.text = "Converts irregular GPS coordinates into uniform hexagonal spatial bins for fast O(1) spatial aggregation and neighbor queries."
    p.font.size = Pt(10.5)
    p.font.color.rgb = TEXT_MUTED

    p = tf7_l.add_paragraph()
    p.text = "\n2. US Census Bureau Point-in-Polygon Joins:"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    p = tf7_l.add_paragraph()
    p.text = "Offline GeoJSON cache mapping for Census Tracts and Block Groups to append demographic and jurisdictional boundaries."
    p.font.size = Pt(10.5)
    p.font.color.rgb = TEXT_MUTED

    p = tf7_l.add_paragraph()
    p.text = "\n3. NOAA Weather & Transit Proximity:"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    p = tf7_l.add_paragraph()
    p.text = "Fuses precipitation, max/min temp, and metric Euclidean distance to the nearest transit stop via SciPy KDTree."
    p.font.size = Pt(10.5)
    p.font.color.rgb = TEXT_MUTED

    # Right: OSMnx Road Graph Builder
    add_card(s7, 6.7, 1.5, 5.8, 5.2, "OSMnx Road Graph & Centrality Extraction")
    tb7_r = s7.shapes.add_textbox(Inches(6.9), Inches(2.1), Inches(5.4), Inches(4.4))
    tf7_r = tb7_r.text_frame
    tf7_r.word_wrap = True

    p = tf7_r.paragraphs[0]
    p.text = "1. OpenStreetMap Topology Extraction:"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    p = tf7_r.add_paragraph()
    p.text = "Downloads drivable street graphs via OSMnx, simplified and projected to UTM coordinates with metric edge lengths."
    p.font.size = Pt(10.5)
    p.font.color.rgb = TEXT_MUTED

    p = tf7_r.add_paragraph()
    p.text = "\n2. Topological Choke-Point Centrality:"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    p = tf7_r.add_paragraph()
    p.text = "Calculates Betweenness Centrality and Degree Centrality for intersection nodes, isolating escape corridors and urban bottlenecks."
    p.font.size = Pt(10.5)
    p.font.color.rgb = TEXT_MUTED

    p = tf7_r.add_paragraph()
    p.text = "\n3. PyTorch Geometric Tensor Export:"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    p = tf7_r.add_paragraph()
    p.text = "Exports graph_chicago.pt and graph_sf.pt PyG Data objects with node feature matrices, ready for Spatiotemporal GNN modeling."
    p.font.size = Pt(10.5)
    p.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 8: ENGINEERING CHALLENGES & RESOLUTIONS
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, "Key Engineering Challenges & Applied Solutions")

    add_card(s8, 0.8, 1.5, 11.7, 5.2, "Incident Log & Architectural Resolutions")

    rows, cols = 6, 3
    t_left, t_top, t_w, t_h = Inches(1.0), Inches(2.2), Inches(11.3), Inches(4.2)
    table_shape = s8.shapes.add_table(rows, cols, t_left, t_top, t_w, t_h)
    table = table_shape.table
    table.columns[0].width = Inches(2.6)
    table.columns[1].width = Inches(4.3)
    table.columns[2].width = Inches(4.4)

    h_list = ["Hurdle / Issue Key", "Technical Bottleneck Encountered", "Applied Engineering Resolution"]
    for c_idx, h in enumerate(h_list):
        cell = table.cell(0, c_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(49, 46, 129)
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_CYAN
        p.alignment = PP_ALIGN.CENTER

    issues_data = [
        ["CRI-1001: Cloud API Latency & Cost", "Calling cloud LLMs for 20.37M records incurs massive API costs and HTTP 429 throttling.", "Built Teacher-Student distillation; fine-tuned 4-head DistilBERT student running offline on CPU @ 1,285 recs/s."],
        ["CRI-1002: PII Redaction Context Loss", "Generic [REDACTED] masking destroys syntax and confuses suspect vs. victim roles.", "Implemented Regex + spaCy coreference mapping (PERSON_Alpha_01, BADGE_01) preserving narrative grammar."],
        ["CRI-1003: Memory OOM on 9.7M Dataset", "Monolithic CSV parsing in pandas exceeded RAM and caused system kernel crashes.", "Engineered PyArrow Parquet streaming in 1M chunks with Intel AMX bfloat16, keeping RAM under 18 GB."],
        ["CRI-1004: Census Polygon Latencies", "Real-time shapefile queries against census servers caused timeouts and high CPU latency.", "Created offline GeoJSON caching, integrated Uber H3 indexing, and parallelized queries across 24 Xeon workers."],
        ["CRI-1005: SIGHUP Terminal Disconnects", "SSH disconnects terminated multi-hour background batch extraction jobs prematurely.", "Built run_unattended_pipeline.sh trapping SIGHUP with atomic chunk checkpoints and live Markdown logbooks."]
    ]
    for r_idx, row in enumerate(issues_data):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx + 1, c_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_BG if r_idx % 2 == 0 else RGBColor(20, 29, 46)
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(9.5)
            p.alignment = PP_ALIGN.LEFT
            if c_idx == 0:
                p.font.bold = True
                p.font.color.rgb = TEXT_GOLD
            elif c_idx == 2:
                p.font.color.rgb = ACCENT_GREEN
            else:
                p.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 9: TEAM ROLES & PROJECT MANAGEMENT
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_header(s9, "Team Roles, Individual Contributions & Freedcamp Tracking")

    # 3 Column Team Cards
    team_members = [
        ("Aum Patro", "Chief ML/NLP Architect & Privacy Engineer", "Module: Privacy Engine & Distillation", [
            "Engineered local_anonymizer.py zero-PII coreference engine",
            "Extracted Groq LPU LLaMA 3.3-70B gold seed dataset",
            "Fine-tuned 4-head DistilBERT model to 100% val accuracy",
            "Executed 20.37M national streaming batch inference",
            "Freedcamp: Tasks #72940053, #72940055, #72940056, #72940057"
        ]),
        ("Ashoutosh Mohanty", "Geospatial Analytics & GNN Engineer", "Module: Spatial Fuser & Road Graph Builder", [
            "Implemented Uber H3 hexagonal indexing (Res 7 & 8)",
            "Integrated US Census Tract and Block Group joins",
            "Fused NOAA historical weather & transit stop distance",
            "Extracted OSMnx road topology & PyTorch Geometric tensors",
            "Freedcamp: Tasks #72940058, #72940059"
        ]),
        ("Sai Dhanush", "Full-Stack CAD Ingestion & Operations Engineer", "Module: Real-Time CAD & Dashboard UI", [
            "Architecting sub-15ms FastAPI CAD stream microservice",
            "Integrated Qdrant vector database for M.O. embeddings",
            "Building cross-jurisdiction serial pattern alert triggers",
            "Developing interactive Mapbox / Deck.gl Command Center UI",
            "Freedcamp: Tasks #72940062, #72940063, #72940064, #72940065"
        ])
    ]

    for idx, (name, role, module, achievements) in enumerate(team_members):
        x = start_x + idx * (col_w + gap)
        add_card(s9, x, y_top, col_w, c_h, name)

        tb_r = s9.shapes.add_textbox(Inches(x + 0.2), Inches(y_top + 0.5), Inches(col_w - 0.4), Inches(0.55))
        tf_r = tb_r.text_frame
        tf_r.word_wrap = True
        pr = tf_r.paragraphs[0]
        pr.text = role
        pr.font.size = Pt(10.5)
        pr.font.bold = True
        pr.font.color.rgb = TEXT_GOLD

        pr2 = tf_r.add_paragraph()
        pr2.text = module
        pr2.font.size = Pt(9.5)
        pr2.font.color.rgb = ACCENT_CYAN

        tb_ach = s9.shapes.add_textbox(Inches(x + 0.2), Inches(y_top + 1.2), Inches(col_w - 0.4), Inches(3.8))
        tf_ach = tb_ach.text_frame
        tf_ach.word_wrap = True
        for a_idx, ach in enumerate(achievements):
            p = tf_ach.paragraphs[0] if a_idx == 0 else tf_ach.add_paragraph()
            p.text = f"• {ach}"
            p.font.size = Pt(10)
            p.font.color.rgb = TEXT_MUTED
            p.space_after = Pt(6)

    # =========================================================================
    # SLIDE 10: FUTURE ROADMAP & CONCLUSION
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10)
    add_header(s10, "Future Roadmap & Project Conclusion")

    # Left: Roadmap Items
    add_card(s10, 0.8, 1.5, 6.6, 5.2, "Next Development Phases (Q4 2026)")
    tb10_l = s10.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(6.2), Inches(4.4))
    tf10_l = tb10_l.text_frame
    tf10_l.word_wrap = True

    phases = [
        ("Phase 1: Spatiotemporal GNN Model Training", "Train ST-GCN / A3T-GCN models on generated road graphs to predict 24-hour localized crime risk heatmaps."),
        ("Phase 2: Real-Time CAD Stream FastAPI Ingestion", "Deploy containerized sub-15ms inference microservice for live 911 dispatch audio/narrative streams."),
        ("Phase 3: Qdrant Vector Cross-Jurisdiction Matching", "Scale Qdrant vector retrieval for identifying multi-state serial burglary and armed robbery patterns."),
        ("Phase 4: Mapbox / Deck.gl Operational Command Center", "Deliver interactive operational dashboard with time-sliders, risk polygons, and automated intelligence export.")
    ]
    for p_title, p_desc in phases:
        p = tf10_l.add_paragraph() if tf10_l.paragraphs[0].text else tf10_l.paragraphs[0]
        p.text = f"🚀 {p_title}:"
        p.font.size = Pt(11.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_CYAN
        p2 = tf10_l.add_paragraph()
        p2.text = f"   {p_desc}"
        p2.font.size = Pt(10.5)
        p2.font.color.rgb = TEXT_MUTED
        p2.space_after = Pt(6)

    # Right: Value Proposition & Impact
    add_card(s10, 7.7, 1.5, 4.8, 5.2, "Summary of Project Impact")
    tb10_r = s10.shapes.add_textbox(Inches(7.9), Inches(2.1), Inches(4.4), Inches(4.4))
    tf10_r = tb10_r.text_frame
    tf10_r.word_wrap = True

    impact_points = [
        ("100% Privacy Compliance", "Zero civilian PII leaves the on-premise infrastructure."),
        ("100% Model Accuracy", "Multi-head DistilBERT student matches teacher precision on 4 M.O. targets."),
        ("20.37 Million Records", "Proved national-scale ingestion capability across 6 major police forces."),
        ("$0 Cloud Inference Cost", "Local 24-core CPU batch inference eliminates massive LLM API bills."),
        ("Actionable Law Enforcement Intel", "Bridges isolated raw records into predictive spatial risk graphs.")
    ]
    for i_title, i_desc in impact_points:
        p = tf10_r.add_paragraph() if tf10_r.paragraphs[0].text else tf10_r.paragraphs[0]
        p.text = f"✅ {i_title}"
        p.font.size = Pt(11.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_GREEN
        p2 = tf10_r.add_paragraph()
        p2.text = f"{i_desc}"
        p2.font.size = Pt(10.5)
        p2.font.color.rgb = TEXT_MUTED
        p2.space_after = Pt(6)

    # Save presentation file
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "project_dharma_presentation.pptx")
    prs.save(output_path)
    print(f"Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    create_presentation()
