"""
CompletenessScorer — Evaluates clinical note completeness against
required documentation elements.

Verifies the presence and adequacy of required sections for each
clinical note type, configured for documentation standards in
long-term care, community health, and critical access hospital settings.

Author: Michael Kwakye Agyapong
"""

from typing import Dict, List, Tuple
from .analyzer import Deficiency


SECTION_DESCRIPTIONS = {
    "subjective": "Subjective findings (patient-reported symptoms, complaints, history)",
    "objective": "Objective findings (vitals, physical exam, lab results)",
    "assessment": "Clinical assessment (diagnosis, clinical impression)",
    "plan": "Treatment plan (orders, interventions, follow-up)",
    "vitals": "Vital signs documentation",
    "pain_assessment": "Pain assessment and scoring",
    "functional_status": "Functional status and ADL assessment",
    "skin_integrity": "Skin integrity and wound assessment",
    "nutrition": "Nutritional status assessment",
    "care_plan": "Care plan with goals and interventions",
    "admission_diagnosis": "Admission diagnosis",
    "hospital_course": "Hospital course summary",
    "discharge_diagnosis": "Discharge diagnosis",
    "discharge_medications": "Discharge medication list",
    "follow_up_instructions": "Follow-up instructions and appointments",
    "chief_complaint": "Chief complaint or reason for visit",
    "history_of_present_illness": "History of present illness",
    "past_medical_history": "Past medical history",
    "medications": "Current medication list",
    "allergies": "Allergy documentation",
    "physical_exam": "Physical examination findings",
}


class CompletenessScorer:
    """
    Evaluates the completeness of clinical documentation by checking
    for the presence of required sections and minimum content adequacy.

    Parameters
    ----------
    config : dict
        Configuration dictionary with completeness settings.
    """

    def __init__(self, config: dict):
        comp_config = config.get("completeness", {})
        self.required_sections = comp_config.get("required_sections", {})
        self.min_section_words = comp_config.get("min_section_words", 5)

    def score(
        self,
        sections: Dict[str, str],
        note_type: str,
    ) -> Tuple[List[Deficiency], float]:
        """
        Score the completeness of a clinical note.

        Parameters
        ----------
        sections : dict
            Mapping of section names to their text content.
        note_type : str
            Type of clinical note being evaluated.

        Returns
        -------
        tuple of (list of Deficiency, float)
            Detected completeness deficiencies and a score (0-100).
        """
        deficiencies = []
        required = self.required_sections.get(note_type, [])

        if not required:
            return deficiencies, 100.0

        present_count = 0
        total_required = len(required)

        for section_name in required:
            section_text = sections.get(section_name, "")
            word_count = len(section_text.split()) if section_text else 0

            if not section_text or word_count < self.min_section_words:
                description = SECTION_DESCRIPTIONS.get(
                    section_name,
                    f"Required section: {section_name}"
                )
                severity = self._classify_severity(section_name, note_type)

                deficiencies.append(Deficiency(
                    category="Completeness",
                    severity=severity,
                    description=(
                        f"Missing or insufficient '{section_name}' section — "
                        f"{description} not adequately documented."
                    ),
                    recommended_action=(
                        f"Add {description.lower()} to this {note_type}. "
                        f"Minimum documentation should include specific clinical "
                        f"findings, not just template placeholders."
                    ),
                ))
            else:
                present_count += 1

                # Check for template-only content (very short sections)
                if word_count < self.min_section_words * 2:
                    deficiencies.append(Deficiency(
                        category="Completeness",
                        severity="LOW",
                        description=(
                            f"Section '{section_name}' appears minimally documented "
                            f"({word_count} words) — may not provide sufficient "
                            f"clinical detail."
                        ),
                        recommended_action=(
                            f"Consider expanding documentation in the "
                            f"{section_name} section with additional clinical detail."
                        ),
                    ))

        # Calculate completeness score
        score = (present_count / total_required * 100) if total_required > 0 else 100.0
        return deficiencies, score

    def _classify_severity(self, section_name: str, note_type: str) -> str:
        """Classify severity based on section importance."""
        critical_sections = {
            "progress_note": ["assessment", "plan"],
            "nursing_assessment": ["vitals", "care_plan"],
            "discharge_summary": ["discharge_diagnosis", "discharge_medications"],
            "admission_assessment": ["chief_complaint", "assessment", "plan"],
        }

        critical = critical_sections.get(note_type, [])
        if section_name in critical:
            return "HIGH"
        return "MEDIUM"
