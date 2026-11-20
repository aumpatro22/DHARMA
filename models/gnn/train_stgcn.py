"""
train_stgcn.py — Project D.H.A.R.M.A. Spatio-Temporal Graph Neural Network (ST-GCN)

Trains a Spatio-Temporal Graph Convolutional Network combining PyTorch Geometric
spatial graph convolutions (GCNConv) with temporal recurrent units (nn.GRU)
to forecast localized crime risk across urban road network topologies.

Architecture:
    Input:
      - Static Graph: G = (V, E, W) road network from processed/graphs/graph_<city>.pt (26 features)
      - Dynamic Temporal Sequence: Past S time-steps of incident counts mapped to intersections
    Layers:
      1. Spatial GCN Block: GCNConv(in_channels=27, hidden_dim) capturing road topology & escape corridors
      2. Temporal Sequence Block: 2-layer nn.GRU capturing temporal surges, periodicity & trends
      3. Forecasting Head: MLP regressor outputting predicted crime intensity y_{v, t+1} for all v in V
    Loss:
      - Zero-inflation weighted MSE loss (emphasizing non-zero incident hotspots)

Usage:
    python3 models/gnn/train_stgcn.py --city sf --epochs 30
    python3 models/gnn/train_stgcn.py --city chicago --epochs 30

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
import pyproj
from scipy.spatial import cKDTree

import torch
import torch.nn as nn
from torch_geometric.nn import GCNConv

# Configure threading for Intel Xeon CPU execution
num_cores = min(os.cpu_count() or 4, 24)
os.environ["OMP_NUM_THREADS"] = str(num_cores)
os.environ["MKL_NUM_THREADS"] = str(num_cores)
torch.set_num_threads(num_cores)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("dharma.stgcn_trainer")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GRAPHS_DIR = PROJECT_ROOT / "processed" / "graphs"
PROCESSED_DIR = PROJECT_ROOT / "processed"
MODELS_DIR = PROJECT_ROOT / "models" / "gnn"


# ---------------------------------------------------------------------------
# ST-GCN Architecture Definition
# ---------------------------------------------------------------------------
class CrimeSTGCN(nn.Module):
    """
    Spatio-Temporal Graph Convolutional Network for Urban Crime Forecasting.
    Combines spatial GCN diffusion over street networks with temporal GRU sequence modeling.
    """

    def __init__(
        self,
        in_channels: int = 27,
        hidden_dim: int = 64,
        num_gru_layers: int = 2,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.hidden_dim = hidden_dim

        # 1. Spatial Graph Convolutional Layers
        self.gcn1 = GCNConv(in_channels, hidden_dim)
        self.gcn2 = GCNConv(hidden_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)

        # 2. Temporal Gated Recurrent Unit
        self.gru = nn.GRU(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_gru_layers,
            batch_first=True,
            dropout=dropout if num_gru_layers > 1 else 0.0,
        )

        # 3. Readout / Prediction Head
        self.regressor = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1),
            nn.ReLU(),  # Crime counts / risk intensities are non-negative
        )

    def forward(
        self,
        x_seq: torch.Tensor,
        edge_index: torch.Tensor,
        edge_weight: torch.Tensor = None,
    ) -> torch.Tensor:
        """
        Args:
            x_seq: [seq_len, num_nodes, in_channels]
            edge_index: [2, num_edges]
            edge_weight: [num_edges] or [num_edges, 1]
        Returns:
            pred_risk: [num_nodes] predicted crime intensity at time t+1
        """
        seq_len, num_nodes, _ = x_seq.shape

        # Squeeze edge weights if necessary
        ew = edge_weight.squeeze(-1) if edge_weight is not None and edge_weight.dim() > 1 else edge_weight

        # 1. Spatial convolutions across each temporal slice in the lookback window
        spatial_features = []
        for t in range(seq_len):
            h = self.gcn1(x_seq[t], edge_index, edge_weight=ew)
            h = self.relu(h)
            h = self.dropout(h)
            h = self.gcn2(h, edge_index, edge_weight=ew)
            h = self.relu(h)
            spatial_features.append(h)

        # [num_nodes, seq_len, hidden_dim]
        temporal_input = torch.stack(spatial_features, dim=1)

        # 2. Temporal sequence modeling with GRU
        gru_out, _ = self.gru(temporal_input)

        # Use final temporal step representation
        last_hidden = gru_out[:, -1, :]  # [num_nodes, hidden_dim]

        # 3. Risk prediction per intersection
        pred_risk = self.regressor(last_hidden).squeeze(-1)  # [num_nodes]
        return pred_risk


# ---------------------------------------------------------------------------
# Spatiotemporal Temporal Grid Formulation
# ---------------------------------------------------------------------------
def build_spatiotemporal_grid(
    city: str,
    graph_dict: Dict[str, torch.Tensor],
    time_bin: str = "biweekly",
) -> Tuple[np.ndarray, List[pd.Timestamp]]:
    """
    Maps historical crime incidents to graph vertices and discretizes them into
    regular temporal intervals Y in R^{T x N}.
    """
    parquet_path = PROCESSED_DIR / f"{city}_fused_matrix.parquet"
    if not parquet_path.exists():
        parquet_path = PROCESSED_DIR / f"{city}_mo_full.parquet"

    logger.info("Loading incident data from %s...", parquet_path.name)
    df = pd.read_parquet(parquet_path)
    df["dt"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["dt", "latitude", "longitude"])
    df = df[(df["latitude"] != 0) & (df["longitude"] != 0)]
    df = df.sort_values("dt").reset_index(drop=True)

    logger.info("Loaded %d valid incidents between %s and %s", len(df), df["dt"].min().date(), df["dt"].max().date())

    # Map incidents to nearest graph node via UTM projection and 2D spatial KDTree
    crs_map = {
        "sf": "EPSG:32610",
        "chicago": "EPSG:32616",
    }
    crs_code = crs_map.get(city, "EPSG:32616")
    transformer = pyproj.Transformer.from_crs("EPSG:4326", crs_code, always_xy=True)
    inc_x, inc_y = transformer.transform(df["longitude"].values, df["latitude"].values)

    pos = graph_dict["pos"].cpu().numpy()  # [num_nodes, 2] -> [easting_m, northing_m]
    kdtree = cKDTree(pos)
    _, nearest_nodes = kdtree.query(np.column_stack([inc_x, inc_y]))
    df["node_idx"] = nearest_nodes

    # Define temporal resample bins
    freq_map = {
        "daily": "1D",
        "weekly": "7D",
        "biweekly": "14D",
        "monthly": "30D",
    }
    freq = freq_map.get(time_bin, "14D")
    df["time_slice"] = df["dt"].dt.floor(freq)

    unique_slices = sorted(df["time_slice"].unique())
    num_slices = len(unique_slices)
    num_nodes = graph_dict["num_nodes"]

    logger.info("Discretized incidents into %d %s temporal steps across %d nodes", num_slices, time_bin, num_nodes)

    # Initialize Y matrix [T, N]
    Y = np.zeros((num_slices, num_nodes), dtype=np.float32)
    slice_to_idx = {ts: idx for idx, ts in enumerate(unique_slices)}

    grouped = df.groupby(["time_slice", "node_idx"]).size().reset_index(name="count")
    for _, row in grouped.iterrows():
        t_idx = slice_to_idx[row["time_slice"]]
        n_idx = int(row["node_idx"])
        Y[t_idx, n_idx] = float(row["count"])

    logger.info("Spatial-temporal grid Y built: shape=%s (non-zero incident points: %d)", Y.shape, np.count_nonzero(Y))
    return Y, unique_slices


# ---------------------------------------------------------------------------
# Training Dataset Generator
# ---------------------------------------------------------------------------
def create_temporal_sequences(
    Y: np.ndarray,
    static_x: np.ndarray,
    seq_len: int = 6,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Creates rolling window sequences for time-series forecasting:
    - Input: X_seq [num_samples, seq_len, num_nodes, in_channels]
    - Target: Y_target [num_samples, num_nodes]
    """
    T, N = Y.shape
    num_samples = T - seq_len

    if num_samples <= 0:
        raise ValueError(f"Sequence length ({seq_len}) must be smaller than total time steps ({T})")

    X_list = []
    Y_list = []

    # static_x: [N, 26]
    for t in range(num_samples):
        # Historical dynamic counts: [seq_len, N, 1]
        y_hist = Y[t: t + seq_len, :, np.newaxis]
        # Broadcast static features across seq_len: [seq_len, N, 26]
        static_repeated = np.repeat(static_x[np.newaxis, :, :], seq_len, axis=0)
        # Concatenate: [seq_len, N, 27]
        sample_x = np.concatenate([static_repeated, y_hist], axis=-1)

        # Target: incident counts at step t + seq_len: [N]
        sample_y = Y[t + seq_len, :]

        X_list.append(sample_x)
        Y_list.append(sample_y)

    X_seq = torch.tensor(np.array(X_list), dtype=torch.float32)
    Y_target = torch.tensor(np.array(Y_list), dtype=torch.float32)
    return X_seq, Y_target


