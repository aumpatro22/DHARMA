"""
local_anonymizer.py — Project D.H.A.R.M.A. PII Scrubbing Module

A hybrid Regex + spaCy NER anonymizer that removes Personally Identifiable
Information (PII) and CJIS-restricted identifiers from crime narrative text
before any off-premises API transmission.

Design Principles:
    1. Zero PII leakage to cloud endpoints.
    2. Coreference-consistent token substitution (same entity → same token).
    3. Sentence structure and entity relationships are preserved so downstream
       Modus Operandi extraction remains reliable.

Author : Project D.H.A.R.M.A. Engineering
Python : 3.10+
"""

from __future__ import annotations

import logging
import re
import string
import sys
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("dharma.anonymizer")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s — %(message)s")
    )
    logger.addHandler(_handler)


# ---------------------------------------------------------------------------
# Token alphabet for human-readable replacement labels
# ---------------------------------------------------------------------------
_GREEK = [
    "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta",
    "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron", "Pi",
    "Rho", "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega",
]


def _ordinal(n: int) -> str:
    """Return a zero-padded two-digit ordinal string: 1 → '01', 12 → '12'."""
    return f"{n:02d}"


# ---------------------------------------------------------------------------
# Regex pattern library — structured PII pre-pass
# ---------------------------------------------------------------------------
_PATTERNS: List[Tuple[str, re.Pattern]] = [
    # US phone numbers  (xxx) xxx-xxxx | xxx-xxx-xxxx | xxx.xxx.xxxx | +1...
    (
        "PHONE",
        re.compile(
            r"""
            (?<!\d)                          # no leading digit
            (?:\+?1[\s.\-]?)?                # optional country code
            (?:\(\d{3}\)|\d{3})              # area code
            [\s.\-]?                          # separator
            \d{3}                            # exchange
            [\s.\-]?                          # separator
            \d{4}                            # subscriber
            (?!\d)                           # no trailing digit
            """,
            re.VERBOSE,
        ),
    ),
    # UK phone numbers  +44 ... | 07xxx ...
    (
        "PHONE",
        re.compile(
            r"""
            (?<!\d)
            (?:\+44[\s.\-]?\d{2,4}[\s.\-]?\d{3,4}[\s.\-]?\d{3,4})
            |
            (?:0[1-9]\d{2,3}[\s.\-]?\d{3,4}[\s.\-]?\d{3,4})
            (?!\d)
            """,
            re.VERBOSE,
        ),
    ),
    # Indian phone numbers  +91 98765 43210 | +91-9876543210 | 9876543210
    (
        "PHONE",
        re.compile(
            r"""
            (?<!\d)
            (?:\+91[\s.\-]?)?
            (?:[6-9]\d{4}[\s.\-]?\d{5})
            (?!\d)
            """,
            re.VERBOSE,
        ),
    ),
    # International E.164 phone numbers (+country_code ...)
    (
        "PHONE",
        re.compile(
            r"""
            (?<!\d)
            \+\d{1,3}[\s.\-]?(?:\(?\d{1,4}\)?[\s.\-]?)?\d{3,4}[\s.\-]?\d{3,5}
            (?!\d)
            """,
            re.VERBOSE,
        ),
    ),
    # National ID / Aadhaar Number  xxxx xxxx xxxx or 18-digit Resident ID
    (
        "NATIONAL_ID",
        re.compile(
            r"""
            (?<!\d)
            (?:\d{4}[\s\-]\d{4}[\s\-]\d{4}|\d{17}[\dXx])
            (?!\d)
            """,
            re.VERBOSE,
        ),
    ),
    # Badge / Officer ID  — Badge #1234, Badge No. 1234, Officer ID 991
    (
        "BADGE",
        re.compile(
            r"""
            (?:Badge|Officer\s*ID|Shield|Star)
            [\s\#:.\-]*
            (\d{2,6})
            """,
            re.VERBOSE | re.IGNORECASE,
        ),
    ),
    # Social Security Number  xxx-xx-xxxx
    (
        "SSN",
        re.compile(
            r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)",
        ),
    ),
    # US Street Address — number + street name + suffix
    (
        "ADDRESS",
        re.compile(
            r"""
            \b
            \d{1,6}                                  # house number
            \s+
            (?:(?:N|S|E|W|NE|NW|SE|SW|North|South|East|West)\.?\s+)?  # direction
            (?:[A-Z][a-zA-Z']+\s*){1,4}             # street name (1-4 words)
            (?:St(?:reet)?|Ave(?:nue)?|Blvd|Boulevard|Dr(?:ive)?|
               Rd|Road|Ln|Lane|Ct|Court|Pl(?:ace)?|Way|
               Pkwy|Parkway|Cir(?:cle)?|Ter(?:race)?)
            \.?
            """,
            re.VERBOSE | re.IGNORECASE,
        ),
    ),
    # US ZIP code  — 5-digit or ZIP+4
    (
        "ZIPCODE",
        re.compile(
            r"(?<!\d)\d{5}(?:-\d{4})?(?!\d)",
        ),
    ),
    # UK Postcode  — A9 9AA / A99 9AA / A9A 9AA …
    (
        "POSTCODE",
        re.compile(
            r"""
            \b
            [A-Z]{1,2}\d[A-Z\d]?   # outward code
            \s*
            \d[A-Z]{2}             # inward code
            \b
            """,
            re.VERBOSE | re.IGNORECASE,
        ),
    ),
    # Email addresses
    (
        "EMAIL",
        re.compile(
            r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
        ),
    ),
    # Driver's licence style IDs — DL# or License# followed by alphanum
    (
        "LICENSE",
        re.compile(
            r"""
            (?:DL|Driver'?s?\s*Licen[sc]e|License)
            [\s\#:.\-]*
            [A-Z0-9]{5,15}
            """,
            re.VERBOSE | re.IGNORECASE,
        ),
    ),
    # Vehicle plate numbers — common US format  ABC-1234, ABC 1234, 1ABC234
    (
        "PLATE",
        re.compile(
            r"""
            \b
            (?:[A-Z]{3}[\s\-]?\d{3,4})       # ABC-1234  (require 3 letters)
            |
            (?:\d[A-Z]{3}\d{3})               # 1ABC234  (California)
            \b
            """,
            re.VERBOSE,
        ),
    ),
]


