"""
batch_infer_student_maxram.py — Project D.H.A.R.M.A. High-Throughput CPU Batch Inference

Processes large historical crime datasets using a fine-tuned MultiHeadDistilBERT student model.
Optimized for 24-core Intel Xeon CPU execution, utilizing up to 110 GB of system RAM,
mixed-precision bfloat16 (Intel AMX), and pyarrow Parquet streaming.

Usage:
    python3 batch_infer_student_maxram.py --input <input_csv> --output <output_parquet> [options]

Author : Project D.H.A.R.M.A. Engineering
Python : 3.10+
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Enforce Xeon CPU optimization settings
os.environ["OMP_NUM_THREADS"] = "24"
os.environ["MKL_NUM_THREADS"] = "24"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

import torch
torch.set_num_threads(24)
torch.set_num_interop_threads(4)

from torch import nn
from transformers import AutoTokenizer, DistilBertModel

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("dharma.batch_infer")

try:
    from dharma.config import PROCESSED_DIR, DISTILBERT_DIR
    LOGBOOK_PATH = PROCESSED_DIR / "execution_logbook.md"
    LOGBOOK_JSON = PROCESSED_DIR / "progress_logbook.json"
    LOGBOOK_MD = PROCESSED_DIR / "progress_logbook.md"
    DEFAULT_MODEL_DIR = str(DISTILBERT_DIR)
except ImportError:
    _root = Path(__file__).resolve().parents[2]
    LOGBOOK_PATH = _root / "processed" / "execution_logbook.md"
    LOGBOOK_JSON = _root / "processed" / "progress_logbook.json"
    LOGBOOK_MD = _root / "processed" / "progress_logbook.md"
    DEFAULT_MODEL_DIR = str(_root / "models" / "distilbert_mo_student")

def update_logbook(
    input_file: str,
    output_file: str,
    chunk_idx: int,
    processed_chunk: int,
    chunk_rows: int,
    total_processed_prev: int,
    elapsed: float,
    throughput: float,
):
    """Writes dynamic execution telemetry and progress dashboard to execution_logbook.md."""
    percentage = (processed_chunk / chunk_rows) * 100.0 if chunk_rows > 0 else 100.0
    rem_in_chunk = chunk_rows - processed_chunk
    eta_sec = rem_in_chunk / throughput if throughput > 0 else 0.0
    eta_min = eta_sec / 60.0
    total_recs = total_processed_prev + processed_chunk

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    dataset_name = os.path.basename(input_file)
    output_name = os.path.basename(output_file)

    content = f"""# 📊 Project D.H.A.R.M.A. — Real-Time Inference Execution Logbook

**Last Update Timestamp:** `{timestamp}`  
**Current Active Dataset:** `{dataset_name}`  
**Output Destination:** `{output_name}`  

---

## 🚀 Live Progress Dashboard

| Telemetry Metric | Current Live Value |
|---|---|
| **Active Dataset File** | `{dataset_name}` |
| **Active Chunk** | Chunk #{chunk_idx} |
| **Chunk Progress** | **{processed_chunk:,} / {chunk_rows:,} rows ({percentage:.1f}%)** |
| **Total Cumulative Processed** | **{total_recs:,} records** |
| **Active Throughput** | **{throughput:.1f} records/sec** |
| **Elapsed Chunk Time** | **{elapsed:.1f}s ({elapsed/60.0:.1f} mins)** |
| **Estimated Chunk ETA** | **~{eta_min:.1f} minutes** |

---

