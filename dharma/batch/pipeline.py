"""
pipeline.py — Project D.H.A.R.M.A. Master Batch Ingestion Pipeline

Connects the entire pipeline:
1. Ingests crime records from a geocoded CSV.
2. Synthesizes/identifies narrative texts.
3. Performs local PII scrubbing (anonymizer).
4. Dispatches anonymized narratives to Groq LPU (MO extractor).
5. Bundles the metadata and extracted MO schema into a unified JSON array.

Usage:
  python3 pipeline.py --input data/chicago_crimes.csv --output processed/chicago_crimes_anonymized_mo.json --limit 10
"""

import os
import sys
import json
import time
import argparse
import random
import logging
from pathlib import Path
import pandas as pd

# Add current folder to sys.path to locate sibling modules
sys.path.append(str(Path(__file__).resolve().parent))

# Load dotenv if available (for API keys)
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass

from local_anonymizer import LocalAnonymizer
from groq_mo_extractor import GroqMOExtractor

from dharma.config import LOGS_DIR, PROCESSED_DIR

# Logging setup
pipeline_log_path = LOGS_DIR / "pipeline.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s — %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(pipeline_log_path), mode='w')
    ]
)
logger = logging.getLogger("dharma.pipeline")

# PII lists for mock narrative synthesis if the input lacks a description column
FIRST_NAMES = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
STREETS = ["Elm", "Oak", "Pine", "Maple", "Cedar", "Washington", "Randolph", "Clark", "State", "Michigan"]
SUFFIXES = ["St", "Ave", "Blvd", "Rd", "Dr", "Ln", "Ct", "Way"]

def synthesize_narrative(row) -> str:
    """Synthesizes a PII-heavy narrative based on category/metadata if no text is present."""
    o_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    s_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    v_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    badge = random.randint(1000, 9999)
    address = f"{random.randint(100, 9999)} {random.choice(STREETS)} {random.choice(SUFFIXES)}"
    phone = f"({random.randint(200, 999)})-555-{random.randint(1000, 9999)}"
    
    cat = str(row.get('category', 'crime')).upper()
    ts = str(row.get('timestamp', 'date'))
    
    if any(k in cat for k in ['THEFT', 'BURGLARY', 'ROBBERY', 'LARCENY']):
        return f"On {ts}, Officer {o_name} (Badge #{badge}) responded to a report of {cat.lower()} at {address}. The store manager, {v_name}, stated that the suspect, {s_name}, walked in, stole items, and fled on foot. Phone: {phone}."
    elif any(k in cat for k in ['ASSAULT', 'BATTERY', 'FIGHT', 'VANDALISM']):
        weapon = random.choice(["metal pipe", "baseball bat", "knife", "fists"])
        return f"On {ts}, Officer {o_name} (Badge #{badge}) responded to a physical assault at {address}. The victim, {v_name}, was struck with a {weapon} by the suspect, {s_name}, who then fled the scene. Phone: {phone}."
    else:
        return f"On {ts}, Officer {o_name} (Badge #{badge}) responded to a disturbance at {address} involving suspect {s_name} and victim {v_name}. Phone: {phone}."

def parse_args():
    parser = argparse.ArgumentParser(description="D.H.A.R.M.A. Master Batch Ingestion Pipeline")
    parser.add_argument("--input", required=True, help="Path to input crimes CSV file")
    parser.add_argument("--output", required=True, help="Path to save output anonymized M.O. JSON file")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of rows to process")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay in seconds between API calls")
    return parser.parse_args()

def main():
    args = parse_args()
    
    start_time = time.time()
    logger.info(f"==================================================")
    logger.info(f"STARTING D.H.A.R.M.A. MASTER PIPELINE")
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")
    logger.info(f"Limit: {args.limit}")
    logger.info(f"Delay: {args.delay} seconds")
    logger.info(f"==================================================")
    
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
        
    df = pd.read_csv(args.input)
    total_records = len(df)
    logger.info(f"Loaded {total_records} records from CSV.")
    
    # Apply limit if set
    if args.limit is not None:
        df = df.head(args.limit)
        logger.info(f"Limited processing to first {len(df)} records.")
        
    # Map columns dynamically
    col_map = {}
    for canonical, alternates in {
        'incident_id': ['incident_id', 'id', 'dr_no', 'ccn', 'case_number', 'case number'],
        'timestamp': ['timestamp', 'date', 'date_occ', 'date occ', 'report_dat', 'incident_datetime'],
        'latitude': ['latitude', 'lat'],
        'longitude': ['longitude', 'lon', 'lng'],
        'category': ['category', 'primary_type', 'primary type', 'offense', 'crm_cd_desc'],
        'narrative': ['narrative', 'description', 'incident_description', 'incident description']
    }.items():
        matched = None
        for col in df.columns:
            if col.lower() in alternates:
                matched = col
                break
        col_map[canonical] = matched

    logger.info(f"Column mapping resolved: {col_map}")
    
    # Initialize anonymizer and extractor
    anonymizer = LocalAnonymizer()
    extractor = GroqMOExtractor()
    
    output_records = []
    success_count = 0
    
    for idx, (_, row) in enumerate(df.iterrows(), start=1):
        # Extract row metadata
        incident_id = row[col_map['incident_id']] if col_map['incident_id'] else idx
        timestamp = row[col_map['timestamp']] if col_map['timestamp'] else None
        latitude = row[col_map['latitude']] if col_map['latitude'] else None
        longitude = row[col_map['longitude']] if col_map['longitude'] else None
        category = row[col_map['category']] if col_map['category'] else None
        
        # Get or synthesize narrative
        raw_narrative = None
        if col_map['narrative'] and pd.notna(row[col_map['narrative']]):
            raw_narrative = str(row[col_map['narrative']]).strip()
            
        if not raw_narrative:
            raw_narrative = synthesize_narrative(row)
            
        logger.info(f"[{idx}/{len(df)}] Processing Incident ID: {incident_id}")
        
        # 1. Scrub PII
        anon_res = anonymizer.anonymize(raw_narrative)
        
        # 2. Extract MO
        mo_res = extractor.extract_mo(anon_res["anonymized_text"])
        
        if not mo_res.get("error_flag", True):
            success_count += 1
            
        # 3. Merge output
        record = {
            "incident_id": int(incident_id) if isinstance(incident_id, (int, float)) else str(incident_id),
            "timestamp": str(timestamp) if timestamp else "",
            "latitude": float(latitude) if pd.notna(latitude) else None,
            "longitude": float(longitude) if pd.notna(longitude) else None,
            "category": str(category) if category else "",
            "anonymized_narrative": anon_res["anonymized_text"],
            "redactions_count": anon_res["redactions_count"],
            "entity_map": anon_res["entity_map"],
            "mo_payload": mo_res
        }
        
        output_records.append(record)
        
        # Rate limit safety delay
        if idx < len(df) and args.delay > 0:
            time.sleep(args.delay)
            
    # Save unified JSON output
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output_records, f, indent=2)
        
    duration = time.time() - start_time
    logger.info(f"==================================================")
    logger.info(f"PIPELINE COMPLETED SUCCESSFULLY")
    logger.info(f"Processed: {len(df)} records")
    logger.info(f"Successful extractions: {success_count}/{len(df)}")
    logger.info(f"Output saved to: {args.output}")
    logger.info(f"Total time: {duration:.2f} seconds")
    logger.info(f"==================================================")

if __name__ == "__main__":
    main()
