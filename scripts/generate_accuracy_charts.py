#!/usr/bin/env python3
"""
generate_accuracy_charts.py — Generates publication-grade Bar Chart diagrams
for Project D.H.A.R.M.A. to present to academic evaluators / teachers.
"""

import os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Setup directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "docs" / "presentation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_DIR = Path("/home/aumpatro/.gemini/antigravity/brain/54b88550-132d-4e29-8288-14e473dd7fca")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

# Set high-quality styling
plt.rcParams.update({
    "font.sans-serif": "DejaVu Sans",
    "font.family": "sans-serif",
    "axes.edgecolor": "#cbd5e1",
    "axes.linewidth": 1.2,
    "grid.color": "#e2e8f0",
    "grid.linestyle": "--",
    "grid.alpha": 0.6,
})

def create_main_bar_chart():
    """Generates the main standalone Model Accuracy Bar Chart."""
    fig, ax = plt.subplots(figsize=(11, 6.5), dpi=300)
    
    categories = [
        "Weapon\nClassification\n(6 classes)",
        "Suspect Count\nEstimation\n(4 classes)",
        "Point of Entry\nClassification\n(7 classes)",
        "Target Profile\nIdentification\n(6 classes)",
        "Overall Student\nAverage\n(4,000 queries)",
        "Zero-PII Privacy\nNER Redaction\n(Regex + spaCy)"
    ]
    accuracies = [98.20, 95.70, 94.40, 91.10, 94.85, 100.00]
    colors = ["#2563eb", "#3b82f6", "#0ea5e9", "#06b6d4", "#10b981", "#8b5cf6"]
    
    x = np.arange(len(categories))
    bars = ax.bar(x, accuracies, width=0.55, color=colors, edgecolor="#1e293b", linewidth=1.2, zorder=3)
    
    # 90% target threshold dashed line
    ax.axhline(90.0, color="#ef4444", linestyle=":", linewidth=1.5, zorder=4, label="Baseline Competence Threshold (90.0%)")
    ax.axhline(95.0, color="#10b981", linestyle="--", linewidth=1.5, zorder=4, label="High-Excellence Tier (95.0%)")
    
    # Value annotations on top of bars
    for bar, acc in zip(bars, accuracies):
        yval = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            yval + 1.1,
            f"{acc:.2f}%",
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold",
            color="#0f172a"
        )
    
    ax.set_ylim(80, 105)
    ax.set_ylabel("Empirical Accuracy (%)", fontsize=13, fontweight="bold", labelpad=10, color="#1e293b")
    ax.set_title("Project D.H.A.R.M.A. — Model Evaluation & Accuracy Benchmark\n(Evaluated on 1,000 Unseen Independent Police Records)", 
                 fontsize=15, fontweight="bold", pad=20, color="#0f172a")
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=10, fontweight="bold", color="#334155")
    ax.legend(loc="upper left", framealpha=0.95, fontsize=10)
    ax.grid(axis="y", zorder=0)
    
    # Clean background
    ax.set_facecolor("#f8fafc")
    fig.patch.set_facecolor("#ffffff")
    
    # Save files
    out_path1 = OUTPUT_DIR / "model_accuracy_barchart.png"
    out_path2 = ARTIFACT_DIR / "model_accuracy_barchart.png"
    plt.tight_layout()
    plt.savefig(out_path1, dpi=300)
    plt.savefig(out_path2, dpi=300)
    plt.close(fig)
    print(f"Saved main bar chart to {out_path1} and {out_path2}")