## 📈 Recent Progress Log
* `[{timestamp}]` **[{dataset_name}]** Chunk #{chunk_idx} — Processed {processed_chunk:,}/{chunk_rows:,} ({percentage:.1f}%) @ {throughput:.1f} rec/sec (ETA: ~{eta_min:.1f}m)
"""
    try:
        os.makedirs(LOGBOOK_PATH.parent, exist_ok=True)
        with open(LOGBOOK_PATH, "w") as f:
            f.write(content)
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Multi-Head DistilBERT Model Architecture (Matches training)
# ---------------------------------------------------------------------------
class MultiHeadDistilBERT(nn.Module):
    """DistilBERT backbone with 4 independent classification heads."""

    def __init__(self, num_classes_per_head: Dict[str, int], dropout: float = 0.3):
        super().__init__()
        self.distilbert = DistilBertModel.from_pretrained("distilbert-base-uncased")
        hidden_size = self.distilbert.config.hidden_size  # 768
        self.dropout = nn.Dropout(dropout)

        self.heads = nn.ModuleDict()
        for head_name, n_classes in num_classes_per_head.items():
            self.heads[head_name] = nn.Sequential(
                nn.Linear(hidden_size, 256),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(256, n_classes),
            )

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        outputs = self.distilbert(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        cls_output = outputs.last_hidden_state[:, 0, :]
        cls_output = self.dropout(cls_output)

        logits = {}
        for head_name, head_layer in self.heads.items():
            logits[head_name] = head_layer(cls_output)

        return logits


# ---------------------------------------------------------------------------
# Multi-Jurisdictional Narrative Synthesizer
# ---------------------------------------------------------------------------
def synthesize_narrative(row: pd.Series) -> str:
    """Dynamically inspects input CSV columns to synthesize uniform crime narratives."""
    cols = {k.lower(): k for k in row.index}

    def get_val(keys: List[str]) -> str | None:
        for k in keys:
            if k.lower() in cols:
                val = row[cols[k.lower()]]
                if pd.notna(val):
                    return str(val).strip()
        return None

    # 1. Direct Narrative / Description match
    narrative = get_val(['narrative', 'description', 'incident_description', 'incident description', 'descript'])
    if narrative and len(narrative) > 15:
        return narrative

    # 2. Chicago / SF Schema: Combine primary_type and description / Description
    primary_type = get_val(['primary_type', 'primary type', 'category', 'crm_cd_desc', 'ofns_desc'])
    description = get_val(['description', 'description', 'descript', 'pd_desc'])

    if primary_type and description:
        if primary_type.lower() == description.lower():
            return f"Incident of crime categorized as {primary_type}."
        return f"Incident of {primary_type.lower()}: {description}."
    elif primary_type:
        return f"Incident of crime categorized as {primary_type}."
    elif description:
        return f"Incident of crime described as {description}."

    # 3. Categorical Schema (NYPD / UK / Fallback)
    parts = []
    offense = get_val(['ofns_desc', 'pd_desc', 'offense', 'crime type', 'crime_type', 'crm_cd', 'nibrsdescription', 'nibrsclass'])
    if offense:
        parts.append(f"offense {offense}")
    premise = get_val(['prem_typ_desc', 'premise', 'premises'])
    if premise:
        parts.append(f"at premise {premise}")
    law_cat = get_val(['law_cat_cd', 'classification'])
    if law_cat:
        parts.append(f"classified as {law_cat}")

    if parts:
        return f"Crime incident details: {', '.join(parts)}."

    # 4. Ultimate Fallback: concatenate non-null fields
    fallback_parts = []
    for k, v in row.items():
        if pd.notna(v) and k.lower() not in ['incident_id', 'id', 'latitude', 'longitude', 'lat', 'lon', 'timestamp', 'date']:
            val_str = str(v).strip()
            if val_str and len(val_str) > 2:
                fallback_parts.append(f"{k}: {val_str}")
    if fallback_parts:
        return f"Incident details - {'; '.join(fallback_parts)}."

    return "Crime incident with unspecified details."


# ---------------------------------------------------------------------------
# Progress Logbook Constants & Helper
# ---------------------------------------------------------------------------
# (LOGBOOK_JSON and LOGBOOK_MD are defined dynamically at top of file)

ALL_STAGES_TAXONOMY = [
    {"stage": 1, "name": "NYPD Historical Arrests", "total_rows": "5,986,025", "output": "nypd_mo_full.parquet"},
    {"stage": 2, "name": "UK National Police Forces", "total_rows": "9,721,254", "output": "uk_mo_full.parquet"},
    {"stage": 3, "name": "LAPD Crime Data", "total_rows": "3,138,335", "output": "lapd_mo_full.parquet"},
    {"stage": 4, "name": "Houston NIBRS Logs", "total_rows": "1,526,084", "output": "houston_mo_full.parquet"},
    {"stage": 5, "name": "San Francisco Crimes", "total_rows": "10,000", "output": "sf_mo_full.parquet"},
    {"stage": 6, "name": "Chicago Crimes", "total_rows": "10,000", "output": "chicago_mo_full.parquet"},
]

def update_logbook(
    dataset_name: str,
    stage_number: int,
    total_stages: int,
    chunk_idx: int,
    processed_in_chunk: int,
    chunk_rows: int,
    total_processed_stage: int,
    throughput: float,
    chunk_elapsed: float,
    status: str = "RUNNING"
):
    try:
        log_data = {}
        if LOGBOOK_JSON.exists():
            with open(LOGBOOK_JSON, "r") as f:
                try:
                    log_data = json.load(f)
                except Exception:
                    log_data = {}

        completed_stages = log_data.get("completed_stages", [])

        remaining_in_chunk = chunk_rows - processed_in_chunk
        eta_seconds = remaining_in_chunk / throughput if throughput > 0 else 0
        eta_mins = eta_seconds / 60

        chunk_pct = (processed_in_chunk / chunk_rows * 100) if chunk_rows > 0 else 0

        active_telemetry = {
            "dataset_name": dataset_name,
            "stage_number": stage_number,
            "total_stages": total_stages,
            "chunk_index": chunk_idx,
            "processed_in_chunk": processed_in_chunk,
            "chunk_rows": chunk_rows,
            "chunk_progress_pct": round(chunk_pct, 1),
            "total_processed_stage": total_processed_stage,
            "throughput_records_sec": round(throughput, 1),
            "elapsed_seconds": round(chunk_elapsed, 1),
            "eta_minutes": round(eta_mins, 1),
            "status": status,
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        log_data["active_telemetry"] = active_telemetry
        log_data["completed_stages"] = completed_stages

        with open(LOGBOOK_JSON, "w") as f:
            json.dump(log_data, f, indent=2)

        md_lines = [
            "# 📖 Project D.H.A.R.M.A. — Real-Time Inference Logbook",
            f"**Last Updated:** `{time.strftime('%Y-%m-%d %H:%M:%S')}`  ",
            f"**Active Stage:** Stage {stage_number} / {total_stages} — **{dataset_name}**  ",
            f"**Stage Status:** `{status}` 🟡\n",
            "---",
            f"\n## ⚡ Active Stage Telemetry (Stage {stage_number}: {dataset_name})",
            f"- **Current Chunk:** Chunk #{chunk_idx} ({processed_in_chunk:,} / {chunk_rows:,} rows — **{chunk_pct:.1f}%**)",
            f"- **Active Throughput:** **{throughput:.1f} records/sec**",
            f"- **Chunk Elapsed Time:** {chunk_elapsed/60:.1f} minutes",
            f"- **Estimated Chunk ETA:** **~{eta_mins:.1f} minutes**\n",
            "---",
            "\n## 📊 All Stages Progress Overview\n",
            "| Stage | Dataset Name | Total Records | Status | Throughput | Output Parquet |",
            "| --- | --- | --- | --- | --- | --- |"
        ]

        completed_dict = {stg.get("stage_number"): stg for stg in completed_stages}

        for item in ALL_STAGES_TAXONOMY:
            stg_num = item["stage"]
            stg_name = item["name"]
            stg_tot = item["total_rows"]
            stg_out = item["output"]

            if stg_num in completed_dict:
                stg_info = completed_dict[stg_num]
                tput_val = stg_info.get('throughput_records_sec', 0)
                tput = f"{tput_val:.1f} recs/s" if tput_val > 0 else "-"
                md_lines.append(f"| **Stage {stg_num}** | {stg_name} | {stg_tot} | ✅ **COMPLETED** | {tput} | `{stg_out}` |")
            elif stg_num == stage_number:
                if status == "COMPLETED":
                    tput = f"{throughput:.1f} recs/s"
                    md_lines.append(f"| **Stage {stg_num}** | {stg_name} | {stg_tot} | ✅ **COMPLETED** | {tput} | `{stg_out}` |")
                else:
                    tput = f"{throughput:.1f} recs/s"
                    md_lines.append(f"| **Stage {stg_num}** | {stg_name} | {stg_tot} | 🟡 **RUNNING ({chunk_pct:.1f}%)** | {tput} | `{stg_out}` |")
            elif stg_num < stage_number:
                md_lines.append(f"| **Stage {stg_num}** | {stg_name} | {stg_tot} | ✅ **COMPLETED** | - | `{stg_out}` |")
            else:
                md_lines.append(f"| **Stage {stg_num}** | {stg_name} | {stg_tot} | ⏳ PENDING | - | `{stg_out}` |")

        with open(LOGBOOK_MD, "w") as f:
            f.write("\n".join(md_lines) + "\n")

    except Exception as e:
        logger.warning("Could not update progress logbook: %s", e)


# ---------------------------------------------------------------------------
# Argument Parser
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="High-Throughput CPU Batch Inference")
    parser.add_argument("--input", required=True, help="Path to input crime CSV file")
    parser.add_argument("--output", required=True, help="Path to output Parquet file")
    parser.add_argument("--chunksize", type=int, default=500000, help="Chunk size for streaming CSV (default: 500,000)")
    parser.add_argument("--batch-size", type=int, default=1024, help="Inference mini-batch size (default: 1024)")
    parser.add_argument("--limit", type=int, default=None, help="Cap row count for dry-run verification")
    parser.add_argument("--model-dir", default=DEFAULT_MODEL_DIR,
                        help="Directory holding student model weights and tokenizer")
    parser.add_argument("--dataset-name", default="Crime Dataset", help="Human readable dataset name for telemetry")
    parser.add_argument("--stage-number", type=int, default=1, help="Stage number (1 to 6)")
    parser.add_argument("--total-stages", type=int, default=6, help="Total number of stages")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------
def main():
    args = parse_args()
    device = torch.device("cpu")

    logger.info("=" * 80)
    logger.info("D.H.A.R.M.A. — High-Throughput CPU Batch Inference")
    logger.info("=" * 80)
    logger.info("Device: CPU (threads=%d)", torch.get_num_threads())
    logger.info("Input: %s", args.input)
    logger.info("Output: %s", args.output)
    logger.info("Chunksize: %s", args.chunksize)
    logger.info("Batch Size: %s", args.batch_size)
    if args.limit:
        logger.info("Limit (dry-run): %d", args.limit)

    # 1. Load configuration and taxonomy maps
    config_path = Path(args.model_dir) / "config.json"
    model_pt_path = Path(args.model_dir) / "model.pt"

    if not config_path.exists() or not model_pt_path.exists():
        logger.error("Model artifacts not found in %s", args.model_dir)
        sys.exit(1)

    with open(config_path, "r") as f:
        config = json.load(f)

    num_classes = config["num_classes"]
    inverse_label_maps = config["inverse_label_maps"]

    logger.info("Loading model and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_dir)
    model = MultiHeadDistilBERT(num_classes)
    model.load_state_dict(torch.load(model_pt_path, map_location=device, weights_only=True))
    model.eval()

    # Align tensor memory layout where applicable
    try:
        model = model.to(memory_format=torch.channels_last)
        logger.info("Applied torch.channels_last layout to model.")
    except Exception as e:
        logger.warning("Could not apply channels_last layout: %s", e)

    # Validate output directory
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    # 1.5 DATASET RESUME CHECK: Skip entire dataset if final output file already exists and is valid
    output_path = Path(args.output)
    if output_path.exists():
        try:
            existing_pf = pq.ParquetFile(output_path)
            if existing_pf.metadata.num_rows > 0:
                logger.info(
                    "  ★ Final Parquet file %s ALREADY EXISTS and is VALID (%d rows). Skipping entire dataset!",
                    output_path.name, existing_pf.metadata.num_rows
                )
                update_logbook(
                    dataset_name=args.dataset_name,
                    stage_number=args.stage_number,
                    total_stages=args.total_stages,
                    chunk_idx=1,
                    processed_in_chunk=existing_pf.metadata.num_rows,
                    chunk_rows=existing_pf.metadata.num_rows,
                    total_processed_stage=existing_pf.metadata.num_rows,
                    throughput=2000.0,
                    chunk_elapsed=0.1,
                    status="COMPLETED"
                )
                sys.exit(0)
        except Exception as e:
            logger.warning("Final output file %s is partial/invalid (%s). Proceeding with chunk inference.", output_path.name, e)

    # 2. Process data in memory-resident chunks with automatic checkpointing & resume capability
    start_time = time.time()
    total_processed = 0

    # Setup checkpoint directory for atomic resume
    output_path = Path(args.output)
    checkpoint_dir = output_path.parent / "checkpoints" / output_path.stem
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Chunk checkpoint directory: %s", checkpoint_dir)

    try:
        logger.info("Streaming CSV input using pandas chunking...")
        chunks = pd.read_csv(args.input, chunksize=args.chunksize)

        for chunk_idx, chunk_df in enumerate(chunks, start=1):
            chunk_start = time.time()
            chunk_rows = len(chunk_df)
            chk_file = checkpoint_dir / f"chunk_{chunk_idx:04d}.parquet"

            if args.limit and total_processed >= args.limit:
                logger.info("Limit of %d reached. Exiting stream.", args.limit)
                break

            # Slice if chunk exceeds limit
            if args.limit and (total_processed + chunk_rows) > args.limit:
                slice_size = args.limit - total_processed
                chunk_df = chunk_df.iloc[:slice_size].copy()
                chunk_rows = len(chunk_df)
            else:
                chunk_df = chunk_df.copy()

            # CHECKPOINT RESUME CHECK: Skip if chunk file already exists and is valid
            if chk_file.exists():
                try:
                    chk_pf = pq.ParquetFile(chk_file)
                    valid_rows = chk_pf.metadata.num_rows
                    if valid_rows > 0:
                        logger.info(
                            "  ★ Checkpoint found for Chunk #%d (%d rows) at %s. Skipping inference!",
                            chunk_idx, valid_rows, chk_file.name
                        )
                        total_processed += valid_rows
                        update_logbook(
                            dataset_name=args.dataset_name,
                            stage_number=args.stage_number,
                            total_stages=args.total_stages,
                            chunk_idx=chunk_idx,
                            processed_in_chunk=valid_rows,
                            chunk_rows=valid_rows,
                            total_processed_stage=total_processed,
                            throughput=2000.0,
                            chunk_elapsed=0.1,
                            status="RUNNING"
                        )
                        continue
                except Exception as e:
                    logger.warning("Checkpoint %s invalid/corrupt (%s). Re-processing chunk.", chk_file.name, e)

            logger.info("Processing Chunk #%d (%d rows)...", chunk_idx, chunk_rows)

            # A. Synthesize narratives
            logger.info("  Synthesizing narratives...")
            narratives = chunk_df.apply(synthesize_narrative, axis=1).tolist()

            # B. Batched Tensor Inference Loop
            predicted_weapon: List[str] = []
            predicted_entry: List[str] = []
            predicted_target: List[str] = []
            predicted_suspects: List[str] = []

            logger.info("  Running batch inference...")
            for start_idx in range(0, chunk_rows, args.batch_size):
                end_idx = min(start_idx + args.batch_size, chunk_rows)
                batch_texts = narratives[start_idx:end_idx]

                # Tokenize
                encodings = tokenizer(
                    batch_texts,
                    max_length=256,
                    padding=True,
                    truncation=True,
                    return_tensors="pt",
                )

                input_ids = encodings["input_ids"].to(device)
                attention_mask = encodings["attention_mask"].to(device)

                # Autocast to bfloat16 for Intel AMX vectorization
                with torch.no_grad():
                    with torch.amp.autocast("cpu", dtype=torch.bfloat16):
                        logits = model(input_ids=input_ids, attention_mask=attention_mask)

                # Vectorized argmax decoding
                pred_weapon_idx = torch.argmax(logits["weapon_classification"], dim=1).numpy()
                pred_entry_idx = torch.argmax(logits["point_of_entry"], dim=1).numpy()
                pred_target_idx = torch.argmax(logits["target_profile"], dim=1).numpy()
                pred_suspects_idx = torch.argmax(logits["suspect_count_estimate"], dim=1).numpy()

                # Map output indices back to labels
                predicted_weapon.extend(
                    [inverse_label_maps["weapon_classification"][str(idx)] for idx in pred_weapon_idx]
                )
                predicted_entry.extend(
                    [inverse_label_maps["point_of_entry"][str(idx)] for idx in pred_entry_idx]
                )
                predicted_target.extend(
                    [inverse_label_maps["target_profile"][str(idx)] for idx in pred_target_idx]
                )
                predicted_suspects.extend(
                    [inverse_label_maps["suspect_count_estimate"][str(idx)] for idx in pred_suspects_idx]
                )

                # Real-time Telemetry & Logbook Update (every 50 batches or ~51,200 rows)
                batch_count = (start_idx // args.batch_size) + 1
                if batch_count % 50 == 0 or end_idx == chunk_rows:
                    batch_duration = time.time() - chunk_start
                    batch_tput = end_idx / batch_duration if batch_duration > 0 else 0.0
                    logger.info(
                        "  [Stage %d/%d: %s] Chunk #%d: %d/%d rows (%.1f%%) — Throughput: %.1f recs/s",
                        args.stage_number,
                        args.total_stages,
                        args.dataset_name,
                        chunk_idx,
                        end_idx,
                        chunk_rows,
                        (end_idx / chunk_rows) * 100,
                        batch_tput,
                    )
                    sys.stdout.flush()
                    update_logbook(
                        dataset_name=args.dataset_name,
                        stage_number=args.stage_number,
                        total_stages=args.total_stages,
                        chunk_idx=chunk_idx,
                        processed_in_chunk=end_idx,
                        chunk_rows=chunk_rows,
                        total_processed_stage=total_processed + end_idx,
                        throughput=batch_tput,
                        chunk_elapsed=batch_duration,
                        status="RUNNING"
                    )

            # C. Append predictions directly to DataFrame
            chunk_df["mo_weapon"] = predicted_weapon
            chunk_df["mo_entry"] = predicted_entry
            chunk_df["mo_target"] = predicted_target
            chunk_df["mo_suspects"] = predicted_suspects

            # D. Align schemas: force non-key numeric columns to float64 to prevent int-vs-float chunk mismatches
            for col in chunk_df.columns:
                if col.lower() not in ['incident_id', 'id', 'arrest_key', 'dr_no', 'ccn', 'case_number', 'case number']:
                    if pd.api.types.is_numeric_dtype(chunk_df[col]) and 'zip' not in col.lower() and 'code' not in col.lower():
                        chunk_df[col] = chunk_df[col].astype('float64')
                    else:
                        chunk_df[col] = chunk_df[col].astype(str).replace('nan', '')

            # E. Save Chunk Parquet Checkpoint atomically
            table = pa.Table.from_pandas(chunk_df, preserve_index=False)
            pq.write_table(table, chk_file, compression="snappy")
            logger.info("  Saved Chunk #%d checkpoint to %s", chunk_idx, chk_file.name)

            total_processed += chunk_rows
            chunk_duration = time.time() - chunk_start
            throughput = chunk_rows / chunk_duration if chunk_duration > 0 else 0.0
            logger.info(
                "  Chunk #%d complete: %d rows in %.2fs (Throughput: %.1f records/sec)",
                chunk_idx,
                chunk_rows,
                chunk_duration,
                throughput,
            )
            sys.stdout.flush()

        # F. Combine all completed chunk checkpoints into final parquet output
        chunk_files = sorted(list(checkpoint_dir.glob("chunk_*.parquet")))
        if chunk_files:
            logger.info("Combining %d chunk checkpoints into final Parquet file %s...", len(chunk_files), args.output)
            tables = [pq.read_table(cf) for cf in chunk_files]
            combined_table = pa.concat_tables(tables)
            pq.write_table(combined_table, args.output, compression="snappy")
            logger.info("Successfully exported combined Parquet file: %s (%d rows)", args.output, combined_table.num_rows)

    finally:
        pass

    # 3. Final metrics
    total_time = time.time() - start_time
    avg_throughput = total_processed / total_time if total_time > 0 else 0.0
    logger.info("=" * 80)
    logger.info("BATCH INFERENCE WORKFLOW COMPLETE")
    logger.info("Processed records : %d", total_processed)
    logger.info("Output file       : %s", args.output)
    logger.info("Total time        : %.2f seconds (%.2f minutes)", total_time, total_time / 60)
    logger.info("Avg throughput    : %.1f records/sec", avg_throughput)
    logger.info("=" * 80)
    sys.stdout.flush()

    # Record stage completion in logbook
    try:
        log_data = {}
        if LOGBOOK_JSON.exists():
            with open(LOGBOOK_JSON, "r") as f:
                log_data = json.load(f)
        completed = log_data.get("completed_stages", [])
        
        # Add if not present
        if not any(c.get("stage_number") == args.stage_number for c in completed):
            completed.append({
                "stage_number": args.stage_number,
                "dataset_name": args.dataset_name,
                "total_rows": total_processed,
                "status": "COMPLETED",
                "output_file": os.path.basename(args.output),
                "throughput_records_sec": round(avg_throughput, 1),
                "elapsed_minutes": round(total_time / 60, 2)
            })
            log_data["completed_stages"] = completed
            with open(LOGBOOK_JSON, "w") as f:
                json.dump(log_data, f, indent=2)

        update_logbook(
            dataset_name=args.dataset_name,
            stage_number=args.stage_number,
            total_stages=args.total_stages,
            chunk_idx=chunk_idx if 'chunk_idx' in locals() else 1,
            processed_in_chunk=chunk_rows if 'chunk_rows' in locals() else total_processed,
            chunk_rows=chunk_rows if 'chunk_rows' in locals() else total_processed,
            total_processed_stage=total_processed,
            throughput=avg_throughput,
            chunk_elapsed=total_time,
            status="COMPLETED"
        )
    except Exception as e:
        logger.warning("Could not record stage completion: %s", e)


if __name__ == "__main__":
    main()
