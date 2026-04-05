"""
TerminologyChecker — Flags non-standard clinical terminology and
unmapped abbreviations in clinical documentation.

Checks clinical text against standard medical abbreviation dictionaries
and identifies terms that may impede accurate clinical coding and
interoperability.

Author: Michael Kwakye Agyapong
"""

import re
import json
import os
from typing import Dict, List, Tuple, Set
from .analyzer import Deficiency


# Common non-standard terms and their standard equivalents
TERMINOLOGY_CORRECTIONS = {
    "sugar": "blood glucose",
    "blood sugar": "blood glucose",
    "water pill": "diuretic",
    "blood thinner": "anticoagulant",
    "breathing treatment": "nebulizer therapy",
    "heart attack": "myocardial infarction",
    "stroke": "cerebrovascular accident",
    "mini stroke": "transient ischemic attack",
    "fits": "seizures",
    "sugar diabetes": "diabetes mellitus",
    "hardening of the arteries": "atherosclerosis",
    "high blood": "hypertension",
    "low blood": "hypotension",
    "kidney failure": "renal failure",
    "bed sore": "pressure injury",
    "bedsore": "pressure injury",
    "pressure sore": "pressure injury",
    "decub": "pressure injury",
    "fall out": "syncope",
    "passing out": "syncope",
}


class TerminologyChecker:
    """
    Checks clinical text for non-standard terminology and abbreviations.

    Identifies clinical terms that may impede accurate ICD-10-CM/SNOMED CT
    mapping, flags unexpanded abbreviations, and suggests standard
    terminology replacements.

    Parameters
    ----------
    config : dict
        Configuration dictionary with terminology settings.
    """

    def __init__(self, config: dict):
        term_config = config.get("terminology", {})
        self.flag_abbreviations = term_config.get("flag_abbreviations", True)
        self.flag_unmapped = term_config.get("flag_unmapped_terms", True)
        self.abbreviation_dict = self._load_abbreviations(term_config)

    def _load_abbreviations(self, config: dict) -> Dict[str, str]:
        """Load medical abbreviation dictionary."""
        abbrev_path = config.get(
            "abbreviation_dict",
            os.path.join(os.path.dirname(os.path.dirname(__file__)),
                         "config", "medical_abbreviations.json")
        )
        try:
            with open(abbrev_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def check(self, text: str) -> Tuple[List[Deficiency], float]:
        """
        Check clinical text for terminology issues.

        Parameters
        ----------
        text : str
            Preprocessed clinical text.

        Returns
        -------
        tuple of (list of Deficiency, float)
            Terminology deficiencies and a standardization score (0-100).
        """
        deficiencies = []
        issues_found = 0
        total_checks = 0

        # Check for unexpanded abbreviations
        if self.flag_abbreviations:
            abbrev_issues = self._check_abbreviations(text)
            deficiencies.extend(abbrev_issues)
            issues_found += len(abbrev_issues)
            total_checks += len(self.abbreviation_dict)

        # Check for non-standard terminology
        if self.flag_unmapped:
            term_issues = self._check_nonstandard_terms(text)
            deficiencies.extend(term_issues)
            issues_found += len(term_issues)
            total_checks += len(TERMINOLOGY_CORRECTIONS)

        # Check for dangerous abbreviations
        dangerous_issues = self._check_dangerous_abbreviations(text)
        deficiencies.extend(dangerous_issues)
        issues_found += len(dangerous_issues)

        # Calculate terminology score
        if total_checks > 0:
            score = max(0.0, 100.0 - (issues_found / max(total_checks, 1) * 100 * 5))
        else:
            score = 100.0

        return deficiencies, min(score, 100.0)

    def _check_abbreviations(self, text: str) -> List[Deficiency]:
        """Check for unexpanded medical abbreviations."""
        deficiencies = []
        found_abbrevs: Set[str] = set()

        for abbrev, expansion in self.abbreviation_dict.items():
            pattern = r"\b" + re.escape(abbrev) + r"\b"
            matches = re.finditer(pattern, text)

            for match in matches:
                if abbrev not in found_abbrevs:
                    found_abbrevs.add(abbrev)
                    # Check if expansion is NOT present nearby
                    context_start = max(0, match.start() - 100)
                    context_end = min(len(text), match.end() + 100)
                    context = text[context_start:context_end]

                    if expansion.lower() not in context.lower():
                        deficiencies.append(Deficiency(
                            category="Terminology",
                            severity="LOW",
                            description=(
                                f"Non-standard abbreviation '{abbrev}' used without "
                                f"expansion — recommend using '{expansion}' or "
                                f"corresponding ICD-10 code."
                            ),
                            text_span=context.strip(),
                            start_pos=match.start(),
                            end_pos=match.end(),
                            recommended_action=(
                                f"Expand '{abbrev}' to '{expansion}' on first use, "
                                f"or use the standardized diagnostic terminology "
                                f"per facility documentation policy."
                            ),
                        ))

        return deficiencies

    def _check_nonstandard_terms(self, text: str) -> List[Deficiency]:
        """Check for non-standard lay terminology in clinical notes."""
        deficiencies = []
        text_lower = text.lower()

        for nonstandard, standard in TERMINOLOGY_CORRECTIONS.items():
            if nonstandard in text_lower:
                deficiencies.append(Deficiency(
                    category="Terminology",
                    severity="MEDIUM",
                    description=(
                        f"Non-standard term '{nonstandard}' detected — "
                        f"recommend standardized terminology: '{standard}'."
                    ),
                    recommended_action=(
                        f"Replace '{nonstandard}' with '{standard}' for "
                        f"accurate clinical coding and interoperability."
                    ),
                ))

        return deficiencies

    def _check_dangerous_abbreviations(self, text: str) -> List[Deficiency]:
        """
        Check for abbreviations on the ISMP/Joint Commission
        'Do Not Use' list.
        """
        dangerous = {
            r"\bU\b": ("U", "units", "Can be mistaken for 0, 4, or cc"),
            r"\bIU\b": ("IU", "international units", "Can be mistaken for IV or 10"),
            r"\bQD\b": ("QD", "daily", "Can be mistaken for QID"),
            r"\bQOD\b": ("QOD", "every other day", "Can be mistaken for QD or QID"),
            r"\bMS\b": ("MS", "morphine sulfate or magnesium sulfate",
                        "Ambiguous — can refer to either medication"),
            r"\bMSO4\b": ("MSO4", "morphine sulfate", "Can be confused with MgSO4"),
            r"\bMgSO4\b": ("MgSO4", "magnesium sulfate", "Can be confused with MSO4"),
        }

        deficiencies = []
        for pattern, (abbrev, replacement, reason) in dangerous.items():
            if re.search(pattern, text):
                deficiencies.append(Deficiency(
                    category="Terminology",
                    severity="HIGH",
                    description=(
                        f"Dangerous abbreviation '{abbrev}' detected — "
                        f"on ISMP 'Do Not Use' list. {reason}."
                    ),
                    recommended_action=(
                        f"Replace '{abbrev}' with '{replacement}' per "
                        f"Joint Commission and ISMP safety standards."
                    ),
                ))

        return deficiencies
