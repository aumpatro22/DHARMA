#!/usr/bin/env python3
"""
groq_mo_extractor.py — Root CLI entrypoint for Project D.H.A.R.M.A. Groq M.O. Extraction
Delegates to dharma.nlp.extractor for clean domain architecture.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dharma.nlp.extractor import GroqMOExtractor, main

if __name__ == "__main__":
    main()