# ---------------------------------------------------------------------------
# spaCy entity-label → token-prefix mapping
# ---------------------------------------------------------------------------
_NER_PREFIX_MAP: Dict[str, str] = {
    "PERSON": "Person",
    "ORG":    "Commercial_Entity",
    "FAC":    "Facility",
    "GPE":    "Location",
    "LOC":    "Location",
}

_REGEX_PREFIX_MAP: Dict[str, str] = {
    "PHONE":    "Phone",
    "BADGE":    "Officer",
    "SSN":      "SSN",
    "ADDRESS":  "Location",
    "ZIPCODE":  "Zipcode",
    "POSTCODE": "Postcode",
    "EMAIL":    "Email",
    "LICENSE":  "License",
    "PLATE":    "Plate",
}


# ---------------------------------------------------------------------------
# Core Anonymizer Class
# ---------------------------------------------------------------------------
class LocalAnonymizer:
    """Hybrid Regex + spaCy NER anonymizer with coreference-consistent tokens.

    Usage
    -----
    >>> anon = LocalAnonymizer()
    >>> result = anon.anonymize("John Doe was seen at 455 West Randolph St.")
    >>> print(result["anonymized_text"])
    Person_01 was seen at Location_Alpha.

    The returned ``entity_map`` allows local audit-trail reconstruction
    without ever transmitting the original PII off-premises.
    """

    def __init__(self, spacy_model: str = "en_core_web_sm") -> None:
        """Load the spaCy pipeline and compile regex patterns.

        Parameters
        ----------
        spacy_model : str
            Name of the spaCy model to load.  Falls back gracefully if the
            model is unavailable (regex-only mode).
        """
        self._nlp = None

        try:
            import spacy
            self._nlp = spacy.load(spacy_model)
            logger.info("spaCy model '%s' loaded successfully.", spacy_model)
        except ImportError:
            logger.warning(
                "spaCy is not installed. Running in regex-only mode."
            )
        except OSError:
            logger.warning(
                "spaCy model '%s' not found. Attempting download...",
                spacy_model,
            )
            try:
                import spacy.cli
                spacy.cli.download(spacy_model)
                import spacy
                self._nlp = spacy.load(spacy_model)
                logger.info("Model '%s' downloaded and loaded.", spacy_model)
            except Exception as exc:
                logger.error(
                    "Failed to download spaCy model: %s. "
                    "Falling back to regex-only mode.",
                    exc,
                )

        self._patterns = _PATTERNS
        logger.info(
            "LocalAnonymizer initialised — %d regex patterns, NLP=%s",
            len(self._patterns),
            "active" if self._nlp else "disabled",
        )

    # -----------------------------------------------------------------
    # Token state management (per-call)
    # -----------------------------------------------------------------
    @staticmethod
    def _make_token_generator(prefix: str):
        """Return a stateful callable that yields sequential tokens.

        For 'Person' → Person_01, Person_02, …
        For 'Officer' → Officer_Alpha, Officer_Beta, …
        For 'Location' → Location_Alpha, Location_Beta, …
        """
        # Categories that use Greek letter suffixes
        _GREEK_PREFIXES = {"Officer", "Location", "Facility"}

        counter = 0

        def _next() -> str:
            nonlocal counter
            counter += 1
            if prefix in _GREEK_PREFIXES:
                suffix = _GREEK[counter - 1] if counter <= len(_GREEK) else f"_{counter}"
                return f"{prefix}_{suffix}"
            return f"{prefix}_{_ordinal(counter)}"

        return _next

    # -----------------------------------------------------------------
    # Primary API
    # -----------------------------------------------------------------
    def anonymize(self, text: str) -> Dict[str, object]:
        """Anonymize PII in *text* and return a structured payload.

        Parameters
        ----------
        text : str
            Raw crime narrative containing potential PII.

        Returns
        -------
        dict
            ``anonymized_text``  — sanitized narrative string.
            ``redactions_count`` — total number of redacted entities.
            ``entity_map``       — ``{generated_token: entity_type}`` for audit.
        """
        if not text or not text.strip():
            return {
                "anonymized_text": text,
                "redactions_count": 0,
                "entity_map": {},
            }

        # Mapping:  original_text (lowered) → assigned token
        _seen: Dict[str, str] = {}
        # Token generators per prefix
        _generators: Dict[str, callable] = {}
        # Audit map:  token → type label
        entity_map: Dict[str, str] = {}
        # Ordered list of (start, end, token, entity_type)
        redactions: List[Tuple[int, int, str, str]] = []

        # ── Step 1: Regex pre-pass ──────────────────────────────────
        for label, pattern in self._patterns:
            for m in pattern.finditer(text):
                span_text = m.group().strip()
                if not span_text:
                    continue

                prefix = _REGEX_PREFIX_MAP.get(label, label)
                key = span_text.lower()

                if key in _seen:
                    token = _seen[key]
                else:
                    if prefix not in _generators:
                        _generators[prefix] = self._make_token_generator(prefix)
                    token = _generators[prefix]()
                    _seen[key] = token
                    entity_map[token] = label

                redactions.append((m.start(), m.end(), token, label))

        # ── Step 2: spaCy NER post-pass ─────────────────────────────
        if self._nlp is not None:
            doc = self._nlp(text)
            for ent in doc.ents:
                if ent.label_ not in _NER_PREFIX_MAP:
                    continue

                # Skip if this span was already captured by regex
                overlap = any(
                    not (ent.end_char <= rs or ent.start_char >= re_)
                    for rs, re_, _, _ in redactions
                )
                if overlap:
                    continue

                span_text = ent.text.strip()
                if not span_text or len(span_text) < 2:
                    continue

                prefix = _NER_PREFIX_MAP[ent.label_]
                key = span_text.lower()

                if key in _seen:
                    token = _seen[key]
                else:
                    if prefix not in _generators:
                        _generators[prefix] = self._make_token_generator(prefix)
                    token = _generators[prefix]()
                    _seen[key] = token
                    entity_map[token] = ent.label_

                redactions.append(
                    (ent.start_char, ent.end_char, token, ent.label_)
                )

        # ── Step 3: Apply redactions (reverse order to preserve offsets) ──
        redactions.sort(key=lambda r: r[0], reverse=True)

        anonymized = text
        for start, end, token, _ in redactions:
            anonymized = anonymized[:start] + token + anonymized[end:]

        redactions_count = len(redactions)

        logger.info(
            "Anonymization complete — %d redaction(s) applied across %d unique entities.",
            redactions_count,
            len(entity_map),
        )

        return {
            "anonymized_text": anonymized,
            "redactions_count": redactions_count,
            "entity_map": entity_map,
        }


