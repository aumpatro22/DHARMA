# 📋 User Stories — Ashoutosh Mohanty
**Project Name:** Dynamic Hierarchical Anonymized Real-Time Modus-Operandi Analytics (Project D.H.A.R.M.A.)  
**User / Role:** Ashoutosh Mohanty (Geospatial Analytics & Spatiotemporal Graph Engineer)  
**Assigned Module:** Uber H3 Spatial Indexing, US Census Boundary Fusing, NOAA Weather Integration, OSMnx Road Topology Graph Building & Spatiotemporal GNNs  

---

### Step 1: Identify Who Will Use Your System

> **"Who are the people who will use our project?"**

| Sl. No. | Person/User | What will they do in the system? |
| :---: | :--- | :--- |
| 1 | **Geospatial & GNN Engineer (Ashoutosh Mohanty)** | Build multi-resolution spatial indexers, fuse environmental/demographic layers onto crime incident records, construct topological road graphs, and train Spatiotemporal Graph Neural Networks (ST-GCN). |
| 2 | **Urban Crime Prevention & Patrol Strategist** | Analyze dynamic 24-hour localized crime risk heatmaps across city road corridors and census block groups to optimize police patrol allocations. |
| 3 | **City Planning & Infrastructure Analyst** | Inspect topological choke-points (bridges, intersections with high betweenness centrality) and transit stop proximity correlations with crime hot-spots. |
| 4 | **GIS & Mapping Operations Specialist** | Query and visualize high-resolution Uber H3 hexagonal bins (Resolutions 7 & 8) with fused weather and socio-demographic indicators. |

---

### Step 2: Identify User Requirements

*Think from the user's point of view:*
* **What does the user want to do?**
* **Why does the user need this feature?**

| User | What the user wants | Why the user needs it |
| :--- | :--- | :--- |
| **Ashoutosh Mohanty (Geospatial Engineer)** | Convert raw incident coordinates into Uber H3 Hexagonal Indexes (Res 7 & 8) | To enable $O(1)$ spatial binning, multi-resolution aggregation, and fast spatial joining across millions of records. |
| **Ashoutosh Mohanty (Geospatial Engineer)** | Spatially join US Census Bureau Tract and Block Group boundaries | To enrich incident records with demographic, socio-economic, and jurisdictional census identifiers. |
| **Ashoutosh Mohanty (Geospatial Engineer)** | Fuse NOAA historical weather logs (temperature, precipitation, wind speed) | To capture environmental factors influencing seasonal and weather-dependent criminal activity. |
| **Ashoutosh Mohanty (Geospatial Engineer)** | Calculate nearest transit stop distance using SciPy KDTree | To measure accessibility and transit-related vulnerability across urban crime hot-spots. |
| **Ashoutosh Mohanty (Geospatial Engineer)** | Extract directed urban road networks via OSMnx and calculate graph centrality | To model road network topology, traffic connectivity, and escape route choke-points for GNNs. |
| **Patrol Strategist** | Predict localized crime risk over road segments 24 hours in advance | To proactively dispatch patrol units to high-risk corridors before incidents occur. |
| **GIS Specialist** | Load fused Parquet feature matrices into mapping and visualization tools | To perform spatial cluster analysis and overlay crime patterns with city infrastructure. |

---

### Step 3: Write User Stories

*Format:* **As a (user), I want (feature), so that (purpose).**

| User Story ID | User | Requirement (User Story) |
| :---: | :--- | :--- |
| **US-AM-01** | Geospatial Engineer | **As a Geospatial Engineer (Ashoutosh Mohanty)**, I want to map GPS coordinates to Uber H3 hexagons at Resolutions 7 and 8, **so that** crime incidents are partitioned into uniform hierarchical spatial cells for fast geospatial analysis. |
| **US-AM-02** | Geospatial Engineer | **As a Geospatial Engineer (Ashoutosh Mohanty)**, I want to download and cache US Census Tract and Block Group GeoJSON boundaries locally, **so that** point-in-polygon spatial joins execute with zero network latency and no external API limits. |
| **US-AM-03** | Geospatial Engineer | **As a Geospatial Engineer (Ashoutosh Mohanty)**, I want to fuse NOAA weather data (precipitation, max/min temperature, wind) with crime timestamps, **so that** weather-driven crime variations are quantified as predictive features. |
| **US-AM-04** | Geospatial Engineer | **As a Geospatial Engineer (Ashoutosh Mohanty)**, I want to compute nearest public transit stop distances using a metric SciPy KDTree, **so that** proximity to transit hubs is factored into crime occurrence risk modeling. |
| **US-AM-05** | Geospatial Engineer | **As a Geospatial Engineer (Ashoutosh Mohanty)**, I want to download drivable road networks from OpenStreetMap using OSMnx, **so that** urban road topology is structured as a directed weighted spatial graph $G = (V, E, W)$. |
| **US-AM-06** | Geospatial Engineer | **As a Geospatial Engineer (Ashoutosh Mohanty)**, I want to calculate betweenness and degree centrality for road intersection nodes, **so that** critical urban choke-points and high-connectivity intersections are identified. |
| **US-AM-07** | GNN Specialist | **As a GNN Specialist (Ashoutosh Mohanty)**, I want to export PyTorch Geometric graph tensors (`graph_chicago.pt`, `graph_sf.pt`), **so that** Spatiotemporal Graph Neural Networks (ST-GCN / A3T-GCN) can be trained for dynamic risk forecasting. |

---

### Step 4: Define When a User Story is Completed

*Acceptance Criteria & Definition of Done:*

| User Story | How will we check it is completed? |
| :--- | :--- |
| **H3 Spatial Indexing (`US-AM-01`)** | `spatial_fuser.py` computes valid H3 Resolution 7 and 8 strings for 100% of non-null coordinate records without invalid index errors. |
| **Census Boundary Join (`US-AM-02`)** | Point-in-polygon matching correctly assigns `tract_fips` and `bg_fips` to crime records using offline cached GeoJSON boundary files. |
| **NOAA Weather Fusion (`US-AM-03`)** | Fused Parquet output includes valid `prcp_mm`, `tmax_c`, `tmin_c`, and `awnd_mps` columns matched against incident dates. |
| **Transit Proximity KDTree (`US-AM-04`)** | Metric Euclidean distance in meters to the nearest transit stop is appended to each record in the fused dataset. |
| **OSMnx Road Graph Extraction (`US-AM-05`)** | `network_graph_builder.py` constructs a valid `networkx.MultiDiGraph` representing drivable streets with projected metric edge lengths. |
| **Topological Centrality Metrics (`US-AM-06`)** | Node features include normalized betweenness centrality and degree centrality scores for all intersection vertices. |
| **PyTorch Geometric Tensor Export (`US-AM-07`)** | `graph_chicago.pt` and `graph_sf.pt` are saved and loaded successfully into PyTorch Geometric `Data` objects containing node feature matrices, edge indices, and edge weights. |
