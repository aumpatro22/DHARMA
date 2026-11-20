"""
network_graph_builder.py — Project D.H.A.R.M.A. Category B: Road Network Graph Extraction

Extracts urban road topology from OpenStreetMap via OSMnx, constructs a directed weighted
spatial graph G = (V, E, W) suitable for PyTorch Geometric Spatiotemporal GNN training,
and computes topological choke-point metrics (betweenness centrality, degree centrality).

Usage:
    python3 network_graph_builder.py --city chicago
    python3 network_graph_builder.py --city sf

Output:
    /home/aumpatro/Project_Crime_detection/processed/graphs/graph_<city>.pt

Author : Project D.H.A.R.M.A. Engineering
Python : 3.10+
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import h3
import networkx as nx
import osmnx as ox

import torch
from torch_geometric.data import Data
from torch_geometric.utils import from_networkx

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("dharma.graph_builder")

# OSMnx Caching Configuration
ox.settings.use_cache = True
ox.settings.cache_folder = str(Path(__file__).resolve().parent / "cache")

from dharma.config import PROCESSED_DIR, GRAPHS_DIR

# ---------------------------------------------------------------------------
# City Configuration Registry
# ---------------------------------------------------------------------------
CITY_CONFIG: Dict[str, Dict] = {
    "chicago": {
        "place_name": "Chicago, Illinois, United States",
        "network_type": "drive",
        "h3_resolution": 8,
        "mo_parquet": str(PROCESSED_DIR / "chicago_mo_full.parquet"),
        "fused_parquet": str(PROCESSED_DIR / "chicago_fused_matrix.parquet"),
        "lat_col": "latitude",
        "lon_col": "longitude",
    },
    "sf": {
        "place_name": "San Francisco, California, United States",
        "network_type": "drive",
        "h3_resolution": 8,
        "mo_parquet": str(PROCESSED_DIR / "sf_mo_full.parquet"),
        "fused_parquet": str(PROCESSED_DIR / "sf_fused_matrix.parquet"),
        "lat_col": "latitude",
        "lon_col": "longitude",
    },
}

# ---------------------------------------------------------------------------
# M.O. Label Encoding Maps (Must match training taxonomy)
# ---------------------------------------------------------------------------
WEAPON_MAP = {"FIREARM": 0, "BLADED": 1, "BLUNT_FORCE": 2, "MELEE_OTHER": 3, "NONE": 4, "UNKNOWN": 5}
ENTRY_MAP = {"FRONT_DOOR": 0, "REAR_DOOR": 1, "WINDOW": 2, "GARAGE": 3, "ROOF_VENT": 4, "NOT_APPLICABLE": 5, "UNKNOWN": 6}
TARGET_MAP = {"COMMERCIAL": 0, "RESIDENTIAL": 1, "INDIVIDUAL": 2, "VEHICLE": 3, "INFRASTRUCTURE": 4, "UNKNOWN": 5}
SUSPECT_MAP = {"SOLO": 0, "PAIR": 1, "GROUP": 2, "UNKNOWN": 3}

NUM_WEAPON_CLASSES = len(WEAPON_MAP)
NUM_ENTRY_CLASSES = len(ENTRY_MAP)
NUM_TARGET_CLASSES = len(TARGET_MAP)
NUM_SUSPECT_CLASSES = len(SUSPECT_MAP)


# ---------------------------------------------------------------------------
# Stage 1: OSMnx Road Network Extraction
# ---------------------------------------------------------------------------
def extract_road_network(place_name: str, network_type: str = "drive") -> nx.MultiDiGraph:
    """Downloads and constructs a NetworkX MultiDiGraph from OpenStreetMap road data."""
    logger.info("Downloading OSM road network for '%s' (type=%s)...", place_name, network_type)
    t0 = time.time()

    G = ox.graph_from_place(place_name, network_type=network_type, simplify=True)

    # Project to UTM for metric edge lengths
    G = ox.project_graph(G)

    logger.info(
        "  Road network extracted: %d nodes, %d edges (%.1fs)",
        G.number_of_nodes(), G.number_of_edges(), time.time() - t0
    )
    return G


# ---------------------------------------------------------------------------
# Stage 2: Compute Topological Choke-Point Metrics
# ---------------------------------------------------------------------------
def compute_topological_features(G: nx.MultiDiGraph) -> Dict[int, Dict[str, float]]:
    """
    Computes per-node topological centrality metrics for choke-point identification:
    - Betweenness Centrality (C_B): Fraction of shortest paths passing through a node
    - Degree Centrality (C_D): Normalized in-degree + out-degree
    - Closeness Centrality (C_C): Inverse sum of shortest path distances
    """
    logger.info("Computing topological centrality metrics...")
    t0 = time.time()

    # Convert to simple DiGraph for centrality calculations (collapse parallel edges)
    G_simple = nx.DiGraph(G)

    # Betweenness centrality (approximate with k samples for large graphs)
    n_nodes = G_simple.number_of_nodes()
    k_samples = min(200, n_nodes)
    betweenness = nx.betweenness_centrality(G_simple, k=k_samples, weight="length", normalized=True)

    # Degree centrality
    degree = nx.degree_centrality(G_simple)

    # Closeness centrality via landmark approximation (multi-source Dijkstra)
    largest_wcc = max(nx.weakly_connected_components(G_simple), key=len)
    G_wcc = G_simple.subgraph(largest_wcc).copy()
    n_wcc = len(G_wcc)
    k_landmarks = min(100, n_wcc)
    rng = np.random.RandomState(42)
    landmarks = rng.choice(list(G_wcc.nodes()), size=k_landmarks, replace=False)
    dist_sums = {n: 0.0 for n in G_wcc.nodes()}
    counts = {n: 0 for n in G_wcc.nodes()}

    for lm in landmarks:
        lengths = nx.single_source_dijkstra_path_length(G_wcc, lm, weight="length")
        for target, d in lengths.items():
            dist_sums[target] += d
            counts[target] += 1

    closeness = {}
    for n in G_wcc.nodes():
        if counts[n] > 0 and dist_sums[n] > 0:
            closeness[n] = (counts[n] / n_wcc) / (dist_sums[n] / counts[n])
        else:
            closeness[n] = 0.0

    # Merge into node feature dict
    topo_features = {}
    for node in G_simple.nodes():
        topo_features[node] = {
            "betweenness": betweenness.get(node, 0.0),
            "degree_centrality": degree.get(node, 0.0),
            "closeness": closeness.get(node, 0.0),
        }

    logger.info("  Topological features computed in %.1fs", time.time() - t0)
    return topo_features


# ---------------------------------------------------------------------------
# Stage 3: Aggregate M.O. Predictions onto H3 Hex Cells → Graph Nodes
# ---------------------------------------------------------------------------
def aggregate_mo_features_to_nodes(
    G: nx.MultiDiGraph,
    mo_parquet_path: str,
    lat_col: str,
    lon_col: str,
    h3_resolution: int,
) -> Dict[int, Dict[str, float]]:
    """
    Maps M.O. predictions from crime parquet to nearest graph nodes via H3 hex spatial join.

    For each graph node, accumulates:
    - mo_weapon_dist: Distribution over 6 weapon classes (normalized histogram)
    - mo_entry_dist: Distribution over 7 entry point classes
    - mo_target_dist: Distribution over 6 target profile classes
    - mo_suspect_dist: Distribution over 4 suspect estimate classes
    - incident_count: Total number of incidents near this node
    """
    logger.info("Aggregating M.O. features from %s onto graph nodes...", os.path.basename(mo_parquet_path))
    t0 = time.time()

    # Load M.O. predictions
    mo_df = pd.read_parquet(mo_parquet_path)
    logger.info("  Loaded %d M.O. records", len(mo_df))

    # Normalize column names to lowercase
    mo_df.columns = [c.lower() for c in mo_df.columns]
    lat_col = lat_col.lower()
    lon_col = lon_col.lower()

    # Filter records with valid coordinates
    mo_df = mo_df.dropna(subset=[lat_col, lon_col])
    mo_df = mo_df[(mo_df[lat_col] != 0) & (mo_df[lon_col] != 0)]
    logger.info("  Records with valid coordinates: %d", len(mo_df))

    # Assign H3 hex index to each incident
    mo_df["h3_index"] = mo_df.apply(
        lambda row: h3.latlng_to_cell(row[lat_col], row[lon_col], h3_resolution),
        axis=1
    )

    # Build H3 → graph node mapping using nearest node lookup
    # Get unprojected node coordinates
    G_unprojected = ox.project_graph(G, to_crs="EPSG:4326") if hasattr(G, 'graph') else G

    # Get node positions
    node_lats = nx.get_node_attributes(G_unprojected, "y")
    node_lons = nx.get_node_attributes(G_unprojected, "x")
    node_ids = list(node_lats.keys())
    node_coords = np.array([[node_lats[n], node_lons[n]] for n in node_ids])

    # For each H3 hex center, find nearest graph node
    hex_groups = mo_df.groupby("h3_index")
    node_mo_agg: Dict[int, Dict[str, np.ndarray]] = {}

    for h3_idx, group in hex_groups:
        # Get hex center coordinates
        hex_lat, hex_lon = h3.cell_to_latlng(h3_idx)

        # Find nearest graph node (simple Euclidean approximation, sufficient at city scale)
        dists = np.sqrt((node_coords[:, 0] - hex_lat) ** 2 + (node_coords[:, 1] - hex_lon) ** 2)
        nearest_node = node_ids[np.argmin(dists)]

        if nearest_node not in node_mo_agg:
            node_mo_agg[nearest_node] = {
                "weapon_hist": np.zeros(NUM_WEAPON_CLASSES, dtype=np.float32),
                "entry_hist": np.zeros(NUM_ENTRY_CLASSES, dtype=np.float32),
                "target_hist": np.zeros(NUM_TARGET_CLASSES, dtype=np.float32),
                "suspect_hist": np.zeros(NUM_SUSPECT_CLASSES, dtype=np.float32),
                "incident_count": 0,
            }

        agg = node_mo_agg[nearest_node]
        agg["incident_count"] += len(group)

        # Accumulate M.O. class histograms
        for _, row in group.iterrows():
            w = WEAPON_MAP.get(str(row.get("mo_weapon", "UNKNOWN")).upper(), 5)
            e = ENTRY_MAP.get(str(row.get("mo_entry", "UNKNOWN")).upper(), 6)
            t = TARGET_MAP.get(str(row.get("mo_target", "UNKNOWN")).upper(), 5)
            s = SUSPECT_MAP.get(str(row.get("mo_suspects", "UNKNOWN")).upper(), 3)
            agg["weapon_hist"][w] += 1
            agg["entry_hist"][e] += 1
            agg["target_hist"][t] += 1
            agg["suspect_hist"][s] += 1

    # Normalize histograms to probability distributions
    for node, agg in node_mo_agg.items():
        for key in ["weapon_hist", "entry_hist", "target_hist", "suspect_hist"]:
            total = agg[key].sum()
            if total > 0:
                agg[key] = agg[key] / total

    logger.info(
        "  M.O. features aggregated onto %d graph nodes (from %d H3 hexes) in %.1fs",
        len(node_mo_agg), len(hex_groups), time.time() - t0
    )
    return node_mo_agg


# ---------------------------------------------------------------------------
# Stage 4: Construct PyTorch Geometric Data Object
# ---------------------------------------------------------------------------
def build_pyg_data(
    G: nx.MultiDiGraph,
    topo_features: Dict[int, Dict[str, float]],
    mo_features: Dict[int, Dict[str, float]],
) -> Data:
    """
    Constructs a PyTorch Geometric Data object with:
    - Node features X ∈ R^{N x D} containing topological + M.O. behavioral features
    - Edge index tensor (COO format)
    - Edge attribute tensor (travel impedance weights)

    Node feature vector layout per node (D = 26 dimensions):
    [betweenness, degree_centrality, closeness,     # 3: topological
     weapon_hist[0..5],                               # 6: M.O. weapon distribution
     entry_hist[0..6],                                # 7: M.O. entry point distribution
     target_hist[0..5],                               # 6: M.O. target profile distribution
     suspect_hist[0..3],                              # 4: M.O. suspect estimate distribution
    ]
    """
    logger.info("Building PyTorch Geometric Data object...")
    t0 = time.time()

    # Establish deterministic node ordering
    node_list = sorted(G.nodes())
    node_to_idx = {node: idx for idx, node in enumerate(node_list)}
    num_nodes = len(node_list)

    # Feature dimension: 3 (topo) + 6 (weapon) + 7 (entry) + 6 (target) + 4 (suspect) = 26
    FEATURE_DIM = 3 + NUM_WEAPON_CLASSES + NUM_ENTRY_CLASSES + NUM_TARGET_CLASSES + NUM_SUSPECT_CLASSES
    X = np.zeros((num_nodes, FEATURE_DIM), dtype=np.float32)

    for idx, node in enumerate(node_list):
        # Topological features
        topo = topo_features.get(node, {})
        X[idx, 0] = topo.get("betweenness", 0.0)
        X[idx, 1] = topo.get("degree_centrality", 0.0)
        X[idx, 2] = topo.get("closeness", 0.0)

        # M.O. behavioral features
        mo = mo_features.get(node, {})
        offset = 3
        if "weapon_hist" in mo:
            X[idx, offset: offset + NUM_WEAPON_CLASSES] = mo["weapon_hist"]
        offset += NUM_WEAPON_CLASSES

        if "entry_hist" in mo:
            X[idx, offset: offset + NUM_ENTRY_CLASSES] = mo["entry_hist"]
        offset += NUM_ENTRY_CLASSES

        if "target_hist" in mo:
            X[idx, offset: offset + NUM_TARGET_CLASSES] = mo["target_hist"]
        offset += NUM_TARGET_CLASSES

        if "suspect_hist" in mo:
            X[idx, offset: offset + NUM_SUSPECT_CLASSES] = mo["suspect_hist"]

    # Build edge index (COO format) and edge weights
    edge_src = []
    edge_dst = []
    edge_weights = []

    for u, v, data in G.edges(data=True):
        if u in node_to_idx and v in node_to_idx:
            edge_src.append(node_to_idx[u])
            edge_dst.append(node_to_idx[v])

            # Edge weight = travel impedance based on length and maxspeed
            length = data.get("length", 100.0)  # meters
            maxspeed = data.get("maxspeed", "30")  # km/h or mph string

            # Parse maxspeed (handle lists and units)
            if isinstance(maxspeed, list):
                maxspeed = maxspeed[0]
            try:
                speed_val = float(str(maxspeed).split()[0])
            except (ValueError, IndexError):
                speed_val = 30.0

            # Convert to travel time (seconds) as impedance
            speed_ms = speed_val * 1000.0 / 3600.0  # km/h to m/s
            travel_time = length / max(speed_ms, 1.0)
            edge_weights.append(travel_time)

    edge_index = torch.tensor([edge_src, edge_dst], dtype=torch.long)
    edge_attr = torch.tensor(edge_weights, dtype=torch.float32).unsqueeze(1)
    x = torch.tensor(X, dtype=torch.float32)

    # Store node coordinates for spatial visualization
    node_y = np.array([G.nodes[n].get("y", 0.0) for n in node_list], dtype=np.float32)
    node_x_coord = np.array([G.nodes[n].get("x", 0.0) for n in node_list], dtype=np.float32)
    pos = torch.tensor(np.stack([node_x_coord, node_y], axis=1), dtype=torch.float32)

    # Construct PyG Data object
    data = Data(
        x=x,
        edge_index=edge_index,
        edge_attr=edge_attr,
        pos=pos,
        num_nodes=num_nodes,
    )

    # Store metadata for downstream training
    data.node_ids = node_list
    data.feature_dim = FEATURE_DIM
    data.feature_names = (
        ["betweenness", "degree_centrality", "closeness"]
        + [f"weapon_{i}" for i in range(NUM_WEAPON_CLASSES)]
        + [f"entry_{i}" for i in range(NUM_ENTRY_CLASSES)]
        + [f"target_{i}" for i in range(NUM_TARGET_CLASSES)]
        + [f"suspect_{i}" for i in range(NUM_SUSPECT_CLASSES)]
    )

    logger.info(
        "  PyG Data object built: %d nodes, %d edges, feature_dim=%d (%.1fs)",
        data.num_nodes, data.num_edges, FEATURE_DIM, time.time() - t0
    )
    return data


# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="D.H.A.R.M.A. Road Network Graph Builder — Extracts OSM topology into PyG tensors"
    )
    parser.add_argument(
        "--city", required=True, choices=list(CITY_CONFIG.keys()),
        help="City identifier (chicago, sf)"
    )
    parser.add_argument(
        "--output-dir", default=str(GRAPHS_DIR),
        help="Directory to save output .pt graph files"
    )
    args = parser.parse_args()

    config = CITY_CONFIG[args.city]
    output_path = Path(args.output_dir) / f"graph_{args.city}.pt"
    os.makedirs(args.output_dir, exist_ok=True)

    logger.info("=" * 80)
    logger.info("D.H.A.R.M.A. — Road Network Graph Builder")
    logger.info("=" * 80)
    logger.info("City: %s", config["place_name"])
    logger.info("Output: %s", output_path)

    pipeline_start = time.time()

    # Stage 1: Extract road network from OSM
    G = extract_road_network(config["place_name"], config["network_type"])

    # Stage 2: Compute topological choke-point metrics
    topo_features = compute_topological_features(G)

    # Stage 3: Aggregate M.O. behavioral predictions onto graph nodes
    mo_features = {}
    if os.path.exists(config["mo_parquet"]):
        mo_features = aggregate_mo_features_to_nodes(
            G,
            config["mo_parquet"],
            config["lat_col"],
            config["lon_col"],
            config["h3_resolution"],
        )
    else:
        logger.warning("M.O. parquet not found at %s. Building graph with topological features only.", config["mo_parquet"])

    # Stage 4: Build PyTorch Geometric Data object
    pyg_data = build_pyg_data(G, topo_features, mo_features)

    # Save pure tensor dict (100% compliant with PyTorch 2.6+ weights_only=True and IDE inspectors)
    tensor_dict = {
        "x": pyg_data.x,
        "edge_index": pyg_data.edge_index,
        "edge_attr": pyg_data.edge_attr,
        "pos": pyg_data.pos,
        "num_nodes": pyg_data.num_nodes,
        "feature_dim": pyg_data.feature_dim,
        "feature_names": pyg_data.feature_names,
    }
    torch.save(tensor_dict, output_path)
    logger.info("Saved graph tensor dict to %s", output_path)

    # Summary report
    total_time = time.time() - pipeline_start
    logger.info("=" * 80)
    logger.info("GRAPH CONSTRUCTION COMPLETE")
    logger.info("  City           : %s", args.city)
    logger.info("  Nodes          : %d", pyg_data.num_nodes)
    logger.info("  Edges          : %d", pyg_data.num_edges)
    logger.info("  Feature dim    : %d", pyg_data.feature_dim)
    logger.info("  File size      : %.2f MB", os.path.getsize(output_path) / (1024 * 1024))
    logger.info("  Total time     : %.1f seconds", total_time)
    logger.info("=" * 80)

    # Save metadata JSON for downstream GNN training
    meta = {
        "city": args.city,
        "place_name": config["place_name"],
        "num_nodes": int(pyg_data.num_nodes),
        "num_edges": int(pyg_data.num_edges),
        "feature_dim": pyg_data.feature_dim,
        "feature_names": pyg_data.feature_names,
        "h3_resolution": config["h3_resolution"],
        "graph_file": str(output_path),
        "build_time_seconds": round(total_time, 1),
    }
    meta_path = output_path.with_suffix(".json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    logger.info("Saved graph metadata to %s", meta_path)


if __name__ == "__main__":
    main()
