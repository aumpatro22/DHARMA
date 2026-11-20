"""
predict_risk.py — Project D.H.A.R.M.A. Interactive ST-GCN Risk Inference Tool

Allows users to input custom geographic coordinates (Latitude, Longitude) or test
sample locations to evaluate real-time road-network crime risk predictions using
the trained Spatio-Temporal Graph Neural Network (ST-GCN).

Usage Examples:
    # Test San Francisco Tenderloin / Civic Center
    python3 models/gnn/predict_risk.py --city sf --lat 37.7833 --lon -122.4167

    # Test Chicago Loop / Downtown
    python3 models/gnn/predict_risk.py --city chicago --lat 41.8818 --lon -87.6231

    # Show top 10 danger zones
    python3 models/gnn/predict_risk.py --city sf --top-k 10
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
import torch
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.gnn.train_stgcn import CrimeSTGCN
# Configure threading
os.environ["OMP_NUM_THREADS"] = "4"
torch.set_num_threads(4)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("dharma.predict_risk")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GRAPHS_DIR = PROJECT_ROOT / "processed" / "graphs"
MODELS_DIR = PROJECT_ROOT / "models" / "gnn"
PROCESSED_DIR = PROJECT_ROOT / "processed"

# Default benchmark landmark coordinates
DEFAULT_COORDS = {
    "sf": {"lat": 37.7833, "lon": -122.4167, "name": "San Francisco — Tenderloin / Civic Center"},
    "chicago": {"lat": 41.8818, "lon": -87.6231, "name": "Chicago — Downtown Loop"},
}


import pyproj

# EPSG projections for each city's road network
CITY_CRS = {
    "sf": "EPSG:32610",      # UTM Zone 10N
    "chicago": "EPSG:32616", # UTM Zone 16N
}


def load_model_and_graph(city: str, device: torch.device):
    graph_path = GRAPHS_DIR / f"graph_{city}.pt"
    model_path = MODELS_DIR / f"stgcn_{city}_best.pt"

    if not graph_path.exists():
        raise FileNotFoundError(f"Graph tensor not found at {graph_path}")
    if not model_path.exists():
        raise FileNotFoundError(f"Model checkpoint not found at {model_path}")

    # Load graph
    graph_dict = torch.load(graph_path, weights_only=True)
    edge_index = graph_dict["edge_index"].to(device)
    edge_attr = graph_dict["edge_attr"].to(device)
    static_x = graph_dict["x"].to(device)  # [N, 26]

    # Initialize model
    in_channels = static_x.shape[1] + 1  # 27
    model = CrimeSTGCN(in_channels=in_channels, hidden_dim=64, num_gru_layers=2, dropout=0.0).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    model.eval()

    return model, graph_dict, static_x, edge_index, edge_attr


def predict_for_location(
    city: str,
    target_lat: float,
    target_lon: float,
    top_k: int = 5,
    device_name: str = "cpu",
):
    device = torch.device(device_name)
    model, graph_dict, static_x, edge_index, edge_attr = load_model_and_graph(city, device)

    # 1. Project GPS coordinates to city UTM network
    crs_code = CITY_CRS.get(city, "EPSG:32610")
    to_utm = pyproj.Transformer.from_crs("EPSG:4326", crs_code, always_xy=True)
    to_wgs84 = pyproj.Transformer.from_crs(crs_code, "EPSG:4326", always_xy=True)

    pos = graph_dict["pos"].cpu().numpy()  # [N, 2] -> [easting_m, northing_m]
    tree = cKDTree(pos)

    # If coordinates are in GPS WGS84 range
    if -180.0 <= target_lon <= 180.0 and -90.0 <= target_lat <= 90.0:
        query_x, query_y = to_utm.transform(target_lon, target_lat)
    else:
        query_x, query_y = target_lon, target_lat

    dist_meters, nearest_node_idx = tree.query([query_x, query_y])
    snapped_utm_x, snapped_utm_y = pos[nearest_node_idx]
    snapped_lon, snapped_lat = to_wgs84.transform(snapped_utm_x, snapped_utm_y)

    # 2. Build temporal input snapshot from latest data
    fused_path = PROCESSED_DIR / f"{city}_fused_matrix.parquet"
    if not fused_path.exists():
        fused_path = PROCESSED_DIR / f"{city}_mo_full.parquet"

    df = pd.read_parquet(fused_path)
    time_col = "timestamp" if "timestamp" in df.columns else ("date" if "date" in df.columns else None)
    df["dt"] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=["dt", "latitude", "longitude"])
    df = df[(df["latitude"] != 0) & (df["longitude"] != 0)]
    df = df.sort_values("dt").reset_index(drop=True)

    # Map incidents to nearest nodes
    incident_coords = np.column_stack([df["latitude"].values, df["longitude"].values])
    _, nearest_nodes = tree.query(incident_coords)
    df["node_idx"] = nearest_nodes

    # Construct biweekly temporal sequence
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
        x_step = torch.cat([static_x, dyn_channel], dim=-1)  # [N, 27]
        seq_tensors.append(x_step)

    # [seq_len, N, 27]
    input_seq = torch.stack(seq_tensors, dim=0)

    # 3. Model Forward Pass
    with torch.no_grad():
        predicted_risk = model(input_seq, edge_index, edge_attr).cpu().numpy()

    # 4. Results Formatting
    local_risk = predicted_risk[nearest_node_idx]
    mean_risk = float(np.mean(predicted_risk))
    max_risk = float(np.max(predicted_risk))
    std_risk = float(np.std(predicted_risk)) + 1e-6

    # Normalized z-score risk
    z_score = (local_risk - mean_risk) / std_risk
    if z_score > 2.0:
        threat_level = "CRITICAL / SEVERE HOTSPOT"
    elif z_score > 1.0:
        threat_level = "HIGH RISK"
    elif z_score > 0.0:
        threat_level = "ELEVATED / MODERATE"
    else:
        threat_level = "LOW / BASELINE"

    print("=" * 76)
    print(f"  PROJECT D.H.A.R.M.A. — ST-GCN REAL-TIME RISK PREDICTION ENGINE")
    print("=" * 76)
    print(f"  City Network       : {city.upper()} ({num_nodes:,} road nodes, {edge_index.shape[1]:,} edges)")
    print(f"  Query Location     : Latitude {target_lat:.5f}, Longitude {target_lon:.5f}")
    print(f"  Snapped Road Node  : Intersection ID #{nearest_node_idx} ({dist_meters:.1f} meters from query point)")
    print("-" * 76)
    print(f"  PREDICTED INCIDENT RISK : {local_risk:.4f}  [Level: {threat_level}]")
    print(f"  Citywide Mean Risk      : {mean_risk:.4f}  (Max Observed: {max_risk:.4f})")
    print(f"  Standard Deviations (Z) : {z_score:+.2f}σ relative to city average")
    print("-" * 76)

    # Top-K Danger Zones
    top_indices = np.argsort(predicted_risk)[::-1][:top_k]
    print(f"\n  TOP {top_k} PREDICTED CRIME HOTSPOTS ACROSS {city.upper()}:")
    print(f"  {'Rank':<5} | {'Node ID':<10} | {'Latitude':<10} | {'Longitude':<11} | {'Risk Score':<12}")
    print("  " + "-" * 60)
    for rank, idx in enumerate(top_indices, start=1):
        utm_x_i, utm_y_i = pos[idx]
        lon_i, lat_i = to_wgs84.transform(utm_x_i, utm_y_i)
        score_i = predicted_risk[idx]
        print(f"  #{rank:<4} | Node {idx:<5} | {lat_i:<10.5f} | {lon_i:<11.5f} | {score_i:<12.4f}")
    print("=" * 76)


def main():
    parser = argparse.ArgumentParser(description="Query ST-GCN Crime Risk for Coordinates")
    parser.add_argument("--city", default="sf", choices=["sf", "chicago"], help="City model (sf or chicago)")
    parser.add_argument("--lat", type=float, help="Latitude")
    parser.add_argument("--lon", type=float, help="Longitude")
    parser.add_argument("--top-k", type=int, default=5, help="Number of top risk intersections to display")
    args = parser.parse_args()

    target_lat = args.lat if args.lat is not None else DEFAULT_COORDS[args.city]["lat"]
    target_lon = args.lon if args.lon is not None else DEFAULT_COORDS[args.city]["lon"]

    predict_for_location(
        city=args.city,
        target_lat=target_lat,
        target_lon=target_lon,
        top_k=args.top_k,
    )


if __name__ == "__main__":
    main()
