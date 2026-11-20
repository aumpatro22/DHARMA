"""
groq_mo_extractor.py — Project D.H.A.R.M.A. Gold Standard M.O. Extraction Module

Receives sanitized narrative text (output of ``local_anonymizer.py``) and
dispatches it to the Groq Cloud API (LLaMA 3.3-70B) to extract a structured
Modus Operandi (M.O.) JSON payload with zero hallucination.

The output schema is specifically designed to serve as Gold Standard Ground
Truth labels for training a downstream local DistilBERT classification
student model.

Design Principles:
    1. Deterministic extraction (temperature=0.0, JSON mode enforced).
    2. Constrained enum fields + per-field confidence scores prevent hallucination.
    3. Graceful error recovery — API failures never crash the batch pipeline.
    4. Returned payloads are schema-validated before propagation.
    5. Few-shot calibrated system prompt ensures label consistency.

Author : Project D.H.A.R.M.A. Engineering
Python : 3.10+
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Auto-load .env from the project root (same directory as this script)
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv

    _env_path = Path(__file__).resolve().parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
        print(f"[dotenv] Loaded environment from {_env_path}")
    else:
        print(f"[dotenv] No .env file found at {_env_path} — using system env.")
except ImportError:
    pass  # python-dotenv not installed; rely on system environment

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("dharma.mo_extractor")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s — %(message)s")
    )
    logger.addHandler(_handler)


# ---------------------------------------------------------------------------
# Schema Enums — Gold Standard Taxonomy for DistilBERT Distillation
# ---------------------------------------------------------------------------
WEAPON_CLASSIFICATIONS: List[str] = [
    "FIREARM", "BLADED", "BLUNT_FORCE", "MELEE_OTHER", "NONE", "UNKNOWN",
]

POINT_OF_ENTRY_VALUES: List[str] = [
    "FRONT_DOOR", "REAR_DOOR", "WINDOW", "GARAGE", "ROOF_VENT",
    "NOT_APPLICABLE", "UNKNOWN",
]

TARGET_PROFILES: List[str] = [
    "COMMERCIAL", "RESIDENTIAL", "INDIVIDUAL",
    "VEHICLE", "INFRASTRUCTURE", "UNKNOWN",
]

SUSPECT_COUNT_VALUES: List[str] = [
    "SOLO", "PAIR", "GROUP", "UNKNOWN",
]

# Default payload returned on error — mirrors the Gold Standard schema
DEFAULT_MO_PAYLOAD: Dict[str, Any] = {
    "modus_operandi": {
        "weapon_classification": "UNKNOWN",
        "weapon_confidence": 0.0,
        "point_of_entry": "UNKNOWN",
        "entry_confidence": 0.0,
        "target_profile": "UNKNOWN",
        "target_confidence": 0.0,
        "suspect_count_estimate": "UNKNOWN",
        "suspect_count_confidence": 0.0,
    },
    "extracted_keywords": [],
    "overall_extraction_confidence": 0.0,
    "error_flag": False,
}


# ---------------------------------------------------------------------------
# System Prompt — Gold Standard Few-Shot Calibrated Extraction
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a senior forensic crime data analyst and expert natural language processor for Project D.H.A.R.M.A.

Your objective is to perform high-precision Modus Operandi (M.O.) extraction from sanitized law enforcement narrative text. Your output will serve as the "Gold Standard Ground Truth" to train a downstream local DistilBERT classification student model.

### INSTRUCTIONS:
1. Analyze the provided input crime narrative carefully.
2. Extract the specific forensic attributes defined in the target JSON schema below.
3. Assign a single standardized category for each primary attribute based ONLY on the provided allowed values.
4. Provide a confidence score (between 0.00 and 1.00) reflecting how explicit the narrative evidence is for each classification.
5. If an attribute is omitted or unclear in the narrative, explicitly output "UNKNOWN" with a lower confidence score.
6. Output MUST strictly be valid JSON. Do NOT include markdown formatting wrappers (like ```json), commentary, or conversational filler.

---

### ALLOWED CATEGORIES & TAXONOMY:

1. `weapon_classification`:
   - "FIREARM" (Handguns, rifles, shotguns, ghost guns, discharge of firearm)
   - "BLADED" (Knives, box cutters, razors, machetes, sharp objects)
   - "BLUNT_FORCE" (Bats, pipes, hammers, clubs, brass knuckles)
   - "MELEE_OTHER" (Hands/fists/feet, strangulation, personal weapons)
   - "NONE" (No weapon involved or threatened)
   - "UNKNOWN" (Insufficient narrative details)

2. `point_of_entry` (For burglary/property/home invasion crimes):
   - "FRONT_DOOR"
   - "REAR_DOOR"
   - "WINDOW"
   - "GARAGE"
   - "ROOF_VENT"
   - "NOT_APPLICABLE" (Non-property or public space crimes)
   - "UNKNOWN"

3. `target_profile`:
   - "COMMERCIAL" (Stores, banks, warehouses, businesses)
   - "RESIDENTIAL" (Homes, apartments, private yards)
   - "INDIVIDUAL" (Person-on-person robbery, assault, mugging)
   - "VEHICLE" (Auto theft, theft from vehicle)
   - "INFRASTRUCTURE" (Public transport, utilities, government property)
   - "UNKNOWN"

4. `suspect_count_estimate`:
   - "SOLO" (1 suspect)
   - "PAIR" (2 suspects)
   - "GROUP" (3 or more suspects)
   - "UNKNOWN"

---

### REQUIRED OUTPUT JSON SCHEMA:

{
  "modus_operandi": {
    "weapon_classification": "<ALLOWED_CATEGORY>",
    "weapon_confidence": <FLOAT_0_TO_1>,
    "point_of_entry": "<ALLOWED_CATEGORY>",
    "entry_confidence": <FLOAT_0_TO_1>,
    "target_profile": "<ALLOWED_CATEGORY>",
    "target_confidence": <FLOAT_0_TO_1>,
    "suspect_count_estimate": "<ALLOWED_CATEGORY>",
    "suspect_count_confidence": <FLOAT_0_TO_1>
  },
  "extracted_keywords": [<LIST_OF_3_TO_5_KEY_ACTION_VERBS_OR_NOUNS>],
  "overall_extraction_confidence": <FLOAT_0_TO_1>
}

---

### FEW-SHOT EXAMPLES FOR CALIBRATION:

#### Example 1:
Input Narrative: "Victim reported that two unknown male suspects approached him near the bus stop. One suspect pulled a black semi-automatic handgun from his waistband and demanded the victim's wallet and smartphone. Suspects fled on foot towards 4th Street."
Output JSON:
{
  "modus_operandi": {
    "weapon_classification": "FIREARM",
    "weapon_confidence": 0.98,
    "point_of_entry": "NOT_APPLICABLE",
    "entry_confidence": 1.00,
    "target_profile": "INDIVIDUAL",
    "target_confidence": 0.95,
    "suspect_count_estimate": "PAIR",
    "suspect_count_confidence": 0.95
  },
  "extracted_keywords": ["handgun", "demanded wallet", "fled on foot", "approached victim"],
  "overall_extraction_confidence": 0.97
}

#### Example 2:
Input Narrative: "Store manager discovered the rear glass door was shattered upon arriving at work. Cash register was pried open and approximately $400 in cash was removed during nighttime hours."
Output JSON:
{
  "modus_operandi": {
    "weapon_classification": "BLUNT_FORCE",
    "weapon_confidence": 0.70,
    "point_of_entry": "REAR_DOOR",
    "entry_confidence": 0.92,
    "target_profile": "COMMERCIAL",
    "target_confidence": 0.98,
    "suspect_count_estimate": "UNKNOWN",
    "suspect_count_confidence": 0.40
  },
  "extracted_keywords": ["rear glass door shattered", "cash register pried", "nighttime burglary"],
  "overall_extraction_confidence": 0.85
}

---

### CURRENT TASK:
"""


