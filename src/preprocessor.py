"""
ClinicalTextPreprocessor — Text preprocessing and section extraction
for clinical documentation analysis.

Handles tokenization, sentence segmentation, abbreviation expansion,
and note section parsing for common clinical note types used in
long-term care, community health centers, and Critical Access Hospitals.

Author: Michael Kwakye Agyapong
"""

import re
import json
import os
from typing import Dict, List, Optional, Tuple


# Section header patterns for clinical note types
SECTION_PATTERNS = {
    "subjective": r"(?i)\b(subjective|s:|hpi|history of present illness|chief complaint|cc:?)\b",
    "objective": r"(?i)\b(objective|o:|physical exam|pe:|vital signs|vitals|exam|labs|results)\b",
    "assessment": r"(?i)\b(assessment|a:|impression|diagnosis|dx:?|diagnos[ei]s)\b",
    "plan": r"(?i)\b(plan|p:|treatment plan|orders|recommendations|disposition)\b",
    "vitals": r"(?i)\b(vital signs|vitals|vs:?|bp|hr|rr|temp|spo2|o2 sat)\b",
    "pain_assessment": r"(?i)\b(pain|pain assessment|pain scale|pain level|pain score)\b",
    "functional_status": r"(?i)\b(functional status|adl|activities of daily living|mobility|ambulation|transfer)\b",
    "skin_integrity": r"(?i)\b(skin|skin integrity|wound|pressure|ulcer|skin assessment|integumentary)\b",
    "nutrition": r"(?i)\b(nutrition|diet|dietary|intake|appetite|weight|bmi|nutritional)\b",
    "care_plan": r"(?i)\b(care plan|goals|interventions|nursing plan|plan of care)\b",
    "admission_diagnosis": r"(?i)\b(admission diagnosis|admitting diagnosis|reason for admission)\b",
    "hospital_course": r"(?i)\b(hospital course|clinical course|course of treatment|summary of stay)\b",
    "discharge_diagnosis": r"(?i)\b(discharge diagnosis|final diagnosis|diagnosis at discharge)\b",
    "discharge_medications": r"(?i)\b(discharge medications|medications at discharge|med list|discharge meds)\b",
    "follow_up_instructions": r"(?i)\b(follow.?up|follow up instructions|discharge instructions|appointments)\b",
    "chief_complaint": r"(?i)\b(chief complaint|cc:?|reason for visit|presenting complaint)\b",
    "history_of_present_illness": r"(?i)\b(history of present illness|hpi|present illness)\b",
    "past_medical_history": r"(?i)\b(past medical history|pmh|medical history|pmhx)\b",
    "medications": r"(?i)\b(medications|current medications|med list|medication list|meds)\b",
    "allergies": r"(?i)\b(allergies|allergy|drug allergies|nkda|nka|adverse reactions)\b",
    "physical_exam": r"(?i)\b(physical exam|pe:?|examination|exam findings|physical examination)\b",
}