# ---------------------------------------------------------------------------
# Weighted Loss for Zero-Inflated Urban Crimes
# ---------------------------------------------------------------------------
class WeightedMSELoss(nn.Module):
    """
    Weighted MSE Loss to handle spatial sparsity in urban crime graphs.
    Penalizes prediction errors on active crime intersections higher than inactive ones.
    """

    def __init__(self, positive_weight: float = 5.0):
        super().__init__()
        self.positive_weight = positive_weight

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        weights = torch.ones_like(target)
        weights[target > 0] = self.positive_weight
        loss = weights * (pred - target) ** 2
        return loss.mean()


# ---------------------------------------------------------------------------
# Main Training Loop
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="D.H.A.R.M.A. Spatio-Temporal GNN (ST-GCN) Trainer")
    parser.add_argument("--city", default="sf", choices=["chicago", "sf"], help="Target city")
    parser.add_argument("--epochs", type=int, default=15, help="Number of training epochs")
    parser.add_argument("--hidden-dim", type=int, default=64, help="GCN and GRU hidden dimensions")
    parser.add_argument("--lr", type=float, default=0.003, help="Learning rate")
    parser.add_argument("--resume", action="store_true", help="Resume/fine-tune from existing best model checkpoint")
    parser.add_argument("--seq-len", type=int, default=6, help="Lookback window length (historical time steps)")
    parser.add_argument("--time-bin", default="biweekly", choices=["daily", "weekly", "biweekly", "monthly"], help="Temporal resolution")
    parser.add_argument("--pos-weight", type=float, default=15.0, help="Loss weight on non-zero crime intersections")
    parser.add_argument("--patience", type=int, default=3, help="Early stopping patience (epochs without validation loss improvement)")
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"], help="Hardware acceleration device")
    args = parser.parse_args()

    # Determine device
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)

    print("=" * 78)
    print("  PROJECT D.H.A.R.M.A. — SPATIO-TEMPORAL GNN (ST-GCN) TRAINING ENGINE")
    print("=" * 78)
    logger.info("Target City: %s | Device: %s | Epochs: %d | Hidden Dim: %d", args.city.upper(), device, args.epochs, args.hidden_dim)

    # 1. Load Road Network Graph Tensor
    graph_path = GRAPHS_DIR / f"graph_{args.city}.pt"
    if not graph_path.exists():
        logger.error("Graph tensor not found at %s. Please run network_graph_builder.py first.", graph_path)
        sys.exit(1)

    logger.info("Loading graph tensor from %s...", graph_path.name)
    graph_dict = torch.load(graph_path, weights_only=True)
    num_nodes = graph_dict["num_nodes"]
    edge_index = graph_dict["edge_index"].to(device)
    edge_attr = graph_dict["edge_attr"].to(device)
    static_x = graph_dict["x"].numpy()  # [N, 26]

    logger.info("Graph loaded: %d nodes, %d edges, %d static features", num_nodes, edge_index.shape[1], static_x.shape[1])

    # 2. Build Spatiotemporal Grid
    Y_grid, time_slices = build_spatiotemporal_grid(args.city, graph_dict, time_bin=args.time_bin)

    # 3. Create Rolling Window Sequences
    logger.info("Generating lookback sequences (seq_len=%d)...", args.seq_len)
    X_seqs, Y_targets = create_temporal_sequences(Y_grid, static_x, seq_len=args.seq_len)
    num_samples = len(X_seqs)
    logger.info("Total temporal sequence samples: %d", num_samples)

    # 4. Chronological Train / Val / Test Split (70% train, 15% val, 15% test)
    n_train = int(num_samples * 0.70)
    n_val = int(num_samples * 0.15)
    n_test = num_samples - n_train - n_val

    X_train, Y_train = X_seqs[:n_train], Y_targets[:n_train]
    X_val, Y_val = X_seqs[n_train: n_train + n_val], Y_targets[n_train: n_train + n_val]
    X_test, Y_test = X_seqs[n_train + n_val:], Y_targets[n_train + n_val:]

    logger.info("Dataset Split: %d Train | %d Validation | %d Test", len(X_train), len(X_val), len(X_test))

    # 5. Initialize Model, Optimizer, and Loss
    in_channels = static_x.shape[1] + 1  # 26 static features + 1 dynamic count = 27
    model = CrimeSTGCN(
        in_channels=in_channels,
        hidden_dim=args.hidden_dim,
        num_gru_layers=2,
        dropout=0.2,
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2)
    criterion = WeightedMSELoss(positive_weight=args.pos_weight)

    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info("Initialized CrimeSTGCN: %d trainable parameters", total_params)

    # 6. Training Loop
    best_val_loss = float("inf")
    best_epoch = 0
    patience_counter = 0
    training_history = []
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    best_model_path = MODELS_DIR / f"stgcn_{args.city}_best.pt"

    if args.resume:
        if best_model_path.exists():
            logger.info("Resuming/fine-tuning from checkpoint: %s", best_model_path)
            model.load_state_dict(torch.load(best_model_path, weights_only=True, map_location=device))
            # Calculate baseline validation loss on checkpoint
            model.eval()
            with torch.no_grad():
                init_val_losses = []
                for i in range(len(X_val)):
                    x_s = X_val[i].to(device)
                    y_s = Y_val[i].to(device)
                    p_s = model(x_s, edge_index, edge_attr)
                    l_s = criterion(p_s, y_s)
                    init_val_losses.append(l_s.item())
                best_val_loss = float(np.mean(init_val_losses))
            logger.info("Resumed baseline Val Loss: %.5f", best_val_loss)
        else:
            logger.warning("Checkpoint %s not found. Training from scratch.", best_model_path)

    print("\n" + "-" * 78)
    print(f"{'Epoch':<8} | {'Train Loss':<12} | {'Val Loss':<12} | {'Val RMSE':<10} | {'Val MAE':<10} | {'Time':<8}")
    print("-" * 78)

    t_train_start = time.time()

    for epoch in range(1, args.epochs + 1):
        t_epoch_start = time.time()

        # Training Phase
        model.train()
        train_losses = []
        for i in range(len(X_train)):
            x_sample = X_train[i].to(device)  # [seq_len, num_nodes, 27]
            y_sample = Y_train[i].to(device)  # [num_nodes]

            optimizer.zero_grad()
            pred = model(x_sample, edge_index, edge_attr)
            loss = criterion(pred, y_sample)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_losses.append(loss.item())

        epoch_train_loss = float(np.mean(train_losses))

        # Validation Phase
        model.eval()
        val_losses = []
        val_errors = []
        with torch.no_grad():
            for i in range(len(X_val)):
                x_val = X_val[i].to(device)
                y_val = Y_val[i].to(device)

                pred = model(x_val, edge_index, edge_attr)
                loss = criterion(pred, y_val)
                val_losses.append(loss.item())
                val_errors.append((pred - y_val).cpu().numpy())

        epoch_val_loss = float(np.mean(val_losses))
        all_errors = np.concatenate(val_errors)
        val_rmse = float(np.sqrt(np.mean(all_errors ** 2)))
        val_mae = float(np.mean(np.abs(all_errors)))
        epoch_time = time.time() - t_epoch_start

        scheduler.step(epoch_val_loss)

        # Checkpoint if best
        is_best = epoch_val_loss < best_val_loss
        if is_best:
            best_val_loss = epoch_val_loss
            best_epoch = epoch
            patience_counter = 0
            # Save pure tensor state dict (weights_only=True compatible)
            torch.save(model.state_dict(), best_model_path)
        else:
            patience_counter += 1

        star = "★" if is_best else " "
        print(f"{epoch:<8d} | {epoch_train_loss:<12.5f} | {epoch_val_loss:<12.5f} | {val_rmse:<10.4f} | {val_mae:<10.4f} | {epoch_time:<6.1f}s {star}")

        training_history.append({
            "epoch": epoch,
            "train_loss": round(epoch_train_loss, 5),
            "val_loss": round(epoch_val_loss, 5),
            "val_rmse": round(val_rmse, 4),
            "val_mae": round(val_mae, 4),
            "epoch_time_seconds": round(epoch_time, 2),
        })

        if patience_counter >= args.patience:
            logger.info("Early stopping triggered at epoch %d (no val_loss improvement for %d consecutive epochs).", epoch, args.patience)
            break

    total_training_time = time.time() - t_train_start
    print("-" * 78)
    logger.info("Training complete in %.1f seconds. Best Epoch: #%d (Val Loss: %.5f)", total_training_time, best_epoch, best_val_loss)

    # 7. Final Test Evaluation on Hold-Out Data
    logger.info("Evaluating best model on hold-out Test Set (%d samples)...", len(X_test))
    model.load_state_dict(torch.load(best_model_path, weights_only=True))
    model.eval()

    test_losses = []
    test_errors = []
    top_k_hits = []

    with torch.no_grad():
        for i in range(len(X_test)):
            x_test = X_test[i].to(device)
            y_test = Y_test[i].to(device)

            pred = model(x_test, edge_index, edge_attr)
            loss = criterion(pred, y_test)
            test_losses.append(loss.item())

            err = (pred - y_test).cpu().numpy()
            test_errors.append(err)

            # Top-15 hotspot hit-rate: Do top predicted nodes experience actual crimes?
            top_pred_nodes = torch.topk(pred, k=min(15, num_nodes)).indices.cpu().numpy()
            actual_crime_nodes = torch.where(y_test > 0)[0].cpu().numpy()
            if len(actual_crime_nodes) > 0:
                hits = len(set(top_pred_nodes).intersection(set(actual_crime_nodes)))
                top_k_hits.append(hits / min(15, len(actual_crime_nodes)))

    all_test_errors = np.concatenate(test_errors)
    test_rmse = float(np.sqrt(np.mean(all_test_errors ** 2)))
    test_mae = float(np.mean(np.abs(all_test_errors)))
    avg_top_k_hit_rate = float(np.mean(top_k_hits) * 100.0) if top_k_hits else 0.0

    print("\n" + "=" * 78)
    print("  FINAL HOLD-OUT TEST RESULTS (CRIME RISK FORECASTING)")
    print("=" * 78)
    print(f"  Hold-Out Test RMSE           : {test_rmse:.4f}")
    print(f"  Hold-Out Test MAE            : {test_mae:.4f}")
    print(f"  Top-15 Intersection Hit Rate : {avg_top_k_hit_rate:.1f}%")
    print(f"  Best Model Saved To          : {best_model_path}")
    print("=" * 78)

    # 8. Save Training Log & Config
    log_path = MODELS_DIR / f"stgcn_{args.city}_log.json"
    with open(log_path, "w") as f:
        json.dump(training_history, f, indent=2)

    config_path = MODELS_DIR / f"stgcn_{args.city}_config.json"
    config_data = {
        "model_type": "CrimeSTGCN",
        "city": args.city,
        "in_channels": in_channels,
        "hidden_dim": args.hidden_dim,
        "num_gru_layers": 2,
        "dropout": 0.2,
        "num_nodes": num_nodes,
        "num_edges": edge_index.shape[1],
        "seq_len": args.seq_len,
        "time_bin": args.time_bin,
        "best_epoch": best_epoch,
        "best_val_loss": round(best_val_loss, 5),
        "test_rmse": round(test_rmse, 4),
        "test_mae": round(test_mae, 4),
        "top_15_hit_rate_pct": round(avg_top_k_hit_rate, 1),
        "model_file": str(best_model_path),
        "training_time_seconds": round(total_training_time, 1),
    }
    with open(config_path, "w") as f:
        json.dump(config_data, f, indent=2)

    logger.info("Saved ST-GCN configuration to %s", config_path)
    logger.info("Saved training history log to %s", log_path)


if __name__ == "__main__":
    main()
