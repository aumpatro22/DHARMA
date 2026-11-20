#!/bin/bash
# Master Dataset Ingestion & M.O. Extraction Runner - NYPD Stage 1 Only
set -e

echo "=== [$(date)] Starting National Dataset Processing (Stage 1 Only) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
export PYTHONPATH="$PROJECT_DIR:${PYTHONPATH:-}"

# 1. NYPD Arrests (5.98M rows)
echo "--- [$(date)] 1/1 Processing NYPD Arrests (5.98M rows) ---"
python3 -m dharma.batch.batch_infer \
  --input "/home/aumpatro/DataSet/NYPD_Arrests_Data_(Historic)_20260316.csv" \
  --output "$PROJECT_DIR/processed/nypd_mo_full.parquet" \
  --chunksize 1000000

echo "=== [$(date)] STAGE 1 (NYPD 5.98M ROWS) COMPLETED SUCCESSFULLY. STOPPING AS REQUESTED. ==="