class ClinicalTextPreprocessor:
    """
    Preprocesses clinical text for downstream NLP analysis.

    Handles:
    - Text normalization and cleaning
    - Sentence segmentation
    - Tokenization
    - Medical abbreviation expansion
    - Clinical note section extraction

    Parameters
    ----------
    config : dict
        Configuration dictionary from settings.yaml.
    """

    def __init__(self, config: dict):
        self.config = config
        self.abbreviation_dict = self._load_abbreviations()

    def _load_abbreviations(self) -> Dict[str, str]:
        """Load medical abbreviation dictionary."""
        abbrev_path = self.config.get("terminology", {}).get(
            "abbreviation_dict",
            os.path.join(os.path.dirname(os.path.dirname(__file__)),
                         "config", "medical_abbreviations.json")
        )
        try:
            with open(abbrev_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def process(self, text: str) -> str:
        """
        Apply full preprocessing pipeline to clinical text.

        Parameters
        ----------
        text : str
            Raw clinical note text.

        Returns
        -------
        str
            Preprocessed clinical text.
        """
        text = self._normalize_whitespace(text)
        text = self._normalize_line_endings(text)
        text = self._clean_formatting_artifacts(text)
        return text.strip()

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize excessive whitespace while preserving paragraph breaks."""
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    def _normalize_line_endings(self, text: str) -> str:
        """Normalize line endings to Unix format."""
        return text.replace("\r\n", "\n").replace("\r", "\n")

    def _clean_formatting_artifacts(self, text: str) -> str:
        """Remove common EHR formatting artifacts."""
        # Remove repeated separator characters
        text = re.sub(r"[-=_]{5,}", "", text)
        # Remove common EHR template markers
        text = re.sub(r"\*{3,}", "", text)
        # Remove empty parentheses and brackets from templates
        text = re.sub(r"\(\s*\)", "", text)
        text = re.sub(r"\[\s*\]", "", text)
        return text

    def segment_sentences(self, text: str) -> List[str]:
        """
        Segment clinical text into sentences.

        Uses rule-based approach tuned for clinical text, which
        contains patterns (e.g., abbreviations with periods) that
        confuse general-purpose sentence segmenters.

        Parameters
        ----------
        text : str
            Preprocessed clinical text.

        Returns
        -------
        list of str
            Individual sentences.
        """
        # Protect common abbreviations from sentence splitting
        protected = text
        for abbrev in self.abbreviation_dict:
            if "." in abbrev:
                protected = protected.replace(abbrev, abbrev.replace(".", "<DOT>"))

        # Split on sentence boundaries
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", protected)

        # Restore protected dots
        sentences = [s.replace("<DOT>", ".").strip() for s in sentences]
        return [s for s in sentences if s]

    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize clinical text into words.

        Parameters
        ----------
        text : str
            Input text.

        Returns
        -------
        list of str
            Tokens.
        """
        tokens = re.findall(r"\b\w+(?:[-']\w+)*\b", text)
        return tokens

    def expand_abbreviations(self, text: str) -> str:
        """
        Expand known medical abbreviations in clinical text.

        Parameters
        ----------
        text : str
            Clinical text with abbreviations.

        Returns
        -------
        str
            Text with abbreviations expanded.
        """
        for abbrev, expansion in self.abbreviation_dict.items():
            pattern = r"\b" + re.escape(abbrev) + r"\b"
            text = re.sub(pattern, f"{abbrev} ({expansion})", text, count=1)
        return text

    def extract_sections(self, text: str, note_type: str) -> Dict[str, str]:
        """
        Extract named sections from a clinical note.

        Identifies section boundaries using pattern matching against
        known clinical section headers, then extracts the text content
        of each section.

        Parameters
        ----------
        text : str
            Preprocessed clinical note text.
        note_type : str
            Type of clinical note (determines expected sections).

        Returns
        -------
        dict
            Mapping of section names to section text content.
        """
        required = self.config.get("completeness", {}).get(
            "required_sections", {}
        ).get(note_type, [])

        # Find all section header positions
        section_positions: List[Tuple[str, int]] = []
        for section_name in required:
            pattern = SECTION_PATTERNS.get(section_name)
            if pattern:
                match = re.search(pattern, text)
                if match:
                    section_positions.append((section_name, match.start()))

        # Sort by position
        section_positions.sort(key=lambda x: x[1])

        # Extract section text
        sections = {}
        for i, (name, start) in enumerate(section_positions):
            if i + 1 < len(section_positions):
                end = section_positions[i + 1][1]
            else:
                end = len(text)
            sections[name] = text[start:end].strip()

        # Mark missing sections
        for section_name in required:
            if section_name not in sections:
                sections[section_name] = ""

        return sections

    def get_word_count(self, text: str) -> int:
        """Return word count of text."""
        return len(self.tokenize(text))

    def get_char_count(self, text: str) -> int:
        """Return character count of text (excluding whitespace)."""
        return len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
