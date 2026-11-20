"""
generate_gold_seed_local.py — Generate Rich Gold Standard Seed Dataset Locally

Fully Decoupled Target Profiles & Entry Points with Expanded Forensic Vocabulary:
  - Commercial (stores, banks, businesses, jewelry shops, pharmacies):
      Enters through WINDOW (front display, plate glass, side), ROOF_VENT (roof hatch, skylight, ventilation shaft),
      FRONT_DOOR, REAR_DOOR, or GARAGE (roll-up bay door).
  - Residential (homes, apartments, single-family houses, condos):
      Enters through FRONT_DOOR, REAR_DOOR, WINDOW (bedroom, sliding glass balcony),
      GARAGE (attached garage, side garage door), or ROOF_VENT (skylight, roof hatch).
  - Vehicles: Enters through WINDOW or DOOR.
  - Individuals / Open Infrastructure: NOT_APPLICABLE.

Expanded Vocabulary Matrices:
  - BLUNT_FORCE: Crowbar, hammer, baseball bat, tire iron, metal pipe, brick, wooden 2x4, wrench, baton, sledgehammer, club.
  - BLADED: Knife, switchblade, box cutter, machete, dagger, razor, hunting knife, pocket knife, kitchen knife.
  - FIREARM: Handgun, pistol, revolver, shotgun, rifle, semi-automatic, firearm, concealed pistol.
  - MELEE_OTHER: Punched, kicked, choked, tackled, struck with fists, beaten with bare hands, shoved.
  - NONE: Unarmed, no weapon observed, hands in pockets, without weapons, empty-handed.

Sentence Length Mix:
  - Includes both concise operational summaries and full officer CAD narratives.

Usage:
    python3 generate_gold_seed_local.py --count 3500
"""

import json
import logging
import os
import random
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections import Counter

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
except ImportError:
    from local_anonymizer import LocalAnonymizer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("dharma.gold_seed_local")

# ---------------------------------------------------------------------------
# Comprehensive Vocabulary Matrices
# ---------------------------------------------------------------------------
WEAPON_VOCABULARY = {
    "BLUNT_FORCE": [
        "crowbar", "hammer", "baseball bat", "tire iron", "metal pipe",
        "brick", "wooden 2x4", "wrench", "baton", "lead pipe",
        "heavy metal rod", "sledgehammer", "club", "brass knuckles"
    ],
    "BLADED": [
        "knife", "switchblade", "box cutter", "machete", "dagger",
        "razor", "hunting knife", "pocket knife", "kitchen knife", "folding blade"
    ],
    "FIREARM": [
        "handgun", "pistol", "revolver", "shotgun", "rifle",
        "semi-automatic", "firearm", "black handgun", "concealed pistol", "assault rifle"
    ],
    "MELEE_OTHER": [
        "punched", "kicked", "choked", "tackled", "struck with fists",
        "beaten with bare hands", "shoved violently", "grabbed by throat and slammed"
    ],
    "NONE": [
        "unarmed", "no weapon observed", "hands in pockets", "without weapons",
        "no weapon displayed", "completely unarmed", "empty-handed"
    ],
}

ENTRY_VOCABULARY = {
    "WINDOW": [
        "front window", "front display window", "side window", "display window", "rear window",
        "bedroom window", "plate glass window", "sliding glass balcony window", "basement window"
    ],
    "FRONT_DOOR": [
        "front door", "main entrance", "front glass door", "entryway door", "front sliding entrance"
    ],
    "REAR_DOOR": [
        "rear door", "back door", "rear exit door", "back entrance",
        "delivery door", "kitchen back door", "fire exit door", "service door"
    ],
    "GARAGE": [
        "garage door", "roll-up garage door", "attached garage entrance",
        "side garage door", "roll-up security bay door", "commercial loading bay"
    ],
    "ROOF_VENT": [
        "roof hatch", "rooftop ventilation shaft", "air duct on the roof",
        "skylight", "attic skylight", "ceiling ventilation duct"
    ],
    "NOT_APPLICABLE": [
        "open street", "sidewalk", "parking lot", "public thoroughfare", "alleyway", "open plaza"
    ],
}

