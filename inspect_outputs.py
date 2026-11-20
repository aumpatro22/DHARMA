#!/usr/bin/env python3
"""
inspect_outputs.py — Root CLI entrypoint
Delegates to scripts/inspect_outputs.py for clean modular architecture.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.inspect_outputs import main

if __name__ == "__main__":
    main()
