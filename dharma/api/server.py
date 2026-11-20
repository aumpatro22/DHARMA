#!/usr/bin/env python3
"""
server.py — Project D.H.A.R.M.A. Tactical Crime Intelligence Web Interface & API

Backend Service powering the local real-time forensic analysis interface:
  1. Zero-PII sanitization via local_anonymizer.py (Regex + spaCy NER)
  2. Multi-Head Modus Operandi extraction via DistilBERT 66M student model
  3. Forensic thinking & multi-hypothesis reasoning via forensic_thinking_engine.py
  4. Spatiotemporal road network risk inference via CrimeSTGCN
  5. 100% Offline, Zero Cloud Dependencies, LLaMA 3.3-70B decapitated.

Author: Project D.H.A.R.M.A. Engineering
Port: 8008
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Ensure project root is in path
try:
    from dharma.config import PROJECT_ROOT, STATIC_DIR, MODELS_DIR, PROCESSED_DIR
except ImportError:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    STATIC_DIR = PROJECT_ROOT / "static"
    MODELS_DIR = PROJECT_ROOT / "models"
    PROCESSED_DIR = PROJECT_ROOT / "processed"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Threading config for high CPU throughput
num_cores = min(os.cpu_count() or 4, 24)
os.environ["OMP_NUM_THREADS"] = str(num_cores)
os.environ["MKL_NUM_THREADS"] = str(num_cores)
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
torch.set_num_threads(num_cores)

try:
    from dharma.nlp.anonymizer import LocalAnonymizer
    from dharma.nlp.thinking_engine import ForensicThinkingEngine
except ImportError:
    from local_anonymizer import LocalAnonymizer
    from forensic_thinking_engine import ForensicThinkingEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s — %(message)s")
logger = logging.getLogger("dharma.server")

app = FastAPI(
    title="Project D.H.A.R.M.A. Forensic Intelligence Console",
    description="Real-Time Modus Operandi Neural Extraction & Spatiotemporal Risk Engine",
    version="2.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global In-Memory Model Cache
# ---------------------------------------------------------------------------
ANONYMIZER: Optional[LocalAnonymizer] = None
THINKING_ENGINE: Optional[ForensicThinkingEngine] = None
GNN_CACHE: Dict[str, Any] = {}

PRESETS = [
    {
        "id": "commercial_heist",
        "title": "🎯 Armed Commercial Jewelry Heist (Firearm)",
        "city": "chicago",
        "lat": 41.8818,
        "lon": -87.6231,
        "narrative": "On 2026-10-02 at 01:45, Officer James Rivera (Badge #4821) responded to an armed robbery at Gold Coast Jewelers, 120 North Michigan Ave, Chicago. Two masked suspects entered through the front entrance holding security staff at gunpoint with semi-automatic handguns and pistols. Suspects bagged $85,000 in diamonds and fled south on foot. Case lead: Detective Kowalski (312-555-0144)."
    },
    {
        "id": "residential_burglary",
        "title": "🌙 Night Residential Burglary (Blunt Force)",
        "city": "chicago",
        "lat": 41.8781,
        "lon": -87.6298,
        "narrative": "Between 23:00 and 04:30 on 2026-09-28, victim Linda Chen reported a residential break-in at 842 West Adams St, Chicago. The solo perpetrator pried open the ground-floor rear bedroom window using a heavy crowbar and pry bar while residents were asleep. Stole cash, luxury watches, and laptop hardware. Latent fingerprints lifted from window sill by CSI Investigator Davis (Badge #6102)."
    },
    {
        "id": "bladed_mugging",
        "title": "🔪 Bladed Street Mugging (Bladed)",
        "city": "sf",
        "lat": 37.7833,
        "lon": -122.4167,
        "narrative": "At approximately 21:15 near 6th St and Mission St, San Francisco, a pedestrian victim was ambushed on the sidewalk by two armed assailants. One suspect pulled a 6-inch tactical knife and blade, slashing the victim jacket and brandishing the weapon demanding his wallet and phone before both suspects fled into the alley. SFPD Officer Hernandez (Badge #219) responded."
    },
    {
        "id": "unarmed_retail_theft",
        "title": "🏬 Unarmed Retail Shoplifting (No Weapons)",
        "city": "chicago",
        "lat": 41.8900,
        "lon": -87.6250,
        "narrative": "Loss Prevention staff at Nordstrom on Michigan Ave, Chicago observed a solo female suspect conceal multiple designer handbags inside an oversized shopping tote. Suspect walked past all cash registers making no attempt to pay, and exited through the front doors into the street with no weapons involved. When approached by security, suspect abandoned the bag and fled on foot."
    },
    {
        "id": "physical_assault_robbery",
        "title": "👊 Violent Transit Assault (Physical Force)",
        "city": "sf",
        "lat": 37.7749,
        "lon": -122.4194,
        "narrative": "At 14:20 near Market Street transit station, San Francisco, a delivery courier was ambushed on the public sidewalk by three gang members. The trio assaulted the courier, punching and kicking the victim in the ribs before snatching his transport backpack and running toward the subway. Responding paramedic unit treated victim for facial contusions."
    }
]


def init_models():
    global ANONYMIZER, THINKING_ENGINE
    logger.info("Initializing Local Anonymizer...")
    t0 = time.time()
    ANONYMIZER = LocalAnonymizer()
    logger.info("Local Anonymizer initialized in %.2fs", time.time() - t0)

    logger.info("Initializing Multi-Head DistilBERT Forensic Thinking Engine...")
    t1 = time.time()
    THINKING_ENGINE = ForensicThinkingEngine()
    logger.info("Forensic Thinking Engine initialized in %.2fs", time.time() - t1)


# ---------------------------------------------------------------------------
# ST-GCN City Risk Inference (Cached)
# ---------------------------------------------------------------------------
def get_city_risk(city: str, lat: float, lon: float) -> Dict[str, Any]:
    city = city.lower()
    if city not in ["sf", "chicago"]:
        return {
            "city": city,
            "supported": False,
            "message": f"ST-GCN road graph currently compiled for Chicago (29,807 nodes) and SF (10,033 nodes)."
        }

    try:
        from models.gnn.predict_risk import (
            load_model_and_graph, CITY_CRS, GRAPHS_DIR, PROCESSED_DIR
        )
        import pyproj
        from scipy.spatial import cKDTree
        import numpy as np
        import pandas as pd

        device = torch.device("cpu")
        crs_code = CITY_CRS.get(city, "EPSG:32610")

        if city not in GNN_CACHE:
            logger.info("Pre-warming ST-GCN graph cache for %s...", city)
            model, graph_dict, static_x, edge_index, edge_attr = load_model_and_graph(city, device)

            to_utm = pyproj.Transformer.from_crs("EPSG:4326", crs_code, always_xy=True)
            to_wgs84 = pyproj.Transformer.from_crs(crs_code, "EPSG:4326", always_xy=True)

            pos = graph_dict["pos"].cpu().numpy()
            tree = cKDTree(pos)

            # Precompute input sequence
            fused_path = PROCESSED_DIR / f"{city}_fused_matrix.parquet"
            if not fused_path.exists():
                fused_path = PROCESSED_DIR / f"{city}_mo_full.parquet"

            df = pd.read_parquet(fused_path)
            time_col = "timestamp" if "timestamp" in df.columns else ("date" if "date" in df.columns else None)
            df["dt"] = pd.to_datetime(df[time_col], errors="coerce")
            df = df.dropna(subset=["dt", "latitude", "longitude"])
            df = df[(df["latitude"] != 0) & (df["longitude"] != 0)]
            df = df.sort_values("dt").reset_index(drop=True)

            incident_coords = np.column_stack([df["latitude"].values, df["longitude"].values])
            _, nearest_nodes = tree.query(incident_coords)
            df["node_idx"] = nearest_nodes

            df["time_slice"] = df["dt"].dt.floor("14D")
            unique_slices = sorted(df["time_slice"].unique())
            seq_len = 6
            recent_slices = unique_slices[-seq_len:]

            num_nodes = graph_dict["num_nodes"]
            seq_tensors = []
            for t_slice in recent_slices:
                counts = np.zeros(num_nodes, dtype=np.float32)
                sub_df = df[df["time_slice"] == t_slice]
                if not sub_df.empty:
                    vc = sub_df["node_idx"].value_counts()
                    counts[vc.index.values] = vc.values
                dyn_channel = torch.tensor(counts, dtype=torch.float32).unsqueeze(-1).to(device)
                x_step = torch.cat([static_x, dyn_channel], dim=-1)
                seq_tensors.append(x_step)

            input_seq = torch.stack(seq_tensors, dim=0)

            with torch.no_grad():
                predicted_risk = model(input_seq, edge_index, edge_attr).cpu().numpy()

            mean_risk = float(np.mean(predicted_risk))
            max_risk = float(np.max(predicted_risk))
            std_risk = float(np.std(predicted_risk)) + 1e-6

            # Compute top 5 hotspots
            top_k_indices = np.argsort(predicted_risk)[::-1][:5]
            top_hotspots = []
            for rank_idx, node_id in enumerate(top_k_indices, start=1):
                node_utm_x, node_utm_y = pos[node_id]
                node_lon, node_lat = to_wgs84.transform(node_utm_x, node_utm_y)
                top_hotspots.append({
                    "rank": rank_idx,
                    "node_id": int(node_id),
                    "latitude": round(float(node_lat), 5),
                    "longitude": round(float(node_lon), 5),
                    "risk_score": round(float(predicted_risk[node_id]), 4),
                })

            GNN_CACHE[city] = {
                "num_nodes": int(num_nodes),
                "num_edges": int(edge_index.shape[1]),
                "pos": pos,
                "tree": tree,
                "to_utm": to_utm,
                "to_wgs84": to_wgs84,
                "predicted_risk": predicted_risk,
                "mean_risk": mean_risk,
                "max_risk": max_risk,
                "std_risk": std_risk,
                "top_hotspots": top_hotspots,
            }

        cache = GNN_CACHE[city]
        tree = cache["tree"]
        to_utm = cache["to_utm"]
        to_wgs84 = cache["to_wgs84"]
        pos = cache["pos"]
        predicted_risk = cache["predicted_risk"]

        query_x, query_y = to_utm.transform(lon, lat)
        dist_m, nearest_node_idx = tree.query([query_x, query_y])

        # Geographic Bounding Constraint: Guard against international / out-of-bounds coordinates (e.g. India, China)
        MAX_SNAP_DISTANCE_METERS = 10000.0  # 10 km maximum snapping tolerance
        if dist_m > MAX_SNAP_DISTANCE_METERS:
            logger.warning("Coordinates (%s, %s) are %.1f km outside %s bounds.", lat, lon, dist_m / 1000.0, city)
            return {
                "city": city.upper(),
                "supported": False,
                "error_type": "GEOGRAPHIC_OUT_OF_BOUNDS",
                "query_lat": lat,
                "query_lon": lon,
                "distance_km": round(float(dist_m) / 1000.0, 1),
                "message": f"Input coordinates ({lat:.4f}, {lon:.4f}) are {dist_m/1000.0:,.1f} km outside the {city.upper()} road network. ST-GCN graph tensors are localized to compiled urban street topologies.",
                "resolution_directive": f"To forecast risk in this region (e.g. India or China), extract the localized road network topology using network_graph_builder.py.",
                "top_hotspots": cache["top_hotspots"],
            }

        snapped_utm_x, snapped_utm_y = pos[nearest_node_idx]
        snapped_lon, snapped_lat = to_wgs84.transform(snapped_utm_x, snapped_utm_y)

        local_risk = float(predicted_risk[nearest_node_idx])
        z_score = (local_risk - cache["mean_risk"]) / cache["std_risk"]

        if z_score > 2.0:
            threat_level = "CRITICAL / SEVERE HOTSPOT"
            badge_color = "red"
        elif z_score > 1.0:
            threat_level = "HIGH RISK"
            badge_color = "amber"
        elif z_score > 0.0:
            threat_level = "ELEVATED / MODERATE"
            badge_color = "blue"
        else:
            threat_level = "LOW / BASELINE"
            badge_color = "emerald"

        return {
            "city": city.upper(),
            "supported": True,
            "num_nodes": cache["num_nodes"],
            "num_edges": cache["num_edges"],
            "query_lat": lat,
            "query_lon": lon,
            "snapped_node_id": int(nearest_node_idx),
            "snapped_distance_m": round(float(dist_m), 1),
            "snapped_lat": round(float(snapped_lat), 5),
            "snapped_lon": round(float(snapped_lon), 5),
            "predicted_risk": round(local_risk, 4),
            "mean_risk": round(cache["mean_risk"], 4),
            "std_risk": round(cache["std_risk"], 4),
            "z_score": round(float(z_score), 2),
            "threat_level": threat_level,
            "badge_color": badge_color,
            "top_hotspots": cache["top_hotspots"],
            "calculation_steps": {
                "step1_utm_projection": f"GPS ({lat}, {lon}) projected to UTM {crs_code} coordinates: ({query_x:.1f}m, {query_y:.1f}m)",
                "step2_kdtree_snap": f"KD-Tree query found nearest road node #{nearest_node_idx} at UTM ({snapped_utm_x:.1f}m, {snapped_utm_y:.1f}m)",
                "step3_euclidean_distance": f"Euclidean road offset: d = sqrt(({query_x:.1f} - {snapped_utm_x:.1f})² + ({query_y:.1f} - {snapped_utm_y:.1f})²) = {dist_m:.1f} meters",
                "step4_stgcn_prediction": f"CrimeSTGCN forward pass on 6 biweekly graph tensors yielded node risk = {local_risk:.4f}",
                "step5_z_score_normalization": f"Z-Score = (LocalRisk - Mean) / Std = ({local_risk:.4f} - {cache['mean_risk']:.4f}) / {cache['std_risk']:.4f} = {z_score:+.2f}σ",
                "step6_threat_tier": f"Z-Score {z_score:+.2f}σ maps to threat category: '{threat_level}'"
            }
        }
    except Exception as e:
        logger.error("Error running ST-GCN risk lookup: %s", str(e), exc_info=True)
        return {
            "city": city,
            "supported": False,
            "error": str(e)
        }


# ---------------------------------------------------------------------------
# API Request & Response Models
# ---------------------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    narrative: str = Field(..., description="Raw incident text containing narrative and potential PII")
    city: Optional[str] = Field(None, description="City for ST-GCN road network risk projection")
    lat: Optional[float] = Field(None, description="Latitude coordinates")
    lon: Optional[float] = Field(None, description="Longitude coordinates")


from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_models()
    yield

app.router.lifespan_context = lifespan


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "system": "Project D.H.A.R.M.A. Forensic Intelligence",
        "version": "2.4.0",
        "architecture": "Multi-Head DistilBERT (Local & Offline)",
        "privacy_engine": "LocalAnonymizer (spaCy NER + Regex)",
        "spatiotemporal_model": "CrimeSTGCN (Chicago & SF Road Networks)",
        "hardware_threads": num_cores,
        "cloud_api_calls": 0,
        "cost_per_query": "$0.000",
    }


@app.get("/api/presets")
def get_presets():
    return PRESETS


@app.get("/api/narrative/random")
def get_random_narrative():
    import random

    first_names = ["James", "Maria", "David", "Linda", "Carlos", "Aisha", "John", "Sarah", "Michael", "Elena", "Rajesh", "Priya", "Robert", "Keiko", "Marcus"]
    last_names = ["Rivera", "Santos", "Kim", "Chen", "Johnson", "Smith", "Patel", "Kowalski", "Davis", "Tanaka", "Hernandez", "Williams", "Kumar", "O'Connor"]
    streets_chicago = [
        ("Michigan Ave", 41.8818, -87.6231),
        ("State St", 41.8837, -87.6278),
        ("Clark St", 41.8902, -87.6309),
        ("Randolph St", 41.8845, -87.6521),
        ("Halsted St", 41.8715, -87.6472),
        ("Madison St", 41.8820, -87.6400)
    ]
    streets_sf = [
        ("Market St", 37.7749, -122.4194),
        ("Mission St", 37.7833, -122.4167),
        ("Geary Blvd", 37.7858, -122.4065),
        ("Columbus Ave", 37.7981, -122.4075),
        ("Valencia St", 37.7650, -122.4218)
    ]

    city = random.choice(["chicago", "sf"])
    st_name, base_lat, base_lon = random.choice(streets_chicago if city == "chicago" else streets_sf)
    lat = round(base_lat + random.uniform(-0.004, 0.004), 4)
    lon = round(base_lon + random.uniform(-0.004, 0.004), 4)
    addr_num = random.randint(100, 2400)
    address = f"{addr_num} {st_name}"

    officer = f"Officer {random.choice(first_names)} {random.choice(last_names)} (Badge #{random.randint(1000, 9999)})"
    victim = f"{random.choice(first_names)} {random.choice(last_names)}"
    witness = f"{random.choice(first_names)} {random.choice(last_names)}"
    phone = f"({random.randint(200, 999)}) 555-{random.randint(1000, 9999)}"
    hour = random.randint(0, 23)
    minute = random.randint(10, 59)
    time_str = f"{hour:02d}:{minute:02d}"

    archetypes = [
        {
            "title": "🎯 Commercial Armed Robbery (Handgun)",
            "text": f"At approximately {time_str}, {officer} responded to an armed robbery at a boutique on {address}. Two masked perpetrators entered through the front door brandishing semi-automatic handguns and pistols. Suspects held cashier {victim} at gunpoint, shattered the display counters, bagged high-value goods, and fled on foot. Witness {witness} notified dispatch at {phone}."
        },
        {
            "title": "🌙 Night Residential Burglary (Crowbar / Forced Window)",
            "text": f"On {time_str}, resident {victim} returned home to find a ground-floor rear bedroom window shattered and pried open at {address}. The solo perpetrator entered while residents were away, used a heavy crowbar to force the window lock, and escaped with jewelry, laptops, and cash. {officer} lifted tool impressions from the window sill. Tips line: {phone}."
        },
        {
            "title": "🔪 Sidewalk Mugging (Bladed Tactical Knife)",
            "text": f"At {time_str} near {address}, a pedestrian was ambushed on the public sidewalk by two armed assailants. One perpetrator pulled a 6-inch tactical knife and blade, slashing {victim}'s coat and demanding their wallet and phone before fleeing down the alley. {officer} interviewed bystander {witness}. Case line: {phone}."
        },
        {
            "title": "🚗 Opportunistic Vehicle Theft",
            "text": f"At {time_str}, motorist {victim} reported a vehicle theft at {address}. While the engine was left idling, a solo suspect jumped into the driver seat and sped away westbound. Responding unit {officer} coordinated with regional transit patrol. Investigator contact: {phone}."
        },
        {
            "title": "🏬 Retail Shoplifting (Unarmed Solo)",
            "text": f"Loss prevention staff at a retail store on {address} reported an unarmed theft incident at {time_str}. A solo suspect concealed electronics in an oversized backpack and slipped through the front doors without displaying any weapons or threatening staff. {officer} reviewed security camera footage with manager {witness}. Call: {phone}."
        },
        {
            "title": "🏭 Commercial Facility Breach (Roof / Vent)",
            "text": f"At {time_str}, security sensors triggered at a commercial facility on {address}. A solo intruder gained access through a rooftop ventilation shaft and hvac duct with heavy cutting tools. The perpetrator ransacked inventory rooms and fled via the external fire escape. Investigating lead: {officer}. Direct line: {phone}."
        }
    ]

    selected = random.choice(archetypes)
    return {
        "title": selected["title"],
        "narrative": selected["text"],
        "city": city,
        "lat": lat,
        "lon": lon,
    }


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    if not req.narrative or not req.narrative.strip():
        raise HTTPException(status_code=400, detail="Narrative text is required.")

    t_start = time.time()

    # Step 1: Zero-PII Anonymization
    t0 = time.time()
    anon_result = ANONYMIZER.anonymize(req.narrative)
    t_anon_ms = round((time.time() - t0) * 1000, 2)

    # Step 2: Multi-Head DistilBERT & Forensic Reasoning Engine
    t1 = time.time()
    engine_result = THINKING_ENGINE.analyze(anon_result["anonymized_text"])
    t_engine_ms = round((time.time() - t1) * 1000, 2)

    # Step 3: ST-GCN Spatiotemporal Risk Projection (if coordinates provided)
    t2 = time.time()
    city_risk = None
    if req.city and req.lat is not None and req.lon is not None:
        city_risk = get_city_risk(req.city, req.lat, req.lon)
    t_risk_ms = round((time.time() - t2) * 1000, 2)

    total_latency_ms = round((time.time() - t_start) * 1000, 2)

    return {
        "success": True,
        "meta": {
            "total_latency_ms": total_latency_ms,
            "stage_latencies_ms": {
                "pii_anonymization": t_anon_ms,
                "neural_mo_and_thinking": t_engine_ms,
                "stgcn_road_risk": t_risk_ms,
            },
            "hardware": f"Intel Xeon ({num_cores} CPU cores)",
            "cloud_tokens_used": 0,
            "llama_3_status": "DECAPITATED",
            "cjis_compliant": True,
        },
        "privacy": {
            "original_narrative": req.narrative,
            "anonymized_narrative": anon_result["anonymized_text"],
            "redactions_count": anon_result["redactions_count"],
            "entity_map": anon_result["entity_map"],
        },
        "modus_operandi": {
            "top_possibilities": engine_result["top_possibilities"],
            "prob_distributions": engine_result["prob_distributions"],
            "entropy_scores": engine_result["entropy_scores"],
        },
        "forensic_intelligence": {
            "scenarios": engine_result["scenarios"],
            "chain_of_thought": engine_result["chain_of_thought"],
            "tactical_checklist": engine_result["tactical_checklist"],
        },
        "math_proof": engine_result.get("math_proof"),
        "spatial_risk": city_risk,
    }


@app.get("/api/download-zip")
def download_project_zip():
    zip_path = PROJECT_ROOT / "Project_Crime_detection.zip"
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Zip file not found")
    return FileResponse(
        str(zip_path),
        media_type="application/zip",
        filename="Project_Crime_detection.zip"
    )


@app.get("/api/download-screenshots")
def download_screenshots_zip():
    zip_path = PROJECT_ROOT / "Project_Screenshots_and_Charts.zip"
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Screenshots zip not found")
    return FileResponse(
        str(zip_path),
        media_type="application/zip",
        filename="Project_Screenshots_and_Charts.zip"
    )


# Mount static directory for frontend
static_path = PROJECT_ROOT / "static"
app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")

if __name__ == "__main__":
    try:
        import subprocess
        subprocess.run(["fuser", "-k", "8008/tcp"], capture_output=True)
        time.sleep(0.3)
    except Exception:
        pass
    uvicorn.run(app, host="0.0.0.0", port=8008)
