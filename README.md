# 🛡️ Project D.H.A.R.M.A.
### Dynamic Hierarchical Anonymized Real-Time Modus-Operandi Analytics
**Privacy-Preserving NLP Distillation & Spatiotemporal Graph Neural Networks for Crime Analysis**

---

## 📌 Overview

**Project D.H.A.R.M.A.** is an end-to-end, privacy-compliant, forensic crime detection and behavioral analysis platform. It resolves the core tension between legal privacy compliance (CJIS/GDPR) and computational feasibility at national scale:

1. **Zero-PII Privacy Engine**: Scrubs personally identifiable information (victim names, officer badges, residential addresses, phone numbers) on-premise using hybrid Regex + spaCy Named Entity Recognition (NER) with coreference preservation.
2. **Teacher-Student Distillation**: Distills zero-temperature Groq LPU (`llama-3.3-70b-versatile`) forensic reasoning into a lightweight on-premise **Multi-Head DistilBERT** student model (66M parameters) achieving **96.22% accuracy** across 1,000 unseen test records.
3. **National-Scale High-Throughput Batch Engine**: Streams multi-million record police archives (NYPD, LAPD, Houston, UK Police) through CPU-optimized batch inference.
4. **Spatiotemporal Graph Neural Networks (ST-GCN)**: Models urban road network topology (OSMnx/NetworkX) fused with Uber H3 spatial indexing and Census boundary demographics for crime risk forecasting.
5. **Forensic Thinking & Multi-Scenario Engine**: Generates ranked probabilistic hypotheses, Shannon entropy ambiguity scores, and step-by-step detective investigative checklists.

---

## 🗂️ Project Directory & File Catalog

```
Project_Crime_detection/
├── README.md                      # [You Are Here] Master Architecture & File Catalog
├── pyproject.toml                 # Standard packaging specification (pip install -e .)
│
├── 🛡️ dharma/                      # Core Production Package (Clean Domain Subsystems)
│   ├── config.py                  # Centralized relative path & directory resolver
│   ├── nlp/                       # Natural Language Processing & Forensic Reasoning
│   │   ├── anonymizer.py          # Zero-PII Regex + spaCy NER scrubbing engine
│   │   ├── extractor.py           # Teacher LLM (Groq LLaMA 3.3-70B) M.O. extractor
│   │   ├── thinking_engine.py     # Multi-hypothesis reasoning & Shannon entropy
│   │   └── student_trainer.py     # Multi-Head DistilBERT student training script
│   ├── spatial/                   # Geospatial & Network Topology
│   │   ├── fuser.py               # Uber H3 + Census Tracts + NOAA Weather ETL
│   │   └── graph_builder.py       # OSMnx drivable road network graph builder
│   ├── gnn/                       # Spatiotemporal Graph Neural Networks
│   │   ├── stgcn.py               # CrimeSTGCN model architecture & training
│   │   └── risk_predictor.py      # Real-time road intersection risk inference
│   ├── batch/                     # High-Throughput Batch Processing
│   │   ├── batch_infer.py         # 24-core Intel Xeon streaming batch engine
│   │   └── pipeline.py            # End-to-end prototype ingestion pipeline
│   └── api/                       # Tactical Intelligence API & Web Dashboard
│       └── server.py              # FastAPI server (:8008) powering interactive console
│
├── ⚡ scripts/                     # Automation, Batch Runners & Evaluation Tools
│   ├── run_all_pipelines.sh       # Batch runner for Stage 1 (NYPD)
│   ├── run_remaining_stages.sh    # Batch runner for Stages 2 & 3 (LAPD & Houston)
│   ├── run_unattended_pipeline.sh # Resilient runner across all 6 national datasets
│   ├── show_model_audit.py        # Official teacher-ready accuracy & confidence report
│   ├── evaluate_test_set.py       # Test evaluation on 1,000 unseen hold-out records
│   ├── inspect_outputs.py         # CLI inspection tool for Parquet matrices
│   ├── generate_gold_seed.py      # Gold Standard seed generation via Groq API
│   └── generate_gold_seed_local.py# Gold Standard seed generation locally (3,500 records)
│
├── 🧪 tests/                      # Automated Verification & Stress Testing
│   ├── test_50_cases.py           # Automated test suite (50 synthetic PII cases)
│   ├── test_difficult_scenarios.py# 3 complex multi-weapon / multi-target stress scenarios
│   └── fixtures/                  # Ground truth test fixtures & result outputs
│
├── 📁 data/                       # Datasets, gold seed training data, and test sets
├── 📁 models/                     # Checkpoints & weights (DistilBERT 268 MB & ST-GCN)
├── 📁 processed/                  # Output Parquet matrices and road graph tensors
├── 📁 logs/                       # Application & execution logs (server.log, fuser.log)
├── 📁 static/                     # Web UI console assets (Leaflet maps, CSS, JS)
└── 📚 docs/                       # Research papers, slide decks & reports
    ├── docs/reports/              # Academic papers, mathematical proofs, and stress reports
    ├── docs/user_stories/         # Sprint user stories and acceptance criteria
    └── docs/presentation/         # Interactive slide deck and PowerPoint (.pptx)
```