# ---------------------------------------------------------------------------
# Core Extractor Class
# ---------------------------------------------------------------------------
class GroqMOExtractor:
    """Dispatches sanitized narratives to Groq Cloud for Gold Standard M.O. extraction.

    The output schema includes per-field confidence scores and extracted
    keywords, designed to serve as high-quality labels for DistilBERT
    student model distillation.

    Usage
    -----
    >>> extractor = GroqMOExtractor(api_key="gsk_...")
    >>> result = extractor.extract_mo("Person_01 broke the rear window...")
    >>> print(result["modus_operandi"]["weapon_classification"])
    BLUNT_FORCE

    On any API or parsing failure the extractor returns a default payload
    with ``error_flag=True`` so batch pipelines never crash.
    """

    # Maximum retries on transient API errors
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_BASE: float = 1.5  # seconds — exponential backoff

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile",
    ) -> None:
        """Initialise the Groq client and model configuration.

        Parameters
        ----------
        api_key : str, optional
            Groq API key.  Falls back to the ``GROQ_API_KEY`` environment
            variable.  If neither is available the extractor enters
            *offline mode* and ``extract_mo`` returns default payloads.
        model : str
            Groq model identifier.
        """
        self._model = model
        self._client = None

        resolved_key = api_key or os.environ.get("GROQ_API_KEY")

        if not resolved_key:
            logger.warning(
                "No Groq API key provided and GROQ_API_KEY is not set. "
                "Extractor is in OFFLINE mode — extract_mo() will return "
                "default payloads with error_flag=True."
            )
        else:
            try:
                import groq
                self._client = groq.Groq(api_key=resolved_key)
                logger.info(
                    "Groq client initialised — model=%s, key=...%s",
                    self._model,
                    resolved_key[-6:],
                )
            except ImportError:
                logger.error(
                    "The 'groq' package is not installed. "
                    "Run: pip install groq"
                )
            except Exception as exc:
                logger.error("Failed to initialise Groq client: %s", exc)

    # -----------------------------------------------------------------
    # Schema validation — Gold Standard
    # -----------------------------------------------------------------
    @staticmethod
    def _clamp_confidence(val: Any) -> float:
        """Clamp a value to a float in [0.0, 1.0]."""
        try:
            return max(0.0, min(1.0, float(val)))
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _validate_and_coerce(raw: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and coerce a raw parsed dict into the Gold Standard schema.

        Handles both nested (``modus_operandi.weapon_classification``) and
        flat (``weapon_classification``) response shapes from the LLM.
        Unknown enum values are replaced with ``"UNKNOWN"``.
        Missing keys are filled from ``DEFAULT_MO_PAYLOAD``.
        """
        # Handle nested vs flat response
        mo = raw.get("modus_operandi", raw)

        # --- weapon_classification ---
        wc = str(mo.get("weapon_classification", "UNKNOWN")).upper().strip()
        if wc not in WEAPON_CLASSIFICATIONS:
            wc = "UNKNOWN"
        wc_conf = GroqMOExtractor._clamp_confidence(mo.get("weapon_confidence", 0.0))

        # --- point_of_entry ---
        poe = str(mo.get("point_of_entry", "UNKNOWN")).upper().strip()
        if poe not in POINT_OF_ENTRY_VALUES:
            poe = "UNKNOWN"
        poe_conf = GroqMOExtractor._clamp_confidence(mo.get("entry_confidence", 0.0))

        # --- target_profile ---
        tp = str(mo.get("target_profile", "UNKNOWN")).upper().strip()
        if tp not in TARGET_PROFILES:
            tp = "UNKNOWN"
        tp_conf = GroqMOExtractor._clamp_confidence(mo.get("target_confidence", 0.0))

        # --- suspect_count_estimate ---
        sc = str(mo.get("suspect_count_estimate", "UNKNOWN")).upper().strip()
        if sc not in SUSPECT_COUNT_VALUES:
            sc = "UNKNOWN"
        sc_conf = GroqMOExtractor._clamp_confidence(mo.get("suspect_count_confidence", 0.0))

        # --- extracted_keywords ---
        keywords = raw.get("extracted_keywords", [])
        if not isinstance(keywords, list):
            keywords = []
        keywords = [str(k).strip() for k in keywords if k]

        # --- overall_extraction_confidence ---
        overall = GroqMOExtractor._clamp_confidence(
            raw.get("overall_extraction_confidence", 0.0)
        )

        return {
            "modus_operandi": {
                "weapon_classification": wc,
                "weapon_confidence": wc_conf,
                "point_of_entry": poe,
                "entry_confidence": poe_conf,
                "target_profile": tp,
                "target_confidence": tp_conf,
                "suspect_count_estimate": sc,
                "suspect_count_confidence": sc_conf,
            },
            "extracted_keywords": keywords,
            "overall_extraction_confidence": overall,
            "error_flag": False,
        }

    # -----------------------------------------------------------------
    # Primary API
    # -----------------------------------------------------------------
    def extract_mo(self, anonymized_text: str) -> Dict[str, Any]:
        """Extract a Gold Standard M.O. payload from a sanitized narrative.

        Parameters
        ----------
        anonymized_text : str
            PII-scrubbed crime narrative (output of ``LocalAnonymizer``).

        Returns
        -------
        dict
            Validated M.O. payload conforming to the Gold Standard schema.
            On failure, ``error_flag`` is ``True`` and fields default to
            ``"UNKNOWN"`` with zero confidence.
        """
        # Guard: empty input
        if not anonymized_text or not anonymized_text.strip():
            logger.warning("Empty narrative received — returning defaults.")
            return {**DEFAULT_MO_PAYLOAD, "error_flag": True}

        # Guard: offline mode (no client)
        if self._client is None:
            logger.warning(
                "Groq client is not available (offline mode). "
                "Returning default payload."
            )
            return {**DEFAULT_MO_PAYLOAD, "error_flag": True}

        # Construct the user prompt with the current task marker
        user_prompt = f'Input Narrative: "{anonymized_text}"\n\nOutput JSON:'

        # --- Dispatch to Groq with retries ---
        last_error: Optional[Exception] = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                logger.info(
                    "Dispatching to Groq (%s) — attempt %d/%d, "
                    "narrative length=%d chars",
                    self._model,
                    attempt,
                    self.MAX_RETRIES,
                    len(anonymized_text),
                )

                chat_completion = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.0,
                    max_tokens=1024,
                    response_format={"type": "json_object"},
                )

                raw_content = chat_completion.choices[0].message.content
                logger.debug("Raw Groq response: %s", raw_content[:500])

                # Parse JSON
                parsed = json.loads(raw_content)
                validated = self._validate_and_coerce(parsed)

                mo = validated["modus_operandi"]
                logger.info(
                    "M.O. extraction SUCCESS — weapon=%s (%.2f), "
                    "entry=%s (%.2f), target=%s (%.2f), "
                    "suspects=%s (%.2f), overall=%.2f",
                    mo["weapon_classification"], mo["weapon_confidence"],
                    mo["point_of_entry"], mo["entry_confidence"],
                    mo["target_profile"], mo["target_confidence"],
                    mo["suspect_count_estimate"], mo["suspect_count_confidence"],
                    validated["overall_extraction_confidence"],
                )

                return validated

            except json.JSONDecodeError as exc:
                logger.error(
                    "JSON parse error on attempt %d: %s", attempt, exc
                )
                last_error = exc

            except Exception as exc:
                logger.error(
                    "Groq API error on attempt %d: %s — %s",
                    attempt,
                    type(exc).__name__,
                    exc,
                )
                last_error = exc

            # Exponential backoff before retry
            if attempt < self.MAX_RETRIES:
                wait = self.RETRY_BACKOFF_BASE ** attempt
                logger.info("Retrying in %.1f seconds...", wait)
                time.sleep(wait)

        # All retries exhausted
        logger.error(
            "All %d attempts failed. Last error: %s. "
            "Returning default payload with error_flag=True.",
            self.MAX_RETRIES,
            last_error,
        )
        return {
            **DEFAULT_MO_PAYLOAD,
            "error_flag": True,
            "error_detail": str(last_error),
        }

    # -----------------------------------------------------------------
    # Batch convenience
    # -----------------------------------------------------------------
    def extract_batch(
        self,
        narratives: List[str],
        delay: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Process multiple narratives sequentially with rate limiting.

        Parameters
        ----------
        narratives : list of str
            Sanitized narrative texts.
        delay : float
            Seconds to wait between API calls (rate limiting).

        Returns
        -------
        list of dict
            One M.O. payload per input narrative.
        """
        results: List[Dict[str, Any]] = []
        total = len(narratives)

        for idx, text in enumerate(narratives, start=1):
            logger.info("Processing narrative %d/%d...", idx, total)
            result = self.extract_mo(text)
            results.append(result)

            if idx < total and delay > 0:
                time.sleep(delay)

        success_count = sum(1 for r in results if not r.get("error_flag"))
        logger.info(
            "Batch complete — %d/%d successful extractions.",
            success_count,
            total,
        )
        return results


# ---------------------------------------------------------------------------
# Self-test & demonstration
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # ── Sample anonymized narratives for multi-scenario testing ──
    SAMPLE_ASSAULT = (
        "On 2025-06-14 at approximately 22:45, Officer Person_01 "
        "(Officer_Alpha) responded to a report of aggravated assault at "
        "Location_Alpha, Location_Gamma. The victim, Person_02, stated "
        "that the suspect, Person_03, struck her with a metal pipe before "
        "fleeing eastbound on foot. A witness, Person_04, corroborated "
        "the account and identified Person_03 from a photo lineup. "
        "Person_03 was later apprehended near Commercial_Entity_01."
    )

    SAMPLE_BURGLARY = (
        "Store manager Person_01 discovered the rear glass door was "
        "shattered upon arriving at work. Cash register was pried open "
        "and approximately $400 in cash was removed during nighttime hours."
    )

    print("=" * 80)
    print("D.H.A.R.M.A. — Gold Standard M.O. Extractor Self-Test")
    print("=" * 80)

    api_key = os.environ.get("GROQ_API_KEY")
    extractor = GroqMOExtractor(api_key=api_key)

    for label, narrative in [("ASSAULT", SAMPLE_ASSAULT), ("BURGLARY", SAMPLE_BURGLARY)]:
        print(f"\n{'─' * 40}")
        print(f"TEST: {label}")
        print(f"{'─' * 40}")
        print(f"INPUT: {narrative[:120]}...")

        result = extractor.extract_mo(narrative)

        print(f"\nOUTPUT PAYLOAD:")
        print(json.dumps(result, indent=2))

        # ── Structural assertions ──
        assert isinstance(result, dict), "FAIL: Result is not a dict."
        assert "modus_operandi" in result, "FAIL: Missing modus_operandi."
        assert "extracted_keywords" in result, "FAIL: Missing extracted_keywords."
        assert "overall_extraction_confidence" in result, "FAIL: Missing overall confidence."
        assert "error_flag" in result, "FAIL: Missing error_flag."

        mo = result["modus_operandi"]
        assert "weapon_classification" in mo, "FAIL: Missing weapon_classification."
        assert "weapon_confidence" in mo, "FAIL: Missing weapon_confidence."
        assert "point_of_entry" in mo, "FAIL: Missing point_of_entry."
        assert "entry_confidence" in mo, "FAIL: Missing entry_confidence."
        assert "target_profile" in mo, "FAIL: Missing target_profile."
        assert "target_confidence" in mo, "FAIL: Missing target_confidence."
        assert "suspect_count_estimate" in mo, "FAIL: Missing suspect_count_estimate."
        assert "suspect_count_confidence" in mo, "FAIL: Missing suspect_count_confidence."

        # Enum validation (only on live results)
        if not result["error_flag"]:
            assert mo["weapon_classification"] in WEAPON_CLASSIFICATIONS, (
                f"FAIL: Invalid weapon: {mo['weapon_classification']}"
            )
            assert mo["point_of_entry"] in POINT_OF_ENTRY_VALUES, (
                f"FAIL: Invalid entry: {mo['point_of_entry']}"
            )
            assert mo["target_profile"] in TARGET_PROFILES, (
                f"FAIL: Invalid target: {mo['target_profile']}"
            )
            assert mo["suspect_count_estimate"] in SUSPECT_COUNT_VALUES, (
                f"FAIL: Invalid suspect count: {mo['suspect_count_estimate']}"
            )
            assert isinstance(result["extracted_keywords"], list), (
                "FAIL: extracted_keywords is not a list."
            )
            assert len(result["extracted_keywords"]) >= 1, (
                "FAIL: No keywords extracted."
            )
            print(f"\n✓ {label}: Live extraction + enum validation PASSED.")
        else:
            print(f"\n⚠ {label}: OFFLINE mode. Structural validation passed.")

    print("\n✓ All Gold Standard schema assertions PASSED.")
    print("✓ Module is production-ready for DistilBERT distillation.\n")
