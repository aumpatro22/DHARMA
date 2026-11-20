#!/usr/bin/env python3
"""
inspect_outputs.py — Project D.H.A.R.M.A. Output Explorer & Live Inspector

Quickly inspect all processed Parquet matrices, model training logs, QA test runs,
or test live model inference on custom crime text.

Usage:
    python3 inspect_outputs.py --summary
    python3 inspect_outputs.py --sample chicago_fused --n 5
    python3 inspect_outputs.py --sample nypd --n 3
    python3 inspect_outputs.py --test-results --n 3
    python3 inspect_outputs.py --predict "Suspect kicked rear window of bank and fled with handgun."
    python3 inspect_outputs.py --serve-deck 8080
"""

import os
import sys
import json
import argparse
from pathlib import Path

try:
    from dharma.config import PROJECT_ROOT, PROCESSED_DIR, DISTILBERT_DIR as MODELS_DIR
    BASE_DIR = PROJECT_ROOT
except ImportError:
    BASE_DIR = Path(__file__).resolve().parent.parent
    PROCESSED_DIR = BASE_DIR / "processed"
    MODELS_DIR = BASE_DIR / "models" / "distilbert_mo_student"

DATASETS = {
    "chicago_fused": PROCESSED_DIR / "chicago_fused_matrix.parquet",
    "sf_fused": PROCESSED_DIR / "sf_fused_matrix.parquet",
    "chicago_mo": PROCESSED_DIR / "chicago_mo_full.parquet",
    "sf_mo": PROCESSED_DIR / "sf_mo_full.parquet",
    "houston": PROCESSED_DIR / "houston_mo_full.parquet",
    "lapd": PROCESSED_DIR / "lapd_mo_full.parquet",
    "nypd": PROCESSED_DIR / "nypd_mo_full.parquet",
    "uk": PROCESSED_DIR / "uk_mo_full.parquet",
}

def print_banner(title: str):
    print("\n" + "=" * 75)
    print(f"  {title}")
    print("=" * 75)

def show_summary():
    import pyarrow.parquet as pq
    print_banner("PROJECT D.H.A.R.M.A. — PROCESSED OUTPUTS INVENTORY")
    total_records = 0
    total_size_mb = 0

    print(f"{'Key':<15} | {'File Name':<30} | {'Rows':>12} | {'Cols':>5} | {'Size (MB)':>10}")
    print("-" * 80)
    for key, path in DATASETS.items():
        if path.exists():
            meta = pq.read_metadata(str(path))
            sz = path.stat().st_size / (1024 * 1024)
            total_records += meta.num_rows
            total_size_mb += sz
            print(f"{key:<15} | {path.name:<30} | {meta.num_rows:>12,d} | {meta.num_columns:>5d} | {sz:>10.2f} MB")
        else:
            print(f"{key:<15} | {path.name:<30} | {'[NOT FOUND]':>12}")

    print("-" * 80)
    print(f"{'TOTAL':<15} | {'8 Parquet Matrices':<30} | {total_records:>12,d} | {'-':>5} | {total_size_mb:>10.2f} MB")

    # Training Log
    train_log = MODELS_DIR / "training_log.json"
    if train_log.exists():
        print_banner("STUDENT MODEL TRAINING CONVERGENCE (models/distilbert_mo_student)")
        with open(train_log) as f:
            log_data = json.load(f)
        for ep in log_data:
            print(f"  Epoch {ep['epoch']}: Train Loss = {ep['train_loss']:.4f} | Val Loss = {ep['val_loss']:.4f} | Avg Val Acc = {ep['avg_accuracy']*100:.1f}%")

    # PyG Graph Tensors
    graphs_dir = PROCESSED_DIR / "graphs"
    if graphs_dir.exists():
        graph_files = list(graphs_dir.glob("*.json"))
        if graph_files:
            print_banner("ROAD NETWORK PYG GRAPH TENSORS (processed/graphs)")
            print(f"{'City':<12} | {'Nodes':>10} | {'Edges':>10} | {'Feature Dim':>12} | {'File Size':>10}")
            print("-" * 65)
            for gf in graph_files:
                with open(gf) as f:
                    meta = json.load(f)
                pt_file = Path(meta["graph_file"])
                sz = pt_file.stat().st_size / (1024 * 1024) if pt_file.exists() else 0.0
                print(f"{meta['city']:<12} | {meta['num_nodes']:>10,d} | {meta['num_edges']:>10,d} | {meta['feature_dim']:>12d} | {sz:>9.2f} MB")

    # Spatio-Temporal GNN Models
    gnn_dir = BASE_DIR / "models" / "gnn"
    if gnn_dir.exists():
        gnn_configs = list(gnn_dir.glob("*_config.json"))
        if gnn_configs:
            print_banner("SPATIO-TEMPORAL GNN MODELS (models/gnn)")
            print(f"{'City':<10} | {'Model':<12} | {'Nodes':>8} | {'Edges':>8} | {'Test RMSE':>10} | {'Test MAE':>10} | {'Top-15 Hit Rate':>16}")
            print("-" * 85)
            for gc in gnn_configs:
                with open(gc) as f:
                    cfg = json.load(f)
                print(f"{cfg['city']:<10} | {cfg['model_type']:<12} | {cfg['num_nodes']:>8,d} | {cfg['num_edges']:>8,d} | {cfg['test_rmse']:>10.4f} | {cfg['test_mae']:>10.4f} | {cfg['top_15_hit_rate_pct']:>15.1f}%")

