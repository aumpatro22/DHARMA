"""
generate_gold_seed.py — Generate Gold Standard Seed Dataset for DistilBERT Training

Uses the D.H.A.R.M.A. pipeline (LocalAnonymizer + GroqMOExtractor) to process
crime incident CSVs and generate a consolidated Gold Seed JSON file containing
anonymized narratives with Gold Standard M.O. labels.

Usage:
    python3 generate_gold_seed.py --limit 2000
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

sys.path.append(str(Path(__file__).resolve().parent))

try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dharma.nlp.anonymizer import LocalAnonymizer
    from dharma.nlp.extractor import GroqMOExtractor
except ImportError:
    from local_anonymizer import LocalAnonymizer
    from groq_mo_extractor import GroqMOExtractor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("dharma.gold_seed_gen")

# PII pools for narrative synthesis
FIRST_NAMES = ["James", "John", "Robert", "Michael", "William", "David", "Richard",
               "Joseph", "Thomas", "Charles", "Christopher", "Daniel", "Matthew",
               "Anthony", "Mark", "Steven", "Paul", "Andrew", "Joshua", "Kenneth"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
              "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson",
              "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee"]
STREETS = ["Elm", "Oak", "Pine", "Maple", "Cedar", "Washington", "Randolph",
           "Clark", "State", "Michigan", "Broadway", "Market", "Mission", "Geary"]
SUFFIXES = ["St", "Ave", "Blvd", "Rd", "Dr", "Ln", "Ct", "Way"]
STORES = ["Walmart", "Target", "Home Depot", "Best Buy", "Walgreens", "CVS", "Safeway"]

# Diverse narrative templates covering all taxonomy categories
TEMPLATES = [
    # FIREARM + INDIVIDUAL + SOLO
    "On {date} at {time}, the victim {v_first} {v_last} was walking near {address} when the suspect {s_first} {s_last} approached and pulled a handgun. The suspect demanded cash and the victim's phone. {s_first} {s_last} then fled southbound on foot. Officer {o_first} {o_last} (Badge #{badge}) responded. Phone: {phone}.",
    # FIREARM + INDIVIDUAL + PAIR
    "Two suspects approached the victim {v_first} {v_last} near the bus stop at {address}. One suspect, {s_first} {s_last}, pulled a black semi-automatic handgun from his waistband and demanded the victim's wallet and smartphone. Both suspects fled on foot. Officer {o_first} {o_last} (Badge #{badge}) took the report. Phone: {phone}.",
    # BLADED + INDIVIDUAL + SOLO
    "The victim {v_first} {v_last} reported being threatened with a knife by the suspect {s_first} {s_last} at {address}. The suspect slashed the victim's arm and grabbed their bag before running away. Officer {o_first} {o_last} (Badge #{badge}) responded. Phone: {phone}.",
    # BLUNT_FORCE + INDIVIDUAL + SOLO
    "Officer {o_first} {o_last} (Badge #{badge}) was dispatched to {address} regarding a physical fight. The victim {v_first} {v_last} was struck multiple times with a metal pipe by the suspect {s_first} {s_last}. The suspect fled on foot eastbound. Phone: {phone}.",
    # MELEE_OTHER + INDIVIDUAL + GROUP
    "Three suspects attacked {v_first} {v_last} near {address}. The main aggressor, {s_first} {s_last}, punched and kicked the victim repeatedly while two accomplices held the victim down. All suspects fled. Officer {o_first} {o_last} (Badge #{badge}) responded. Phone: {phone}.",
    # NONE + COMMERCIAL + SOLO (shoplifting)
    "On {date} at {time}, Officer {o_first} {o_last} (Badge #{badge}) responded to a shoplifting report at {store} located at {address}. The suspect {s_first} {s_last} concealed merchandise and exited without paying. The suspect was unarmed. The store manager {v_first} {v_last} detained the suspect. Phone: {phone}.",
    # BLUNT_FORCE + COMMERCIAL + UNKNOWN suspects (burglary, rear door)
    "Store manager {v_first} {v_last} discovered the rear glass door of {store} at {address} was shattered upon arriving at work on {date}. Cash register was pried open and approximately $400 in cash was removed during nighttime hours. Officer {o_first} {o_last} (Badge #{badge}) investigated. Phone: {phone}.",
    # NONE + RESIDENTIAL + SOLO (burglary, window)
    "On {date}, the homeowner {v_first} {v_last} at {address} returned home to find a side window smashed and jewelry missing from the bedroom. No weapon was observed. Neighbor saw one person fleeing. Officer {o_first} {o_last} (Badge #{badge}) responded. Phone: {phone}.",
    # NONE + VEHICLE + SOLO
    "Victim {v_first} {v_last} reported their car stolen from the parking lot of {store} at {address} on {date}. The suspect {s_first} {s_last} was caught on CCTV entering the unlocked vehicle and driving away. Officer {o_first} {o_last} (Badge #{badge}) is investigating. Phone: {phone}.",
    # FIREARM + COMMERCIAL + SOLO (bank robbery)
    "On {date} at {time}, a robbery occurred at the Chase Bank on {address}. The suspect {s_first} {s_last} presented a note demanding cash and displayed a concealed handgun. The teller {v_first} {v_last} complied and the suspect fled with $5,000 through the back exit. Officer {o_first} {o_last} (Badge #{badge}) responded. Phone: {phone}.",
    # NONE + RESIDENTIAL + PAIR (burglary, front door)
    "On {date}, {v_first} {v_last} returned to their apartment at {address} to find the front door had been kicked in. Two suspects were seen leaving the building with electronics. Officer {o_first} {o_last} (Badge #{badge}) took the report. Phone: {phone}.",
    # BLADED + COMMERCIAL + SOLO (armed robbery)
    "The suspect {s_first} {s_last} entered {store} at {address} on {date} and threatened the cashier {v_first} {v_last} with a box cutter. The suspect demanded cash from the register and fled. Officer {o_first} {o_last} (Badge #{badge}) responded. Phone: {phone}.",
    # NONE + VEHICLE + PAIR (theft from vehicle)
    "On {date} at {time}, two suspects were seen smashing the passenger window of a vehicle parked at {address}. The suspects stole a laptop bag and fled. The vehicle owner {v_first} {v_last} filed a report. Officer {o_first} {o_last} (Badge #{badge}) responded. Phone: {phone}.",
    # FIREARM + INDIVIDUAL + GROUP (gang assault)
    "Three armed suspects confronted {v_first} {v_last} at {address}. The primary suspect {s_first} {s_last} fired a shot into the air and demanded valuables. All three fled in a dark sedan. Officer {o_first} {o_last} (Badge #{badge}) responded. Phone: {phone}.",
    # NONE + INFRASTRUCTURE + SOLO (vandalism)
    "On {date}, the suspect {s_first} {s_last} was observed spray-painting graffiti on the exterior wall of the public transit station at {address}. The suspect caused approximately $2,000 in damage. Officer {o_first} {o_last} (Badge #{badge}) apprehended the suspect. Phone: {phone}.",
    # NONE + RESIDENTIAL + SOLO (garage entry)
    "On {date}, {v_first} {v_last} discovered their garage at {address} had been broken into overnight. Power tools and a bicycle were stolen. The garage door lock had been pried open. No witnesses. Officer {o_first} {o_last} (Badge #{badge}) responded. Phone: {phone}.",
]


def generate_records(count: int) -> list:
    """Generate diverse PII-heavy narrative records."""
    random.seed(42)
    records = []
    for i in range(count):
        template = TEMPLATES[i % len(TEMPLATES)]
        o_first, o_last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
        s_first, s_last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
        v_first, v_last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
        badge = str(random.randint(1000, 9999))
        address = f"{random.randint(100, 9999)} {random.choice(STREETS)} {random.choice(SUFFIXES)}"
        store = random.choice(STORES)
        phone = f"({random.randint(200, 999)})-555-{random.randint(1000, 9999)}"
        date = f"2025-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        time_str = f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}"

        narrative = template.format(
            date=date, time=time_str,
            o_first=o_first, o_last=o_last,
            s_first=s_first, s_last=s_last,
            v_first=v_first, v_last=v_last,
            badge=badge, address=address,
            store=store, phone=phone,
        )
        records.append({
            "id": i + 1,
            "raw_narrative": narrative,
        })
    return records


def main():
    parser = argparse.ArgumentParser(description="Generate Gold Seed Dataset")
    parser.add_argument("--limit", type=int, default=100,
                        help="Number of seed records to generate")
    default_output = str(PROJECT_ROOT / "data" / "gold_seed_2000.json")
    parser.add_argument("--output", type=str,
                        default=default_output,
                        help="Output path for Gold Seed JSON")
    parser.add_argument("--delay", type=float, default=0.3,
                        help="Delay between API calls in seconds")
    args = parser.parse_args()

    logger.info("Generating %d raw narrative records...", args.limit)
    records = generate_records(args.limit)

    anonymizer = LocalAnonymizer()
    extractor = GroqMOExtractor()

    gold_seeds = []
    for idx, rec in enumerate(records, start=1):
        logger.info("[%d/%d] Processing record ID: %d", idx, args.limit, rec["id"])

        # Anonymize
        anon = anonymizer.anonymize(rec["raw_narrative"])

        # Extract Gold Standard M.O.
        mo = extractor.extract_mo(anon["anonymized_text"])

        gold_seeds.append({
            "id": rec["id"],
            "anonymized_narrative": anon["anonymized_text"],
            "redactions_count": anon["redactions_count"],
            "mo_payload": mo,
        })

        if idx < args.limit and args.delay > 0:
            time.sleep(args.delay)

    # Save
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(gold_seeds, f, indent=2)

    success = sum(1 for s in gold_seeds if not s["mo_payload"].get("error_flag", True))
    logger.info("Gold Seed generation complete: %d/%d successful. Saved to %s",
                success, args.limit, args.output)


if __name__ == "__main__":
    main()
