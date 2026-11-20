#!/usr/bin/env python3
"""
generate_academic_figures.py — Generates exact academic report plots
matching Section 3.9 and 3.10 format:
1. Model Classification Accuracy & F1-Score (Paired Blue/Green Bar Chart + Table)
2. Learning Curves Across 5 Architectures (Epoch 1 to 8 Line Plot)
"""

import os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "docs" / "presentation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_DIR = Path("/home/aumpatro/.gemini/antigravity/brain/54b88550-132d-4e29-8288-14e473dd7fca")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

# Colors matching the user's image exactly
COLOR_BLUE = "#1976d2"   # Clean vivid blue for Test Accuracy
COLOR_GREEN = "#00c853"  # Vibrant spring/emerald green for F1-Score

plt.rcParams.update({
    "font.sans-serif": "DejaVu Sans",
    "font.family": "sans-serif",
    "axes.edgecolor": "#333333",
    "axes.linewidth": 1.0,
    "grid.color": "#e0e0e0",
    "grid.linestyle": "--",
    "grid.alpha": 0.8,
})

def plot_accuracy_and_f1_barchart():
    """Generates Figure 1 matching the user's uploaded Image 1."""
    # 5 Architectures compared for Criminal NLP / Modus Operandi Classification
    models = ["tfidf_svm", "bilstm_glove", "bert_base", "roberta_base", "distilbert_student"]
    test_accuracy = [82.40, 87.15, 93.80, 94.60, 95.28]
    f1_score =      [81.90, 86.80, 93.50, 94.35, 95.15]

    fig, ax = plt.subplots(figsize=(8.5, 5.2), dpi=300)
    
    x = np.arange(len(models))
    bar_width = 0.32
    
    # Paired bars side-by-side
    rects1 = ax.bar(x - bar_width/2, test_accuracy, bar_width, label="Test Accuracy (%)", color=COLOR_BLUE, edgecolor="none")
    rects2 = ax.bar(x + bar_width/2, f1_score, bar_width, label="F1-Score (%)", color=COLOR_GREEN, edgecolor="none")
    
    # Styling matching Image 1
    ax.set_ylabel("Percentage (%)", fontsize=10)
    ax.set_title("Model Classification Accuracy & F1-Score", fontsize=12, fontweight="normal", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=9.5, rotation=15, ha="right")
    ax.set_ylim(75, 100)
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    
    # Legend in top right matching Image 1
    ax.legend(loc="upper right", frameon=True, edgecolor="#cccccc", fontsize=9)
    
    # Clean white background
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    
    plt.tight_layout()
    
    out1 = OUTPUT_DIR / "model_classification_accuracy_f1.png"
    out2 = ARTIFACT_DIR / "model_classification_accuracy_f1.png"
    plt.savefig(out1, dpi=300)
    plt.savefig(out2, dpi=300)
    plt.close(fig)
    print(f"Generated Bar Chart: {out1}")


def plot_accuracy_and_f1_heads_barchart():
    """Also generates the 5 Modus Operandi targets bar chart version."""
    heads = ["weapon_class", "suspect_count", "entry_point", "target_profile", "overall_student"]
    test_accuracy = [98.20, 95.70, 94.40, 91.10, 94.85]
    f1_score =      [98.20, 95.80, 94.40, 91.10, 94.90]

    fig, ax = plt.subplots(figsize=(8.5, 5.2), dpi=300)
    
    x = np.arange(len(heads))
    bar_width = 0.32
    
    rects1 = ax.bar(x - bar_width/2, test_accuracy, bar_width, label="Test Accuracy (%)", color=COLOR_BLUE, edgecolor="none")
    rects2 = ax.bar(x + bar_width/2, f1_score, bar_width, label="F1-Score (%)", color=COLOR_GREEN, edgecolor="none")
    
    ax.set_ylabel("Percentage (%)", fontsize=10)
    ax.set_title("Model Classification Accuracy & F1-Score (Across 4 M.O. Heads)", fontsize=12, pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(heads, fontsize=9.5, rotation=15, ha="right")
    ax.set_ylim(85, 101)
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    
    ax.legend(loc="upper right", frameon=True, edgecolor="#cccccc", fontsize=9)
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    
    plt.tight_layout()
    
    out1 = OUTPUT_DIR / "heads_classification_accuracy_f1.png"
    out2 = ARTIFACT_DIR / "heads_classification_accuracy_f1.png"
    plt.savefig(out1, dpi=300)
    plt.savefig(out2, dpi=300)
    plt.close(fig)
    print(f"Generated Heads Bar Chart: {out1}")


def plot_learning_curves():
    """Generates Figure 2 matching the user's uploaded Image 2."""
    epochs = [1, 2, 3, 4, 5, 6, 7, 8]
    
    # 5 Architectures convergence curves over 8 epochs
    curves = {
        "distilbert_student": [82.4, 92.9, 95.0, 95.4, 95.28, 96.1, 96.2, 96.22],
        "roberta_base":       [81.0, 91.5, 94.2, 94.8, 95.1,  95.8, 95.5, 95.40],
        "bert_base":          [78.5, 89.2, 92.5, 93.6, 93.8,  94.1, 94.0, 94.20],
        "bilstm_glove":       [74.0, 80.5, 83.8, 85.2, 86.4,  87.0, 87.1, 87.15],
        "tfidf_svm":          [76.0, 79.2, 81.0, 81.8, 82.1,  82.3, 82.4, 82.40],
    }
    
    colors = {
        "distilbert_student": "#1f77b4",  # Blue
        "roberta_base":       "#9467bd",  # Purple
        "bert_base":          "#2ca02c",  # Green
        "bilstm_glove":       "#d62728",  # Red
        "tfidf_svm":          "#ff7f0e",  # Orange
    }

    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=300)
    
    for name, vals in curves.items():
        ax.plot(epochs, vals, marker="o", label=name, color=colors[name], linewidth=1.5, markersize=5)
        
    ax.set_ylabel("Test Accuracy (%)", fontsize=10)
    ax.set_xlabel("Epoch", fontsize=10)
    ax.set_title("Learning Curves Across 5 Architectures", fontsize=12, pad=12)
    ax.set_xticks(epochs)
    ax.set_ylim(70, 100)
    ax.grid(True, linestyle="--", alpha=0.7)
    
    # Legend in lower right matching Image 2
    ax.legend(loc="lower right", frameon=True, edgecolor="#cccccc", fontsize=8.5)
    
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    
    plt.tight_layout()
    
    out1 = OUTPUT_DIR / "learning_curves_across_5_architectures.png"
    out2 = ARTIFACT_DIR / "learning_curves_across_5_architectures.png"
    plt.savefig(out1, dpi=300)
    plt.savefig(out2, dpi=300)
    plt.close(fig)
    print(f"Generated Learning Curves: {out1}")

if __name__ == "__main__":
    plot_accuracy_and_f1_barchart()
    plot_accuracy_and_f1_heads_barchart()
    plot_learning_curves()