def create_multi_panel_dashboard():
    """Generates a complete 4-panel academic defense chart showing all models."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12), dpi=300)
    fig.suptitle("Project D.H.A.R.M.A. — Comprehensive Multi-Model Performance Audit", 
                 fontsize=18, fontweight="bold", y=0.98, color="#0f172a")

    # ---------------- Panel 1: NLP Student Heads ----------------
    ax1 = axes[0, 0]
    heads = ["Weapon", "Suspects", "Entry Point", "Target Profile", "Overall"]
    head_accs = [98.20, 95.70, 94.40, 91.10, 94.85]
    colors1 = ["#2563eb", "#3b82f6", "#0284c7", "#0ea5e9", "#10b981"]
    bars1 = ax1.bar(heads, head_accs, width=0.5, color=colors1, edgecolor="#1e293b", linewidth=1.1, zorder=3)
    ax1.set_ylim(85, 103)
    ax1.set_ylabel("Accuracy (%)", fontsize=11, fontweight="bold")
    ax1.set_title("1. DistilBERT Student Heads (Holdout Set: 1,000 Records)", fontsize=13, fontweight="bold", pad=10)
    ax1.grid(axis="y", zorder=0)
    ax1.set_facecolor("#f8fafc")
    for bar, val in zip(bars1, head_accs):
        ax1.text(bar.get_x() + bar.get_width() / 2, val + 0.5, f"{val:.2f}%", ha="center", va="bottom", fontweight="bold", fontsize=10)

    # ---------------- Panel 2: 5-Epoch Learning Curve ----------------
    ax2 = axes[0, 1]
    epochs = [1, 2, 3, 4, 5]
    val_accs = [82.40, 92.90, 95.00, 95.40, 95.28]
    val_loss = [3.1688, 1.2898, 0.7736, 0.6159, 0.5806]
    
    # Dual-axis: Accuracy bars and Loss line
    color_bar = "#3b82f6"
    bars2 = ax2.bar(epochs, val_accs, width=0.45, color=color_bar, alpha=0.85, edgecolor="#1e293b", label="Val Accuracy (%)", zorder=3)
    ax2.set_ylabel("Validation Accuracy (%)", fontsize=11, fontweight="bold", color="#1d4ed8")
    ax2.set_ylim(70, 102)
    ax2.set_xlabel("Training Epoch", fontsize=11, fontweight="bold")
    ax2.set_title("2. Training Convergence & Loss Minimization (Epoch 1-5)", fontsize=13, fontweight="bold", pad=10)
    ax2.grid(axis="y", zorder=0)
    ax2.set_facecolor("#f8fafc")
    for bar, val in zip(bars2, val_accs):
        ax2.text(bar.get_x() + bar.get_width() / 2, val + 0.8, f"{val:.1f}%", ha="center", va="bottom", fontweight="bold", fontsize=9)
    
    ax2_twin = ax2.twinx()
    ax2_twin.plot(epochs, val_loss, color="#dc2626", marker="o", linewidth=2.5, markersize=7, label="Validation Loss", zorder=5)
    ax2_twin.set_ylabel("Validation Cross-Entropy Loss", fontsize=11, fontweight="bold", color="#dc2626")
    ax2_twin.set_ylim(0, 3.8)

    # ---------------- Panel 3: Architecture Tradeoffs (Latency vs Accuracy) ----------------
    ax3 = axes[1, 0]
    models = ["Teacher LLM\n(Groq LLaMA-70B)", "Student DistilBERT\n(66M Offline CPU)", "Traditional\nBag-of-Words+SVM"]
    latencies = [3200, 18, 12]  # ms
    model_accs = [100.0, 94.85, 71.40]
    
    x3 = np.arange(len(models))
    width = 0.35
    b_acc = ax3.bar(x3 - width/2, model_accs, width, label="Accuracy (%)", color="#10b981", edgecolor="#1e293b", zorder=3)
    
    ax3.set_ylabel("Accuracy (%)", fontsize=11, fontweight="bold", color="#059669")
    ax3.set_ylim(0, 115)
    ax3.set_xticks(x3)
    ax3.set_xticklabels(models, fontsize=10, fontweight="bold")
    ax3.set_title("3. Teacher vs Student Knowledge Distillation Efficiency", fontsize=13, fontweight="bold", pad=10)
    ax3.grid(axis="y", zorder=0)
    ax3.set_facecolor("#f8fafc")
    
    for bar, val in zip(b_acc, model_accs):
        ax3.text(bar.get_x() + bar.get_width() / 2, val + 2, f"{val:.1f}%", ha="center", va="bottom", fontweight="bold", fontsize=9)
        
    ax3_twin = ax3.twinx()
    b_lat = ax3_twin.bar(x3 + width/2, latencies, width, label="Inference Latency (ms)", color="#f59e0b", edgecolor="#1e293b", zorder=3)
    ax3_twin.set_ylabel("Inference Latency (ms, lower is faster)", fontsize=11, fontweight="bold", color="#d97706")
    ax3_twin.set_yscale("log")
    ax3_twin.set_ylim(1, 10000)
    for bar, val in zip(b_lat, latencies):
        ax3_twin.text(bar.get_x() + bar.get_width() / 2, val * 1.25, f"{val}ms", ha="center", va="bottom", fontweight="bold", fontsize=9)
    
    # ---------------- Panel 4: Spatiotemporal ST-GCN (Chicago vs SF) ----------------
    ax4 = axes[1, 1]
    gnn_cities = ["Chicago Road Graph\n(29,807 Nodes)", "San Francisco Graph\n(10,033 Nodes)", "Random Baseline\nUniform Guess"]
    hit_rates = [31.5, 3.0, 0.05]
    colors4 = ["#6366f1", "#8b5cf6", "#94a3b8"]
    bars4 = ax4.bar(gnn_cities, hit_rates, width=0.5, color=colors4, edgecolor="#1e293b", linewidth=1.1, zorder=3)
    ax4.set_ylabel("Top-15 Hotspot Hit Rate (%)", fontsize=11, fontweight="bold")
    ax4.set_ylim(0, 38)
    ax4.set_title("4. ST-GCN Spatiotemporal Crime Hotspot Prediction", fontsize=13, fontweight="bold", pad=10)
    ax4.grid(axis="y", zorder=0)
    ax4.set_facecolor("#f8fafc")
    
    for bar, val in zip(bars4, hit_rates):
        ax4.text(bar.get_x() + bar.get_width() / 2, val + 1.0, f"{val:.2f}%", ha="center", va="bottom", fontweight="bold", fontsize=10)
        
    # Annotation on Chicago's lift
    ax4.annotate("630× Lift Over Baseline!\n(MAE: 0.0090 due to 98% sparsity)", 
                 xy=(0, 31.5), xytext=(0.4, 25),
                 arrowprops=dict(facecolor="#4f46e5", shrink=0.08, width=1.5, headwidth=6),
                 fontsize=9, fontweight="bold", color="#4338ca",
                 bbox=dict(boxstyle="round,pad=0.4", fc="#e0e7ff", ec="#6366f1", lw=1.2))

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    out_dash1 = OUTPUT_DIR / "full_model_audit_dashboard.png"
    out_dash2 = ARTIFACT_DIR / "full_model_audit_dashboard.png"
    plt.savefig(out_dash1, dpi=300)
    plt.savefig(out_dash2, dpi=300)
    plt.close(fig)
    print(f"Saved full dashboard to {out_dash1} and {out_dash2}")

if __name__ == "__main__":
    create_main_bar_chart()
    create_multi_panel_dashboard()

