#!/usr/bin/env python3
"""
local_anonymizer.py — Root CLI entrypoint for Project D.H.A.R.M.A. PII Scrubbing
Delegates to dharma.nlp.anonymizer for clean domain architecture.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dharma.nlp.anonymizer import LocalAnonymizer, main, _PATTERNS

if __name__ == "__main__":
    main()
