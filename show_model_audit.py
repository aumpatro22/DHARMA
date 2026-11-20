#!/usr/bin/env python3
"""
show_model_audit.py — Root CLI entrypoint for Project D.H.A.R.M.A. Model Audit
Delegates to scripts/show_model_audit.py for clean modularity.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.show_model_audit import main

if __name__ == "__main__":
    main()
