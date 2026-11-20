#!/usr/bin/env python3
"""
pipeline.py — Root CLI entrypoint for Project D.H.A.R.M.A. Master Pipeline
Delegates to dharma.batch.pipeline for clean domain architecture.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dharma.batch.pipeline import main

if __name__ == "__main__":
    main()
