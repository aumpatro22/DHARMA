#!/usr/bin/env python3
"""
network_graph_builder.py — Root CLI entrypoint for Road Network Topology Builder
Delegates to dharma.spatial.graph_builder for clean domain architecture.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dharma.spatial.graph_builder import main

if __name__ == "__main__":
    main()
