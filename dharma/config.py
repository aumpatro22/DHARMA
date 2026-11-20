"""
dharma.config — Centralized Configuration & Path Resolver for Project D.H.A.R.M.A.

Replaces hardcoded environment paths with deterministic, relative anchor paths.
Works identically across developer workstations, Docker containers, and CI pipelines.
"""

from pathlib import Path
import os
import sys

# Project root: parent of the `dharma` package
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Core asset directories
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = PROJECT_ROOT / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
DISTILBERT_DIR = MODELS_DIR / "distilbert_mo_student"
GNN_MODELS_DIR = MODELS_DIR / "gnn"
GRAPHS_DIR = PROCESSED_DIR / "graphs"
LOGS_DIR = PROJECT_ROOT / "logs"
CACHE_DIR = PROJECT_ROOT / "cache"
STATIC_DIR = PROJECT_ROOT / "static"
DOCS_DIR = PROJECT_ROOT / "docs"
EXTERNAL_DATASET_DIR = Path(os.getenv("DHARMA_DATASET_DIR", "/home/aumpatro/DataSet" if Path("/home/aumpatro/DataSet").exists() else str(DATA_DIR)))

# Ensure runtime directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Central threading defaults for multi-core Xeon / CPU execution
DEFAULT_NUM_CORES = min(os.cpu_count() or 4, 24)
