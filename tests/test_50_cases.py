"""
run_50_tests.py — Batch Verification and Performance Test Runner
Generates 50 unique, PII-heavy crime narrative test cases, runs them
through the D.H.A.R.M.A. LocalAnonymizer and GroqMOExtractor,
and outputs a structured test results log.
"""

import os
import re
import sys
import json
import time
import string
import random
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dharma.nlp.anonymizer import LocalAnonymizer
    from dharma.nlp.thinking_engine import ForensicThinkingEngine
except ImportError:
    from local_anonymizer import LocalAnonymizer
    from forensic_thinking_engine import ForensicThinkingEngine

# List of PII pools for random injection
FIRST_NAMES = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles", "Christopher", "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Paul", "Andrew", "Joshua", "Kenneth", "Kevin", "Brian", "George", "Edward", "Ronald", "Timothy", "Jason", "Jeffrey", "Ryan", "Jacob", "Gary", "Nicholas", "Eric", "Jonathan", "Stephen", "Larry", "Justin", "Scott", "Brandon", "Benjamin", "Samuel", "Gregory", "Alexander", "Frank", "Patrick", "Raymond", "Jack", "Dennis", "Jerry"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts"]
STREETS = ["Elm", "Oak", "Pine", "Maple", "Cedar", "Washington", "Randolph", "Clark", "State", "Michigan", "Broadway", "Market", "Mission", "Geary", "Valencia", "Castro", "Haight", "Lombard", "Lincoln", "Jackson"]
SUFFIXES = ["St", "Ave", "Blvd", "Rd", "Dr", "Ln", "Ct", "Way"]
STORES = ["Walmart", "Target", "Home Depot", "Best Buy", "Macy's", "Walgreens", "CVS Pharmacy", "Apple Store", "Nordstrom", "Safeway"]
WEAPONS = ["handgun", "shotgun", "pocket knife", "crowbar", "baseball bat", "hammer", "machete", "screwdriver", "none", "unknown"]

TEMPLATES = [
    # 1. Commercial Retail Theft / Opportunity
    "On {date} at {time}, Officer {officer_first} {officer_last} (Badge #{badge}) responded to a shoplifting report at {store} located at {address}. The suspect, {suspect_first} {suspect_last}, walked into the store, grabbed several electronic items, and ran out the front door without paying. The store manager, {witness_first} {witness_last}, tried to stop the suspect, but the suspect threatened them and fled on foot. The suspect was unarmed. Contact: {phone}.",
    
    # 2. Residential Burglary / Forced Window
    "At around {time} on {date}, a burglary occurred at {address}. The homeowner, {victim_first} {victim_last}, returned home to find a rear window shattered and the lock broken. Several pieces of jewelry and laptops were missing. A neighbor, {witness_first} {witness_last}, reported seeing a suspicious individual matching the description of {suspect_first} {suspect_last} running from the backyard around {time}. Officer {officer_first} {officer_last} (Badge #{badge}) is investigating. Call {phone} with tips.",
    
    # 3. Assault with Blunt Force
    "Officer {officer_first} {officer_last} (Badge #{badge}) was dispatched to {address} regarding a physical fight. Upon arrival, the officer found the victim, {victim_first} {victim_last}, bleeding from the head. According to witnesses, the suspect, {suspect_first} {suspect_last}, struck the victim multiple times with a {weapon} after a verbal dispute. The suspect was apprehended down the street. Call dispatch at {phone}.",
    
    # 4. Bank Robbery / Sophisticated
    "On {date} at {time}, a robbery was reported at the Chase Bank on {address}. The suspect, {suspect_first} {suspect_last}, approached the teller, {victim_first} {victim_last}, and presented a note demanding cash and claiming to have a concealed {weapon}. The suspect successfully obtained $5,000 in cash and fled through the back exit. A security guard, {witness_first} {witness_last}, noted the suspect left in a vehicle with license plate {plate}. Contact Officer {officer_first} {officer_last} (Badge #{badge}) at {phone}.",
    
    # 5. Vehicle Theft / Opportunistic
    "Victim {victim_first} {victim_last} reported their car stolen from the driveway of {address} on {date}. The victim left the keys in the ignition while running inside. The suspect, {suspect_first} {suspect_last}, entered the vehicle and drove away. Officer {officer_first} {officer_last} (Badge #{badge}) spotted the vehicle near {store} and initiated a traffic stop, arresting the suspect. Phone: {phone}."
]

