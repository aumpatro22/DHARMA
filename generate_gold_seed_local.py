#!/usr/bin/env python3
"""
generate_gold_seed_local.py — Root CLI entrypoint
Delegates to scripts/generate_gold_seed_local.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate_gold_seed_local import main

if __name__ == "__main__":
    main()