TARGET_VOCABULARY = {
    "COMMERCIAL": [
        "jewelry store", "convenience store", "retail outlet", "electronics store",
        "bank branch", "pharmacy", "supermarket", "gas station", "department store",
        "liquor store", "commercial warehouse", "restaurant", "hardware store", "pawn shop"
    ],
    "RESIDENTIAL": [
        "single-family residence", "apartment unit", "suburban home", "condominium",
        "duplex", "two-story house", "townhouse", "private residence", "residential property"
    ],
    "INDIVIDUAL": [
        "pedestrian", "commuter", "bystander", "victim", "store customer", "transit rider", "shopper"
    ],
    "VEHICLE": [
        "parked sedan", "delivery van", "SUV", "pickup truck", "automobile", "rental car"
    ],
    "INFRASTRUCTURE": [
        "transit station", "bus shelter", "electrical sub-station", "municipal facility",
        "public park structure", "city maintenance depot"
    ],
}

SUSPECT_VOCABULARY = {
    "SOLO": {
        "phrase": ["solo suspect", "lone suspect", "single perpetrator", "lone individual", "one suspect", "solo individual"],
        "adverb": "fled solo",
        "count_label": "SOLO",
    },
    "PAIR": {
        "phrase": ["two suspects", "a pair of individuals", "two masked persons", "two accomplices", "a duo of suspects"],
        "adverb": "both fled",
        "count_label": "PAIR",
    },
    "GROUP": {
        "phrase": ["three suspects", "four individuals", "a group of perpetrators", "multiple assailants", "gang of four"],
        "adverb": "all suspects fled",
        "count_label": "GROUP",
    },
    "UNKNOWN": {
        "phrase": ["unknown number of suspects", "unidentified perpetrator", "unseen burglars", "unidentified individual"],
        "adverb": "the perpetrator fled",
        "count_label": "UNKNOWN",
    },
}

FIRST_NAMES = [
    "James", "John", "Robert", "Michael", "William", "David", "Richard",
    "Joseph", "Thomas", "Charles", "Christopher", "Daniel", "Matthew",
    "Anthony", "Mark", "Steven", "Paul", "Andrew", "Joshua", "Kenneth",
    "Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Elizabeth",
    "Susan", "Jessica", "Sarah", "Karen", "Nancy", "Lisa", "Betty",
    "Margaret", "Sandra", "Ashley", "Dorothy", "Kimberly", "Emily", "Donna",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson",
    "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee",
    "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis",
    "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott",
]
STREETS = [
    "Elm", "Oak", "Pine", "Maple", "Cedar", "Washington", "Randolph",
    "Clark", "State", "Michigan", "Broadway", "Market", "Mission", "Geary",
    "Main", "First", "Second", "Third", "Park", "Lake", "River", "Hill",
    "Spring", "Walnut", "Cherry", "Birch", "Willow", "Ash", "Poplar",
]
SUFFIXES = ["St", "Ave", "Blvd", "Rd", "Dr", "Ln", "Ct", "Way"]


