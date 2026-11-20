#!/bin/bash
# Master Dataset Ingestion & M.O. Extraction Runner (LAPD & Houston NIBRS)
set -e

echo "=== [$(date)] Resuming Dataset Batch Inference (LAPD & Houston NIBRS) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
export PYTHONPATH="$PROJECT_DIR:${PYTHONPATH:-}"

# 1. LAPD Crime Data (3.14M rows) ~ 25 mins
echo "--- [$(date)] Processing LAPD Crime Data (3.14M rows) ---"
python3 -m dharma.batch.batch_infer \
  --input "/home/aumpatro/DataSet/LAPD_Crime_Data_2020_Present.csv" \
  --output "$PROJECT_DIR/processed/lapd_mo_full.parquet" \
  --chunksize 1000000

# 2. Houston NIBRS Logs (1.52M rows) ~ 12 mins
echo "--- [$(date)] Processing Houston NIBRS Logs (1.52M rows) ---"
python3 -m dharma.batch.batch_infer \
  --input "/home/aumpatro/DataSet/Houston_NIBRS_Data.csv" \
  --output "$PROJECT_DIR/processed/houston_mo_full.parquet" \
  --chunksize 1000000

echo "=== [$(date)] ALL NATIONAL DATASETS FULLY PROCESSED INTO PARQUET MATRICES ==="