# ---------------------------------------------------------------------------
# Self-test & CLI entrypoint
# ---------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Project D.H.A.R.M.A. Local PII Anonymizer")
    parser.add_argument("--text", type=str, default=None, help="Narrative text to scrub")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    anon = LocalAnonymizer()

    if args.text:
        res = anon.anonymize(args.text)
        print("\n" + "=" * 80)
        print("ORIGINAL NARRATIVE")
        print("=" * 80)
        print(args.text)
        print("\n" + "=" * 80)
        print("ANONYMIZED NARRATIVE")
        print("=" * 80)
        print(res["anonymized_text"])
        print("\n" + "=" * 80)
        print(f"REDACTIONS COUNT: {res['redactions_count']}")
        print("=" * 80)
        print("\nENTITY MAP:")
        for token, etype in sorted(res["entity_map"].items()):
            print(f"  {token:30s} → {etype}")
        return

    SAMPLE_NARRATIVE = (
        "On 2025-06-14 at approximately 22:45, Officer James Rivera (Badge #4821) "
        "responded to a report of aggravated assault at 455 West Randolph St, "
        "Chicago, IL 60606. The victim, Maria Santos, stated that the suspect, "
        "John Doe, struck her with a metal pipe before fleeing eastbound on foot. "
        "A witness, David Kim, corroborated the account and identified John Doe "
        "from a photo lineup. Officer Rivera collected evidence from the scene. "
        "The suspect was later apprehended near a Walgreens at 200 North State St "
        "by Officer Tanaka (Badge #3317). John Doe was transported to Cook County "
        "Jail. Contact: (312) 555-0198. Case forwarded to the DA's office."
    )

    result = anon.anonymize(SAMPLE_NARRATIVE)

    print("\n" + "=" * 80)
    print("ORIGINAL NARRATIVE")
    print("=" * 80)
    print(SAMPLE_NARRATIVE)

    print("\n" + "=" * 80)
    print("ANONYMIZED NARRATIVE")
    print("=" * 80)
    print(result["anonymized_text"])

    print("\n" + "=" * 80)
    print(f"REDACTIONS COUNT: {result['redactions_count']}")
    print("=" * 80)

    print("\nENTITY MAP (for local audit trail):")
    for token, etype in sorted(result["entity_map"].items()):
        print(f"  {token:30s} → {etype}")

    # ── Assertions ──────────────────────────────────────────────────
    a_text = result["anonymized_text"]

    assert "John Doe" not in a_text, "FAIL: Raw person name leaked."
    assert "Maria Santos" not in a_text, "FAIL: Raw person name leaked."
    assert "David Kim" not in a_text, "FAIL: Raw person name leaked."
    assert "James Rivera" not in a_text, "FAIL: Raw officer name leaked."
    assert "(312) 555-0198" not in a_text, "FAIL: Phone number leaked."
    assert "4821" not in a_text, "FAIL: Badge number leaked."
    assert "3317" not in a_text, "FAIL: Badge number leaked."

    print(f"\n✓ PII leakage check PASSED: No raw names, phones, or badges in output.")
    print(f"✓ All {result['redactions_count']} redactions applied successfully.\n")


if __name__ == "__main__":
    main()
