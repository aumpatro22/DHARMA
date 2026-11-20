#!/usr/bin/env python3
"""
evaluate_test_set.py — Standalone Model Evaluation & Test Harness

Evaluates the trained MultiHeadDistilBERT student model on an independent,
unseen ground-truth test dataset (e.g. data/gold_test_1000.json).

Computes:
  - Exact overall accuracy across all 4 M.O. heads
  - Detailed Precision, Recall, and F1-Score per class
  - Support counts and error summaries

Usage:
  python3 evaluate_test_set.py --test-file data/gold_test_1000.json
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from transformers import DistilBertTokenizer, DistilBertModel
from sklearn.metrics import classification_report, accuracy_score

# Configure CPU threading
num_cores = min(os.cpu_count() or 4, 24)
os.environ["OMP_NUM_THREADS"] = str(num_cores)
os.environ["MKL_NUM_THREADS"] = str(num_cores)
os.environ["TOKENIZERS_PARALLELISM"] = "false"
torch.set_num_threads(num_cores)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("dharma.evaluator")

# ---------------------------------------------------------------------------
# Model Architecture
# ---------------------------------------------------------------------------
class MultiHeadDistilBERT(nn.Module):
    def __init__(self, num_classes_per_head: Dict[str, int], dropout: float = 0.3):
        super().__init__()
        self.distilbert = DistilBertModel.from_pretrained("distilbert-base-uncased")
        hidden_size = self.distilbert.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.heads = nn.ModuleDict()
        for head_name, n_classes in num_classes_per_head.items():
            self.heads[head_name] = nn.Sequential(
                nn.Linear(hidden_size, 256),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(256, n_classes),
            )

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> Dict[str, torch.Tensor]:
        outputs = self.distilbert(input_ids=input_ids, attention_mask=attention_mask)
        cls_output = outputs.last_hidden_state[:, 0, :]
        cls_output = self.dropout(cls_output)
        return {head_name: head(cls_output) for head_name, head in self.heads.items()}


class EvalDataset(Dataset):
    def __init__(self, texts: List[str], labels: Dict[str, List[int]], tokenizer, max_length: int = 256):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx: int):
        encoding = self.tokenizer(
            self.texts[idx],
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        item = {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
        }
        for head_name, label_list in self.labels.items():
            item[f"label_{head_name}"] = torch.tensor(label_list[idx], dtype=torch.long)
        return item


def load_test_records(test_file: str, label_maps: Dict[str, Dict[str, int]]) -> Tuple[List[str], Dict[str, List[int]]]:
    with open(test_file, "r") as f:
        records = json.load(f)

    texts = []
    labels = {head: [] for head in label_maps}

    for record in records:
        narrative = record.get("anonymized_narrative", "")
        payload = record.get("mo_payload", {})
        mo = payload.get("modus_operandi", payload)

        if not narrative.strip():
            continue

        texts.append(narrative)
        for head, lmap in label_maps.items():
            val = str(mo.get(head, "UNKNOWN")).upper().strip()
            labels[head].append(lmap.get(val, lmap.get("UNKNOWN", 0)))

    return texts, labels


def print_banner(title: str):
    print("\n" + "=" * 78)
    print(f"  {title}")
    print("=" * 78)


def main():
    project_root = Path(__file__).resolve().parent.parent
    default_test = str(project_root / "data" / "gold_test_1000.json")
    default_model = str(project_root / "models" / "distilbert_mo_student")

    parser = argparse.ArgumentParser(description="Evaluate Student Model on Test Dataset")
    parser.add_argument("--test-file", type=str, default=default_test,
                        help="Path to the test JSON file")
    parser.add_argument("--model-dir", type=str, default=default_model,
                        help="Directory containing model.pt and config.json")
    parser.add_argument("--batch-size", type=int, default=64,
                        help="Inference batch size")
    args = parser.parse_args()

    test_path = Path(args.test_file).resolve()
    model_dir = Path(args.model_dir).resolve()

    if not test_path.exists():
        print(f"Error: Test file not found at {test_path}")
        sys.exit(1)

    config_path = model_dir / "config.json"
    weights_path = model_dir / "model.pt"

    if not config_path.exists() or not weights_path.exists():
        print(f"Error: Model files not found in {model_dir}")
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    label_maps = config["label_maps"]
    inv_label_maps = config["inverse_label_maps"]
    num_classes = config["num_classes"]

    print_banner(f"PROJECT D.H.A.R.M.A. — MODEL EVALUATION ON UNSEEN TEST DATA")
    print(f"Test File : {test_path} ({test_path.stat().st_size / (1024*1024):.2f} MB)")
    print(f"Model Dir : {model_dir}")
    print(f"Hardware  : CPU ({num_cores} cores active)")

    # 1. Load Data
    print("\nLoading test dataset...")
    texts, labels = load_test_records(str(test_path), label_maps)
    print(f"Total Test Samples: {len(texts)}")

    # 2. Load Model & Tokenizer
    print("Loading model weights and tokenizer...")
    device = torch.device("cpu")
    tokenizer = DistilBertTokenizer.from_pretrained(str(model_dir))
    model = MultiHeadDistilBERT(num_classes).to(device)
    model.load_state_dict(torch.load(weights_path, map_location=device, weights_only=True))
    model.eval()

    # 3. Create DataLoader
    test_dataset = EvalDataset(texts, labels, tokenizer)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False, num_workers=4)

    # 4. Run Evaluation
    print(f"Running inference across {len(test_loader)} batches (batch_size={args.batch_size})...")
    start_time = time.time()

    all_preds = {head: [] for head in label_maps}
    all_targets = {head: [] for head in label_maps}

    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            logits_dict = model(input_ids, attention_mask)

            for head in label_maps:
                preds = torch.argmax(logits_dict[head], dim=1).cpu().numpy()
                targets = batch[f"label_{head}"].numpy()
                all_preds[head].extend(preds)
                all_targets[head].extend(targets)

    elapsed_time = time.time() - start_time
    throughput = len(texts) / elapsed_time

    # 5. Compute Metrics
    accuracies = {}
    print_banner("OFFICIAL TEST SET ACCURACY & PERFORMANCE METRICS")
    print(f"Evaluated {len(texts)} unseen samples in {elapsed_time:.2f}s ({throughput:.1f} records/sec)\n")

    print(f"{'Classification Head':<28} | {'Classes':>7} | {'Test Accuracy':>15} | {'Status'}")
    print("-" * 75)
    for head in label_maps:
        acc = accuracy_score(all_targets[head], all_preds[head])
        accuracies[head] = acc
        status = "PASSED (>= 90%)" if acc >= 0.90 else "ACCEPTABLE"
        print(f"{head:<28} | {num_classes[head]:>7} | {acc * 100:>14.2f}% | {status}")

    overall_acc = sum(accuracies.values()) / len(accuracies)
    print("-" * 75)
    print(f"{'OVERALL AVERAGE ACCURACY':<28} | {'-':>7} | {overall_acc * 100:>14.2f}% | {'OUTSTANDING' if overall_acc >= 0.90 else 'GOOD'}")

    # 6. Detailed Class Reports
    for head in label_maps:
        print_banner(f"DETAILED REPORT: {head.upper()} (Accuracy: {accuracies[head]*100:.2f}%)")
        target_names = [inv_label_maps[head][str(i)] for i in range(num_classes[head])]
        report = classification_report(
            all_targets[head],
            all_preds[head],
            labels=list(range(num_classes[head])),
            target_names=target_names,
            zero_division=0,
            digits=3,
        )
        print(report)

    print("=" * 78)
    print("TEST EVALUATION COMPLETED SUCCESSFULLY")
    print("=" * 78 + "\n")


if __name__ == "__main__":
    main()
