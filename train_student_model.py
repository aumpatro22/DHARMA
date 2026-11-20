#!/usr/bin/env python3
"""
train_student_model.py — Root CLI entrypoint for DistilBERT Student Model Training
Delegates to dharma.nlp.student_trainer for clean domain architecture.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dharma.nlp.student_trainer import MultiHeadDistilBERT, main

if __name__ == "__main__":
    main()