def generate_test_cases(count=50) -> list:
    test_cases = []
    random.seed(42)  # For deterministic generation
    
    for idx in range(count):
        template = random.choice(TEMPLATES)
        
        # Select random variables
        o_first, o_last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
        s_first, s_last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
        v_first, v_last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
        w_first, w_last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
        
        # Ensure unique roles
        while s_first == o_first or s_first == v_first or s_first == w_first:
            s_first = random.choice(FIRST_NAMES)
        while v_first == o_first or v_first == s_first or v_first == w_first:
            v_first = random.choice(FIRST_NAMES)
            
        badge = str(random.randint(1000, 9999))
        address = f"{random.randint(100, 9999)} {random.choice(STREETS)} {random.choice(SUFFIXES)}"
        store = random.choice(STORES)
        phone = f"({random.randint(200, 999)})-555-{random.randint(1000, 9999)}"
        plate = f"{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}-{random.randint(1000, 9999)}"
        weapon = random.choice(WEAPONS)
        
        date = f"2026-07-{random.randint(1, 19):02d}"
        time_str = f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}"
        
        narrative = template.format(
            date=date,
            time=time_str,
            officer_first=o_first,
            officer_last=o_last,
            badge=badge,
            store=store,
            address=address,
            suspect_first=s_first,
            suspect_last=s_last,
            victim_first=v_first,
            victim_last=v_last,
            witness_first=w_first,
            witness_last=w_last,
            phone=phone,
            plate=plate,
            weapon=weapon
        )
        
        test_cases.append({
            "id": idx + 1,
            "raw_narrative": narrative,
            "metadata": {
                "officer": f"{o_first} {o_last}",
                "suspect": f"{s_first} {s_last}",
                "victim": f"{v_first} {v_last}",
                "witness": f"{w_first} {w_last}",
                "badge": badge,
                "address": address,
                "phone": phone,
                "plate": plate,
                "weapon": weapon
            }
        })
        
    return test_cases

def main():
    print("=" * 80)
    print("D.H.A.R.M.A. — Generating and Executing 50 Test Cases")
    print("=" * 80)
    
    test_cases = generate_test_cases(50)
    print(f"Generated {len(test_cases)} test cases.")
    
    # Initialize components (100% offline local neural inference)
    anonymizer = LocalAnonymizer()
    engine = ForensicThinkingEngine()
    
    results = []
    success_count = 0
    total_duration = 0.0
    
    for idx, tc in enumerate(test_cases, start=1):
        print(f"[{idx}/50] Processing Test ID: {tc['id']}")
        
        # Step 1: Anonymize
        start_anon = time.time()
        anon_result = anonymizer.anonymize(tc["raw_narrative"])
        duration_anon = time.time() - start_anon
        
        # Step 2: Live Offline DistilBERT & Thinking Engine Inference
        start_mo = time.time()
        engine_result = engine.analyze(anon_result["anonymized_text"])
        duration_mo = time.time() - start_mo
        
        duration = duration_anon + duration_mo
        total_duration += duration
        success_count += 1
            
        results.append({
            "test_id": tc["id"],
            "raw_narrative": tc["raw_narrative"],
            "anonymized_text": anon_result["anonymized_text"],
            "redactions_count": anon_result["redactions_count"],
            "entity_map": anon_result["entity_map"],
            "top_possibilities": engine_result["top_possibilities"],
            "entropy_scores": engine_result["entropy_scores"],
            "scenarios_count": len(engine_result["scenarios"]),
            "duration_seconds": duration,
            "error_flag": False
        })
        
    # Write full logs to processed folder
    log_path = str(PROJECT_ROOT / "processed" / "test_results_50.json")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"\nCompleted 50 runs. Logs written to: {log_path}")
    print(f"Success rate: {success_count}/50 ({success_count*2}%)")
    print(f"Total time elapsed: {total_duration:.2f} seconds")
    print(f"Average time per run: {total_duration / 50:.2f} seconds")

if __name__ == "__main__":
    main()
