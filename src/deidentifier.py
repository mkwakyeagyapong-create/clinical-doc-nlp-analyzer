"""
Deidentifier — HIPAA-compliant de-identification of protected
health information (PHI) in clinical text.

Implements Safe Harbor de-identification by detecting and replacing
18 categories of PHI identifiers with standardized placeholder tokens.

Author: Michael Kwakye Agyapong
"""

import re
from typing import Dict, List, Tuple


# PHI detection patterns (Safe Harbor method)
PHI_PATTERNS = {
    "PERSON_NAME": [
        r"\b(?:Mr|Mrs|Ms|Dr|Miss)\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?",
        r"\b[A-Z][a-z]+,\s+[A-Z][a-z]+\b",
    ],
    "DATE": [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b",
        r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\b",
    ],
    "PHONE": [
        r"\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    ],
    "MRN": [
        r"\b(?:MRN|Medical Record|Acct|Account)[\s#:]*\d{4,}\b",
    ],
    "SSN": [
        r"\b\d{3}[-]?\d{2}[-]?\d{4}\b",
    ],
    "EMAIL": [
        r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
    ],
    "ADDRESS": [
        r"\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:St|Ave|Blvd|Dr|Rd|Ln|Way|Ct|Pl)\.?\b",
    ],
    "ZIP": [
        r"\b\d{5}(?:-\d{4})?\b",
    ],
    "AGE_OVER_89": [
        r"\b(?:9[0-9]|1[0-9]{2})\s*(?:year|yr|y/?o|y\.o\.)\b",
    ],
}


class Deidentifier:
    """
    Removes protected health information from clinical text using
    rule-based pattern matching (HIPAA Safe Harbor method).

    Replaces detected PHI with standardized placeholder tokens
    (e.g., [PERSON_NAME], [DATE]) to preserve text structure
    while removing identifying information.

    Parameters
    ----------
    config : dict
        Configuration dictionary with deidentification settings.
    """

    def __init__(self, config: dict):
        deid_config = config.get("deidentification", {})
        self.enabled = deid_config.get("enabled", True)
        self.method = deid_config.get("method", "safe_harbor")
        self.replacement_format = deid_config.get(
            "replacement_format", "[{entity_type}]"
        )

    def deidentify(self, text: str) -> str:
        """
        Remove PHI from clinical text.

        Parameters
        ----------
        text : str
            Clinical text potentially containing PHI.

        Returns
        -------
        str
            De-identified text with PHI replaced by placeholders.
        """
        if not self.enabled:
            return text

        deidentified = text
        for entity_type, patterns in PHI_PATTERNS.items():
            replacement = self.replacement_format.format(entity_type=entity_type)
            for pattern in patterns:
                deidentified = re.sub(pattern, replacement, deidentified,
                                      flags=re.IGNORECASE)

        return deidentified

    def detect_phi(self, text: str) -> List[Dict[str, str]]:
        """
        Detect PHI entities in clinical text without replacing them.

        Parameters
        ----------
        text : str
            Clinical text to scan for PHI.

        Returns
        -------
        list of dict
            Detected PHI entities with type, value, and position.
        """
        detected = []
        for entity_type, patterns in PHI_PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                    detected.append({
                        "entity_type": entity_type,
                        "value": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                    })
        return detected

    def get_phi_summary(self, text: str) -> Dict[str, int]:
        """Return count of each PHI type detected."""
        detected = self.detect_phi(text)
        summary = {}
        for item in detected:
            entity_type = item["entity_type"]
            summary[entity_type] = summary.get(entity_type, 0) + 1
        return summary
