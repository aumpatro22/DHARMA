#!/bin/bash
# Project D.H.A.R.M.A. — Unattended Resilient Batch Execution Runner
# Designed to run completely detached from interactive SSH terminals with chunk checkpointing.

set -e
trap "" HUP # Ignore hangup signal (SIGHUP) completely

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
export PYTHONPATH="$PROJECT_DIR:${PYTHONPATH:-}"
DATA_DIR="/home/aumpatro/DataSet"
PROCESSED_DIR="$PROJECT_DIR/processed"
LOG_FILE="$PROJECT_DIR/logs/unattended_execution.log"

mkdir -p "$PROCESSED_DIR"

echo "================================================================================" >> "$LOG_FILE"
echo "=== [$(date)] STARTING UNATTENDED RESILIENT BATCH INFERENCE PIPELINE ===" >> "$LOG_FILE"
echo "================================================================================" >> "$LOG_FILE"

# Stage 1: NYPD Arrests (5.98M rows)
echo "--- [$(date)] Stage 1/6: NYPD Arrests ---" >> "$LOG_FILE"
python3 -u "$PROJECT_DIR/batch_infer_student_maxram.py" \
  --input "$DATA_DIR/NYPD_Arrests_Data_(Historic)_20260316.csv" \
  --output "$PROCESSED_DIR/nypd_mo_full.parquet" \
  --chunksize 1000000 \
  --dataset-name "NYPD Historical Arrests" \
  --stage-number 1 \
  --total-stages 6 >> "$LOG_FILE" 2>&1

# Stage 2: UK National Police Forces (9.72M rows)
echo "--- [$(date)] Stage 2/6: UK National Police Forces ---" >> "$LOG_FILE"
python3 -u "$PROJECT_DIR/batch_infer_student_maxram.py" \
  --input "$DATA_DIR/UK_Police_Data.csv" \
  --output "$PROCESSED_DIR/uk_mo_full.parquet" \
  --chunksize 1000000 \
  --dataset-name "UK National Police Forces" \
  --stage-number 2 \
  --total-stages 6 >> "$LOG_FILE" 2>&1

# Stage 3: LAPD Crime Data (3.14M rows)
echo "--- [$(date)] Stage 3/6: LAPD Crime Data ---" >> "$LOG_FILE"
python3 -u "$PROJECT_DIR/batch_infer_student_maxram.py" \
  --input "$DATA_DIR/LAPD_Crime_Data_2020_Present.csv" \
  --output "$PROCESSED_DIR/lapd_mo_full.parquet" \
  --chunksize 1000000 \
  --dataset-name "LAPD Crime Data" \
  --stage-number 3 \
  --total-stages 6 >> "$LOG_FILE" 2>&1

# Stage 4: Houston NIBRS Logs (1.52M rows)
echo "--- [$(date)] Stage 4/6: Houston NIBRS Logs ---" >> "$LOG_FILE"
python3 -u "$PROJECT_DIR/batch_infer_student_maxram.py" \
  --input "$DATA_DIR/Houston_NIBRS_Data.csv" \
  --output "$PROCESSED_DIR/houston_mo_full.parquet" \
  --chunksize 1000000 \
  --dataset-name "Houston NIBRS Logs" \
  --stage-number 4 \
  --total-stages 6 >> "$LOG_FILE" 2>&1

# Stage 5: San Francisco Crimes (10k rows)
echo "--- [$(date)] Stage 5/6: San Francisco Crimes ---" >> "$LOG_FILE"
python3 -u "$PROJECT_DIR/batch_infer_student_maxram.py" \
  --input "$PROJECT_DIR/data/sf_crimes.csv" \
  --output "$PROCESSED_DIR/sf_mo_full.parquet" \
  --chunksize 300000 \
  --dataset-name "San Francisco Crimes" \
  --stage-number 5 \
  --total-stages 6 >> "$LOG_FILE" 2>&1

# Stage 6: Chicago Crimes (10k rows)
echo "--- [$(date)] Stage 6/6: Chicago Crimes ---" >> "$LOG_FILE"
python3 -u "$PROJECT_DIR/batch_infer_student_maxram.py" \
  --input "$PROJECT_DIR/data/chicago_crimes.csv" \
  --output "$PROCESSED_DIR/chicago_mo_full.parquet" \
  --chunksize 600000 \
  --dataset-name "Chicago Crimes" \
  --stage-number 6 \
  --total-stages 6 >> "$LOG_FILE" 2>&1

echo "================================================================================" >> "$LOG_FILE"
echo "=== [$(date)] ALL 6 STAGES COMPLETED SUCCESSFULLY! ===" >> "$LOG_FILE"
echo "================================================================================" >> "$LOG_FILE"
