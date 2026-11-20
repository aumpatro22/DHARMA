# 📋 User Stories — Aum Patro
**Project Name:** Dynamic Hierarchical Anonymized Real-Time Modus-Operandi Analytics (Project D.H.A.R.M.A.)  
**User / Role:** Aum Patro (Chief ML/NLP Architect & Privacy Pipeline Engineer)  
**Assigned Module:** Privacy-Preserving PII Engine, Teacher-Student Distillation, 4-Head DistilBERT Classifier & National Batch Streaming  

---

### Step 1: Identify Who Will Use Your System

> **"Who are the people who will use our project?"**

| Sl. No. | Person/User | What will they do in the system? |
| :---: | :--- | :--- |
| 1 | **ML/NLP Pipeline Engineer (Aum Patro)** | Build and execute automated PII redaction pipelines, fine-tune multi-head NLP models, and run high-throughput batch inference over millions of historical crime narratives. |
| 2 | **Forensic Intelligence Analyst** | Review extracted Modus Operandi (M.O.) ground-truth labels (weapons, entry points, targets, suspect counts) to establish criminal behavioral profiles without exposing civilian PII. |
| 3 | **Law Enforcement Data Privacy Officer** | Inspect and audit sanitized text streams to ensure zero Personally Identifiable Information (PII) or CJIS-restricted data leaves on-premise infrastructure. |
| 4 | **System & Infrastructure Administrator** | Monitor Xeon CPU utilization, AMX bfloat16 vector execution, and PyArrow Parquet streaming throughput during national-scale batch processing. |

---

### Step 2: Identify User Requirements

*Think from the user's point of view:*
* **What does the user want to do?**
* **Why does the user need this feature?**

| User | What the user wants | Why the user needs it |
| :--- | :--- | :--- |
| **Aum Patro (Lead ML Engineer)** | Scrub names, phone numbers, badge IDs, and addresses locally | To prevent PII leakage to cloud LLM endpoints and comply with CJIS privacy regulations. |
| **Aum Patro (Lead ML Engineer)** | Retain coreference tokens (e.g., `PERSON_Alpha_01`, `BADGE_01`) | To preserve grammatical syntax and actor-victim relationships for accurate downstream M.O. classification. |
| **Aum Patro (Lead ML Engineer)** | Extract 4-head Gold Standard M.O. labels using Groq LPU (LLaMA 3.3-70B) | To establish high-quality training ground-truth for local student model distillation. |
| **Aum Patro (Lead ML Engineer)** | Fine-tune a 4-head DistilBERT classifier on 24-core Xeon CPU | To achieve 100% offline inference capability with zero recurring cloud API costs and sub-millisecond latency. |
| **Aum Patro (Lead ML Engineer)** | Stream 20.37M crime records in 1M chunks to Parquet format | To prevent memory exhaustion (OOM) and enable high-speed vectorized analytical querying. |
| **Forensic Analyst** | View extracted M.O. classifications with per-head confidence scores | To assess evidence credibility and identify recurring criminal behavioral signatures. |
| **System Administrator** | Access dynamic real-time execution logbooks and ETA telemetry | To track batch processing progress and ensure unattended pipeline resilience against disconnections. |

---

### Step 3: Write User Stories

*Format:* **As a (user), I want (feature), so that (purpose).**

| User Story ID | User | Requirement (User Story) |
| :---: | :--- | :--- |
| **US-AP-01** | ML/NLP Engineer | **As an ML Engineer (Aum Patro)**, I want to sanitize raw crime incident narratives using a hybrid Regex + spaCy NER pipeline, **so that** all civilian and officer PII is completely stripped before any external API dispatch. |
| **US-AP-02** | ML/NLP Engineer | **As an ML Engineer (Aum Patro)**, I want to replace identical entities with consistent coreference labels (e.g., `PERSON_Alpha_01`), **so that** grammatical narrative structure and entity relationships remain intact for semantic analysis. |
| **US-AP-03** | ML/NLP Engineer | **As an ML Engineer (Aum Patro)**, I want to query Groq Cloud LPU (LLaMA 3.3-70B) in deterministic JSON mode at `temperature=0.0`, **so that** I can generate a 2,000-sample Gold Standard M.O. seed dataset with zero hallucination. |
| **US-AP-04** | ML/NLP Engineer | **As an ML Engineer (Aum Patro)**, I want to fine-tune a Multi-Head DistilBERT model with 4 classification heads (`weapon`, `entry`, `target`, `suspects`), **so that** a single lightweight model can predict complete Modus Operandi profiles simultaneously. |
| **US-AP-05** | ML/NLP Engineer | **As an ML Engineer (Aum Patro)**, I want to optimize model training and inference for 24-core Intel Xeon CPU threads, **so that** training completes locally in under 15 minutes and achieves 100% validation accuracy. |
| **US-AP-06** | ML/NLP Engineer | **As an ML Engineer (Aum Patro)**, I want to process 20.37M historical crime records using PyArrow Parquet streaming in 1,000,000-row chunks, **so that** system RAM usage remains capped below 18 GB with throughput exceeding 1,200 recs/sec. |
| **US-AP-07** | System Administrator | **As a System Administrator**, I want unattended batch execution with SIGHUP signal traps and real-time Markdown logbooks, **so that** long-running inference jobs survive terminal disconnects and maintain live progress telemetry. |

---

### Step 4: Define When a User Story is Completed

*Acceptance Criteria & Definition of Done:*

| User Story | How will we check it is completed? |
| :--- | :--- |
| **Local PII Scrubbing (`US-AP-01`)** | Narrative text is processed by `local_anonymizer.py`; 100% of names, phone numbers, badge IDs, and street addresses are masked with zero regex/NER leakage. |
| **Coreference Preservation (`US-AP-02`)** | Multiple occurrences of the same individual/officer in a narrative receive the exact same token ID (e.g., `PERSON_Alpha_01` throughout the text). |
| **Groq Gold Seed Extraction (`US-AP-03`)** | `generate_gold_seed.py` outputs `gold_seed_2000.json` containing 2,000 valid, schema-validated JSON records with per-field confidence scores. |
| **DistilBERT Multi-Head Training (`US-AP-04`)** | `train_student_model.py` produces `model.pt` predicting all 4 taxonomy heads simultaneously without separate forward passes. |
| **100% Validation Accuracy (`US-AP-05`)** | Evaluation on the validation split achieves 100.0% accuracy across `weapon_classification`, `point_of_entry`, `target_profile`, and `suspect_count_estimate`. |
| **National Batch Streaming (`US-AP-06`)** | Ingestion of 20,373,839 records across NYPD, UK, LAPD, Houston, SF, and Chicago produces valid Parquet datasets (`nypd_mo_full.parquet`, `uk_mo_full.parquet`, etc.) at >1,200 recs/s. |
| **Resilient Unattended Execution (`US-AP-07`)** | `run_unattended_pipeline.sh` completes all 6 pipeline stages detached from terminal with live status recorded in `progress_logbook.md` and `progress_logbook.json`. |