def generate_decoupled_record(rng: random.Random) -> Tuple[str, Dict[str, str], List[str]]:
    """
    Synthesizes fully decoupled records where:
    - Target profiles have access to ALL plausible entry points (including commercial windows/roofs).
    - Weapons are explicitly and unambiguously bound to their forensic classes.
    - Narrative phrasing mixes concise summaries with detailed dispatch logs.
    """
    # Balanced Target selection
    target_class = rng.choice(["COMMERCIAL", "RESIDENTIAL", "INDIVIDUAL", "VEHICLE", "INFRASTRUCTURE"])
    target_name = rng.choice(TARGET_VOCABULARY[target_class])

    # Balanced Suspect selection
    suspect_class = rng.choice(["SOLO", "PAIR", "GROUP", "UNKNOWN"])
    suspect_info = SUSPECT_VOCABULARY[suspect_class]
    suspect_phrase = rng.choice(suspect_info["phrase"])
    fled_phrase = suspect_info["adverb"]

    # Decouple Entry based on Target
    if target_class == "COMMERCIAL":
        # Commercial can enter through: WINDOW (smash-and-grab), ROOF_VENT (roof hatch/air duct),
        # FRONT_DOOR, REAR_DOOR, or GARAGE (roll-up bay door)
        entry_class = rng.choice(["WINDOW", "ROOF_VENT", "FRONT_DOOR", "REAR_DOOR", "GARAGE"])
    elif target_class == "RESIDENTIAL":
        # Residential can enter through: WINDOW, FRONT_DOOR, REAR_DOOR, GARAGE, ROOF_VENT
        entry_class = rng.choice(["WINDOW", "FRONT_DOOR", "REAR_DOOR", "GARAGE", "ROOF_VENT"])
    elif target_class == "VEHICLE":
        entry_class = rng.choice(["WINDOW", "FRONT_DOOR", "REAR_DOOR"])
    else: # INDIVIDUAL or INFRASTRUCTURE
        entry_class = rng.choice(["NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "FRONT_DOOR"])

    entry_name = rng.choice(ENTRY_VOCABULARY[entry_class])

    # Select Weapon
    if target_class in ["COMMERCIAL", "RESIDENTIAL", "VEHICLE"]:
        # Burglary, robbery, or theft: can use BLUNT_FORCE (crowbar, hammer), BLADED, FIREARM, or NONE
        weapon_class = rng.choice(["BLUNT_FORCE", "FIREARM", "BLADED", "NONE", "BLUNT_FORCE"])
    elif target_class == "INDIVIDUAL":
        weapon_class = rng.choice(["FIREARM", "BLADED", "BLUNT_FORCE", "MELEE_OTHER", "NONE"])
    else: # INFRASTRUCTURE
        weapon_class = rng.choice(["BLUNT_FORCE", "NONE"])

    # Metadata tokens for CAD headers
    o_first, o_last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
    s_first, s_last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
    v_first, v_last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
    badge = str(rng.randint(1000, 9999))
    address = f"{rng.randint(100, 9999)} {rng.choice(STREETS)} {rng.choice(SUFFIXES)}"
    phone = f"({rng.randint(200, 999)})-555-{rng.randint(1000, 9999)}"
    date = f"2025-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
    time_str = f"{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}"

    # Pick sentence style: 40% concise summary, 60% full CAD narrative
    is_concise = rng.random() < 0.40

    keywords = [target_name, entry_name, suspect_phrase]

    # Generate narrative according to weapon & entry
    if weapon_class == "BLUNT_FORCE":
        weapon_name = rng.choice(WEAPON_VOCABULARY["BLUNT_FORCE"])
        keywords.append(weapon_name)
        if entry_class in ["WINDOW", "FRONT_DOOR", "REAR_DOOR", "GARAGE", "ROOF_VENT"]:
            action = rng.choice(["smashed", "forced open", "pried open", "breached", "shattered"])
            if is_concise:
                narrative = f"Suspect {action} {entry_name} of {target_name} with a {weapon_name} and {fled_phrase}."
            else:
                narrative = (
                    f"On {date} at {time_str}, {suspect_phrase} {action} the {entry_name} of {target_name} "
                    f"located at {address} with a {weapon_name}. The suspect ransacked the interior and {fled_phrase}. "
                    f"Officer {o_first} {o_last} (Badge #{badge}) responded to the dispatch call. Contact: {phone}."
                )
        else: # NOT_APPLICABLE street attack
            action = rng.choice(["struck the victim with a", "attacked the victim using a", "swung a"])
            if is_concise:
                narrative = f"Suspect {action} {weapon_name} during assault on {target_name} and {fled_phrase}."
            else:
                narrative = (
                    f"Officer {o_first} {o_last} (Badge #{badge}) responded to {address} on {date}. "
                    f"Witnesses reported {suspect_phrase} {action} {weapon_name} against {v_first} {v_last} "
                    f"in the {entry_name}. The suspect {fled_phrase}. Dispatch phone: {phone}."
                )

    elif weapon_class == "BLADED":
        weapon_name = rng.choice(WEAPON_VOCABULARY["BLADED"])
        keywords.append(weapon_name)
        if entry_class in ["WINDOW", "FRONT_DOOR", "REAR_DOOR"]:
            action = rng.choice(["brandished a", "wielded a", "threatened occupants with a", "slashed entry screens with a"])
            if is_concise:
                narrative = f"Suspect entered {target_name} via {entry_name} armed with a {weapon_name} and {fled_phrase}."
            else:
                narrative = (
                    f"On {date} at {time_str}, {suspect_phrase} accessed {target_name} through the {entry_name} at {address}. "
                    f"The perpetrator {action} {weapon_name} while demanding cash from {v_first} {v_last}. "
                    f"Officer {o_first} {o_last} (Badge #{badge}) is investigating. Phone: {phone}."
                )
        else: # street attack
            action = rng.choice(["threatened the victim with a", "slashed at the victim using a", "pulled a"])
            if is_concise:
                narrative = f"Suspect {action} {weapon_name} against pedestrian and {fled_phrase}."
            else:
                narrative = (
                    f"At {address} on {date}, {suspect_phrase} {action} {weapon_name} during an encounter with {v_first} {v_last}. "
                    f"Officer {o_first} {o_last} (Badge #{badge}) took the incident report. Phone: {phone}."
                )

    elif weapon_class == "FIREARM":
        weapon_name = rng.choice(WEAPON_VOCABULARY["FIREARM"])
        keywords.append(weapon_name)
        action = rng.choice(["brandished a", "pointed a", "displayed a concealed", "fired a", "aimed a loaded"])
        if entry_class in ["WINDOW", "FRONT_DOOR", "REAR_DOOR", "GARAGE", "ROOF_VENT"]:
            if is_concise:
                narrative = f"Suspect entered {target_name} through {entry_name}, {action} {weapon_name}, and {fled_phrase}."
            else:
                narrative = (
                    f"On {date} at {time_str}, {suspect_phrase} breached the {entry_name} of {target_name} at {address}. "
                    f"The suspect {action} {weapon_name} and demanded money before fleeing. "
                    f"Officer {o_first} {o_last} (Badge #{badge}) responded. Tips: {phone}."
                )
        else:
            if is_concise:
                narrative = f"Suspect {action} {weapon_name} during armed confrontation at {address} and {fled_phrase}."
            else:
                narrative = (
                    f"On {date} at {time_str}, {suspect_phrase} {action} {weapon_name} near {address} while confronting {v_first} {v_last}. "
                    f"Officer {o_first} {o_last} (Badge #{badge}) secured the scene. Phone: {phone}."
                )

    elif weapon_class == "MELEE_OTHER":
        melee_term = rng.choice(WEAPON_VOCABULARY["MELEE_OTHER"])
        keywords.append(melee_term)
        if is_concise:
            narrative = f"Suspect {melee_term} victim near {target_name} and {fled_phrase}."
        else:
            narrative = (
                f"Officer {o_first} {o_last} (Badge #{badge}) was dispatched to {address} on {date}. "
                f"Reports indicate {suspect_phrase} {melee_term} {v_first} {v_last} repeatedly following an altercation. "
                f"The suspect {fled_phrase}. Contact: {phone}."
            )

    else: # NONE
        none_term = rng.choice(WEAPON_VOCABULARY["NONE"])
        keywords.append(none_term)
        if entry_class in ["WINDOW", "FRONT_DOOR", "REAR_DOOR", "GARAGE", "ROOF_VENT"]:
            action = rng.choice(["entered through the unlocked", "walked through the", "slipped in through the open", "climbed through the"])
            if is_concise:
                narrative = f"Suspect was {none_term}, {action} {entry_name} of {target_name}, stole merchandise, and {fled_phrase}."
            else:
                narrative = (
                    f"On {date} at {time_str}, {suspect_phrase} was {none_term} when observed {action} {entry_name} "
                    f"of {target_name} at {address}. Property was removed from the premise. "
                    f"Officer {o_first} {o_last} (Badge #{badge}) took the report. Phone: {phone}."
                )
        else:
            if is_concise:
                narrative = f"Suspect was {none_term} and fled after snatching property from pedestrian."
            else:
                narrative = (
                    f"On {date}, {v_first} {v_last} reported being approached at {address} by {suspect_phrase} "
                    f"who was {none_term}. The suspect took a handbag and {fled_phrase}. "
                    f"Officer {o_first} {o_last} (Badge #{badge}) is investigating. Phone: {phone}."
                )

    labels = {
        "weapon_classification": weapon_class,
        "point_of_entry": entry_class,
        "target_profile": target_class,
        "suspect_count_estimate": suspect_class,
    }

    return narrative, labels, keywords


def build_mo_payload(labels: Dict[str, str], keywords: List[str]) -> dict:
    return {
        "modus_operandi": {
            "weapon_classification": labels["weapon_classification"],
            "weapon_confidence": 0.98,
            "point_of_entry": labels["point_of_entry"],
            "entry_confidence": 0.98,
            "target_profile": labels["target_profile"],
            "target_confidence": 0.98,
            "suspect_count_estimate": labels["suspect_count_estimate"],
            "suspect_count_confidence": 0.98,
        },
        "extracted_keywords": keywords,
        "overall_extraction_confidence": 0.98,
        "error_flag": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate Decoupled Gold Seed Dataset Locally")
    parser.add_argument("--count", type=int, default=3500,
                        help="Number of seed records to generate (default: 3500)")
    default_output = str(PROJECT_ROOT / "data" / "gold_seed_2000.json")
    parser.add_argument("--output", type=str, default=default_output)
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    anonymizer = LocalAnonymizer()

    logger.info("Generating %d Decoupled Gold Seed records...", args.count)

    gold_seeds = []
    for i in range(args.count):
        raw_text, labels, keywords = generate_decoupled_record(rng)
        anon = anonymizer.anonymize(raw_text)
        mo_payload = build_mo_payload(labels, keywords)

        gold_seeds.append({
            "id": i + 1,
            "anonymized_narrative": anon["anonymized_text"],
            "redactions_count": anon["redactions_count"],
            "entity_map": anon["entity_map"],
            "mo_payload": mo_payload,
        })

        if (i + 1) % 500 == 0 or (i + 1) == args.count:
            logger.info("  Generated %d/%d records...", i + 1, args.count)

    # Save output
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(gold_seeds, f, indent=2)

    weapon_dist = Counter(s["mo_payload"]["modus_operandi"]["weapon_classification"] for s in gold_seeds)
    entry_dist = Counter(s["mo_payload"]["modus_operandi"]["point_of_entry"] for s in gold_seeds)
    target_dist = Counter(s["mo_payload"]["modus_operandi"]["target_profile"] for s in gold_seeds)
    suspect_dist = Counter(s["mo_payload"]["modus_operandi"]["suspect_count_estimate"] for s in gold_seeds)

    logger.info("\n" + "=" * 65)
    logger.info("DECOUPLED GOLD SEED GENERATION COMPLETE")
    logger.info("=" * 65)
    logger.info("Total records generated: %d", len(gold_seeds))
    logger.info("Output file:            %s", args.output)
    logger.info("\nLabel Distributions:")
    logger.info("  weapon_classification: %s", dict(weapon_dist))
    logger.info("  point_of_entry:        %s", dict(entry_dist))
    logger.info("  target_profile:        %s", dict(target_dist))
    logger.info("  suspect_count:         %s", dict(suspect_dist))
    logger.info("=" * 65)


if __name__ == "__main__":
    main()
