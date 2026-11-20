#!/usr/bin/env python3
"""
evaluate_test_set.py — Root CLI entrypoint for test set evaluation
Delegates to scripts/evaluate_test_set.py for clean modularity.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluate_test_set import main

if __name__ == "__main__":
    main()
