#!/usr/bin/env python3
"""
test_difficult_scenarios.py — Root entrypoint delegating to tests/test_difficult_scenarios.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.test_difficult_scenarios import main

if __name__ == "__main__":
    main()