def show_sample(key: str, n: int = 3):
    import pandas as pd
    if key not in DATASETS:
        print(f"Error: Unknown dataset '{key}'. Available: {list(DATASETS.keys())}")
        return

    path = DATASETS[key]
    if not path.exists():
        print(f"Error: File not found at {path}")
        return

    print_banner(f"SAMPLE {n} ROWS: {path.name}")
    df = pd.read_parquet(str(path))
    pd.set_option('display.max_columns', 25)
    pd.set_option('display.width', 1000)
    print(df.head(n).to_string())

def show_test_results(n: int = 5):
    path = PROCESSED_DIR / "test_results_50.json"
    if not path.exists():
        print(f"Error: Test results file not found at {path}")
        return

    print_banner(f"QA VERIFICATION SUITE — SAMPLE OF {n} TEST CASES")
    with open(path) as f:
        tests = json.load(f)

    for item in tests[:n]:
        print(f"\n--- Test Case #{item.get('test_id', '?')} ---")
        print(f"Raw Input       : {item.get('raw_narrative')}")
        print(f"Anonymized Text : {item.get('anonymized_text')}")
        print(f"Redactions Count: {item.get('redactions_count')}")
        mo = item.get('mo_payload', {}).get('modus_operandi', {})
        print(f"Extracted M.O.  : Weapon={mo.get('weapon_classification')} | Entry={mo.get('point_of_entry')} | Target={mo.get('target_profile')} | Suspects={mo.get('suspect_count_estimate')}")

def run_prediction(narrative: str):
    import torch
    from transformers import AutoTokenizer
    try:
        from dharma.nlp.student_trainer import MultiHeadDistilBERT
    except ImportError:
        from train_student_model import MultiHeadDistilBERT

    print_banner("RUNNING LIVE STUDENT MODEL INFERENCE")
    print(f"Input Narrative:\n  \"{narrative}\"\n")

    with open(MODELS_DIR / "config.json") as f:
        cfg = json.load(f)

    tokenizer = AutoTokenizer.from_pretrained(MODELS_DIR)
    model = MultiHeadDistilBERT(cfg['num_classes'])
    model.load_state_dict(torch.load(MODELS_DIR / "model.pt", map_location="cpu"))
    model.eval()

    inputs = tokenizer(narrative, return_tensors="pt", max_length=256, truncation=True)
    with torch.no_grad():
        preds = model(inputs["input_ids"], inputs["attention_mask"])

    inv = cfg["inverse_label_maps"]
    print("Forensic M.O. Classification Output:")
    print("-" * 65)
    for head, logits in preds.items():
        pred_idx = str(torch.argmax(logits, dim=1).item())
        label = inv[head].get(pred_idx, "UNKNOWN")
        prob = torch.softmax(logits, dim=1).max().item()
        bar_len = int(prob * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        print(f"  {head:<25} : {label:<16} [{bar}] {prob*100:>5.1f}%")
    print("-" * 65)

def serve_deck(port: int = 8080):
    import http.server
    import socketserver
    import webbrowser

    os.chdir(BASE_DIR)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}/presentation.html"
        print_banner(f"INTERACTIVE PRESENTATION SERVER RUNNING ON PORT {port}")
        print(f"  Open in your browser: {url}")
        print("  Press Ctrl+C to stop.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

def main():
    parser = argparse.ArgumentParser(description="Project D.H.A.R.M.A. Output Inspector")
    parser.add_argument("--summary", action="store_true", help="Print overall processed inventory and model status")
    parser.add_argument("--sample", type=str, choices=list(DATASETS.keys()), help="Print sample rows from a processed dataset")
    parser.add_argument("--n", type=int, default=3, help="Number of rows or test cases to display")
    parser.add_argument("--test-results", action="store_true", help="Show synthetic QA verification test results")
    parser.add_argument("--predict", type=str, help="Run live forensic classification on a crime narrative")
    parser.add_argument("--serve-deck", type=int, nargs="?", const=8080, help="Launch local HTTP server to view presentation.html")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if args.summary:
        show_summary()
    if args.sample:
        show_sample(args.sample, args.n)
    if args.test_results:
        show_test_results(args.n)
    if args.predict:
        run_prediction(args.predict)
    if args.serve_deck:
        serve_deck(args.serve_deck)

if __name__ == "__main__":
    main()
