# 📋 User Stories — Sai Dhanush
**Project Name:** Dynamic Hierarchical Anonymized Real-Time Modus-Operandi Analytics (Project D.H.A.R.M.A.)  
**User / Role:** Sai Dhanush (Full-Stack CAD Ingestion & Operations Dashboard Engineer)  
**Assigned Module:** Real-Time CAD Stream Ingestion (FastAPI/gRPC), Qdrant Vector Search, Cross-Jurisdictional Serial Pattern Matching & Mapbox Command Center Dashboard  

---

### Step 1: Identify Who Will Use Your System

> **"Who are the people who will use our project?"**

| Sl. No. | Person/User | What will they do in the system? |
| :---: | :--- | :--- |
| 1 | **Full-Stack & Ingestion Engineer (Sai Dhanush)** | Build high-concurrency real-time CAD ingestion microservices, configure Qdrant vector search collections, and develop interactive operational mapping dashboards. |
| 2 | **911 / Emergency CAD Dispatcher** | Feed incoming 911 dispatch narratives into the system and receive immediate real-time M.O. predictions (weapons, entry, suspects) in <15 milliseconds. |
| 3 | **Inter-Agency Serial Crime Detective** | Perform cross-jurisdictional similarity searches using vector embeddings to link serial robberies, burglaries, or assault patterns across different police departments. |
| 4 | **Police Tactical Commander & Duty Officer** | Monitor live tactical command center dashboards displaying spatial risk hot-spots, dynamic heatmaps, time-slider crime progressions, and multi-filter analytics. |

---

### Step 2: Identify User Requirements

*Think from the user's point of view:*
* **What does the user want to do?**
* **Why does the user need this feature?**

| User | What the user wants | Why the user needs it |
| :--- | :--- | :--- |
| **Sai Dhanush (Full-Stack Engineer)** | Deploy a high-speed FastAPI/gRPC endpoint for narrative anonymization and inference | To ingest continuous live Computer-Aided Dispatch (CAD) audio/text streams with sub-15ms latency. |
| **Sai Dhanush (Full-Stack Engineer)** | Ingest M.O. vectors and narrative embeddings into Qdrant vector database | To enable sub-second high-dimensional similarity search and cosine nearest-neighbor retrieval over millions of incidents. |
| **Sai Dhanush (Full-Stack Engineer)** | Build an automated cross-jurisdiction pattern matching engine | To automatically flag high-similarity crime clusters sharing unique Modus Operandi signatures across state/city borders. |
| **Sai Dhanush (Full-Stack Engineer)** | Create an interactive Mapbox / Deck.gl web dashboard | To provide tactical commanders with visual heatmaps, road corridor overlays, and time-slider playback of evolving crime clusters. |
| **911 Dispatcher** | View instant weapon and suspect count predictions while handling emergency calls | To provide frontline officers with immediate situational awareness before arriving at the crime scene. |
| **Detective** | Search crime databases using natural language queries (e.g. "masked duo pried rear window of pharmacy") | To retrieve past identical incidents and identify potential serial offender repeat patterns. |
| **Tactical Commander** | Filter incidents by date, weapon type, entry method, and H3 hexagonal cell | To plan targeted patrol deployments and generate daily executive crime intelligence reports. |

---

### Step 3: Write User Stories

*Format:* **As a (user), I want (feature), so that (purpose).**

| User Story ID | User | Requirement (User Story) |
| :---: | :--- | :--- |
| **US-SD-01** | Full-Stack Engineer | **As a Full-Stack Engineer (Sai Dhanush)**, I want to wrap `local_anonymizer.py` and the fine-tuned DistilBERT student model into a FastAPI microservice, **so that** live CAD dispatch streams are anonymized and classified in real-time. |
| **US-SD-02** | 911 Dispatcher | **As a 911 CAD Dispatcher**, I want incoming incident narratives to return 4-head M.O. predictions in under 15 milliseconds, **so that** officers receive instant threat-level and weapon intelligence en route. |
| **US-SD-03** | Full-Stack Engineer | **As a Full-Stack Engineer (Sai Dhanush)**, I want to ingest M.O. feature vectors and text embeddings into a local Qdrant vector collection (`ingest_tri_pillar_to_qdrant_v2.py`), **so that** multi-modal similarity queries execute in sub-second time. |
| **US-SD-04** | Crime Detective | **As an Inter-Agency Detective**, I want to perform semantic similarity searches across NYPD, LAPD, Houston, and UK datasets, **so that** cross-jurisdictional serial offenders using identical Modus Operandi are quickly identified. |
| **US-SD-05** | Full-Stack Engineer | **As a Full-Stack Engineer (Sai Dhanush)**, I want to construct an automated similarity alert trigger when a new incident matches an existing cluster above a 0.88 cosine threshold, **so that** detectives receive instant serial pattern notifications. |
| **US-SD-06** | Tactical Commander | **As a Police Tactical Commander**, I want an interactive Mapbox / Deck.gl web dashboard with H3 hexagon layers and time-sliders, **so that** I can visualize spatial risk hot-spots and historical crime progression dynamically. |
| **US-SD-07** | Tactical Commander | **As a Tactical Commander**, I want multi-dimensional filtering (by weapon, target profile, date range, and census tract) with one-click PDF/CSV intelligence export, **so that** operational briefs can be generated instantly for patrol briefings. |

---

### Step 4: Define When a User Story is Completed

*Acceptance Criteria & Definition of Done:*

| User Story | How will we check it is completed? |
| :--- | :--- |
| **Real-Time FastAPI Microservice (`US-SD-01`)** | FastAPI service accepts POST requests at `/api/v1/infer_cad` and returns anonymized text and 4-head M.O. predictions in a single response payload. |
| **Sub-15ms Ingestion Latency (`US-SD-02`)** | Benchmark testing with 1,000 concurrent requests verifies average end-to-end response latency is strictly below 15 milliseconds on CPU. |
| **Qdrant Vector Database Ingestion (`US-SD-03`)** | `ingest_tri_pillar_to_qdrant_v2.py` successfully populates Qdrant collections with dense M.O. vectors and metadata payloads with 100% indexing success. |
| **Cross-Jurisdiction Serial Search (`US-SD-04`)** | A sample query (e.g. "commercial burglary with rear window pry bar") retrieves top-10 nearest neighbor incidents across multiple cities ranked by cosine similarity. |
| **Serial Pattern Alert Trigger (`US-SD-05`)** | Simulated ingestion of a matching incident emits an automated alert with linked case IDs when cosine similarity exceeds 0.88. |
| **Interactive Mapbox / Deck.gl Dashboard (`US-SD-06`)** | Web application renders interactive H3 hexagons, road network layers, and time-slider animation smoothly at 60 FPS without UI freezing. |
| **Multi-Dimensional Filters & Export (`US-SD-07`)** | Users can filter by any combination of weapon, entry point, target, and date range, with one-click export generating verified CSV and PDF summary reports. |
