#!/usr/bin/env python3
"""
batch_infer_student_maxram.py — Root CLI entrypoint for High-Throughput Batch Inference
Delegates to dharma.batch.batch_infer for clean domain architecture.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dharma.batch.batch_infer import main

if __name__ == "__main__":
    main()