*(Note: Lightweight root entrypoint shims like `server.py` and `show_model_audit.py` are preserved at the repository root for backwards-compatible convenience).*

---

## 🚀 Quickstart & Common Commands

### 1. View Official Model Confidence & Accuracy Audit
Displays a teacher-ready audit report with exact accuracy percentages, mathematical confidence formulas, and ST-GCN sparsity explanations:
```bash
python3 show_model_audit.py
```

### 2. Run Interactive Forensic Thinking Engine
Provides multi-hypothesis reasoning, semantic entropy (ambiguity score), and an actionable detective checklist:
```bash
# Single incident analysis
python3 forensic_thinking_engine.py --narrative "Suspect smashed front window of jewelry store with a crowbar and fled solo."

# Interactive shell
python3 forensic_thinking_engine.py --interactive
```

### 3. Evaluate NLP Student Model on 1,000 Unseen Test Records
Evaluates `models/distilbert_mo_student/` on the independent hold-out test dataset:
```bash
python3 evaluate_test_set.py --test-file data/gold_test_1000.json
```

### 4. Run Road Network Risk Prediction (ST-GCN)
Predicts spatio-temporal crime hotspots on city road network topologies:
```bash
python3 models/gnn/predict_risk.py --city chicago
```

### 5. Run Batch Processing on Large Archives
Executes high-throughput CPU batch inference on historical police datasets:
```bash
python3 batch_infer_student_maxram.py \
  --input "data/chicago_crimes.csv" \
  --output "processed/chicago_mo_test.parquet" \
  --chunksize 50000
```

---

## 📊 Benchmark & Accuracy Results

| Forensic Classification Head | Classes | Unseen Test Accuracy | Status |
| :--- | :---: | :---: | :---: |
| **`weapon_classification`** | 6 | **100.00%** | Perfect distinction |
| **`suspect_count_estimate`** | 4 | **96.90%** | Outstanding |
| **`point_of_entry`** | 7 | **95.60%** | Outstanding |
| **`target_profile`** | 6 | **92.40%** | High linguistic overlap flagged via entropy |
| **Overall Average Accuracy** | — | **96.22%** | **Outstanding (DistilBERT Student)** |

---

## 👥 Authors & Team
- **Aum Patro** — Core NLP Distillation, Batch Engine Architecture & Forensic Thinking Engine
- **Ashoutosh Mohanty** — Geospatial ETL, Uber H3 Indexing & Census Polygon Spatial Joins
- **Sai Dhanush** — Spatiotemporal Graph Neural Networks (ST-GCN) & Road Network Graph Modeling
