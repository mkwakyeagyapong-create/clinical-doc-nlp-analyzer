"""
CoherenceAnalyzer — Assesses narrative coherence and semantic
consistency between clinical documentation sections.

Evaluates whether assessment findings are consistent with the
documented plan, whether diagnoses are supported by objective
findings, and whether the clinical narrative demonstrates
appropriate reasoning.

Author: Michael Kwakye Agyapong
"""

import re
from typing import Dict, List, Tuple
from collections import Counter
from .analyzer import Deficiency


# Clinical indicators that should appear in objective section
# if mentioned in assessment
OBJECTIVE_INDICATORS = {
    "hypertension": ["bp", "blood pressure", "systolic", "diastolic", "mmhg"],
    "diabetes": ["glucose", "blood sugar", "hba1c", "a1c", "fingerstick"],
    "infection": ["wbc", "temperature", "temp", "fever", "culture", "white blood cell"],
    "anemia": ["hgb", "hemoglobin", "hct", "hematocrit", "cbc"],
    "renal": ["bun", "creatinine", "cr", "gfr", "kidney"],
    "pain": ["pain scale", "pain score", "pain level", "numeric rating"],
    "respiratory": ["spo2", "oxygen", "respiratory rate", "rr", "breath sounds"],
    "cardiac": ["heart rate", "hr", "rhythm", "ekg", "ecg", "cardiac"],
    "dehydration": ["intake", "output", "i&o", "fluid", "skin turgor"],
    "fall": ["fall risk", "morse", "tinetti", "balance", "gait"],
}


class CoherenceAnalyzer:
    """
    Analyzes the narrative coherence of clinical documentation.

    Evaluates semantic consistency between note sections, checks
    whether clinical assertions are supported by documented evidence,
    and identifies logical gaps in the clinical reasoning chain.

    Parameters
    ----------
    config : dict
        Configuration dictionary with coherence settings.
    """

    def __init__(self, config: dict):
        coh_config = config.get("coherence", {})
        self.threshold = coh_config.get("assessment_plan_threshold", 0.3)
        self.check_dx_med = coh_config.get("check_dx_med_consistency", True)

    def analyze(
        self,
        sections: Dict[str, str],
        note_type: str,
    ) -> Tuple[List[Deficiency], float]:
        """
        Analyze narrative coherence of clinical documentation.

        Parameters
        ----------
        sections : dict
            Mapping of section names to their text content.
        note_type : str
            Type of clinical note.

        Returns
        -------
        tuple of (list of Deficiency, float)
            Coherence deficiencies and a score (0-100).
        """
        deficiencies = []
        coherence_scores = []

        # Check assessment-plan consistency
        if "assessment" in sections and "plan" in sections:
            ap_deficiencies, ap_score = self._check_assessment_plan(
                sections.get("assessment", ""),
                sections.get("plan", "")
            )
            deficiencies.extend(ap_deficiencies)
            coherence_scores.append(ap_score)

        # Check objective-assessment consistency
        if "objective" in sections and "assessment" in sections:
            oa_deficiencies, oa_score = self._check_objective_assessment(
                sections.get("objective", ""),
                sections.get("assessment", "")
            )
            deficiencies.extend(oa_deficiencies)
            coherence_scores.append(oa_score)

        # Check for unsupported assertions
        assertion_deficiencies = self._check_unsupported_assertions(sections)
        deficiencies.extend(assertion_deficiencies)
        if assertion_deficiencies:
            coherence_scores.append(max(0, 100 - len(assertion_deficiencies) * 15))
        else:
            coherence_scores.append(100.0)

        # Calculate overall coherence score
        score = sum(coherence_scores) / len(coherence_scores) if coherence_scores else 100.0
        return deficiencies, score

    def _check_assessment_plan(
        self,
        assessment: str,
        plan: str,
    ) -> Tuple[List[Deficiency], float]:
        """Check semantic consistency between assessment and plan."""
        deficiencies = []

        if not assessment.strip() or not plan.strip():
            return deficiencies, 50.0

        # Extract key clinical terms from assessment
        assessment_terms = self._extract_clinical_terms(assessment)
        plan_terms = self._extract_clinical_terms(plan)

        if not assessment_terms:
            return deficiencies, 75.0

        # Calculate term overlap
        overlap = assessment_terms & plan_terms
        coverage = len(overlap) / len(assessment_terms) if assessment_terms else 0

        if coverage < self.threshold:
            deficiencies.append(Deficiency(
                category="Coherence",
                severity="MEDIUM",
                description=(
                    f"Low consistency between Assessment and Plan sections "
                    f"({coverage * 100:.0f}% term overlap). Conditions identified "
                    f"in assessment may not be addressed in the plan."
                ),
                recommended_action=(
                    "Ensure that each condition or finding documented in the "
                    "assessment has a corresponding intervention, order, or "
                    "follow-up action in the plan section."
                ),
            ))

        score = min(100.0, coverage * 100 * 2)  # Scale to 0-100
        return deficiencies, score

    def _check_objective_assessment(
        self,
        objective: str,
        assessment: str,
    ) -> Tuple[List[Deficiency], float]:
        """Check that assessment findings are supported by objective data."""
        deficiencies = []
        objective_lower = objective.lower()
        assessment_lower = assessment.lower()
        unsupported_count = 0

        for condition, indicators in OBJECTIVE_INDICATORS.items():
            # Check if condition is mentioned in assessment
            if condition in assessment_lower:
                # Check if supporting data exists in objective section
                has_support = any(ind in objective_lower for ind in indicators)
                if not has_support:
                    unsupported_count += 1
                    deficiencies.append(Deficiency(
                        category="Coherence",
                        severity="MEDIUM",
                        description=(
                            f"Assessment references '{condition}' but no "
                            f"supporting objective data (e.g., "
                            f"{', '.join(indicators[:3])}) found in the "
                            f"Objective section."
                        ),
                        recommended_action=(
                            f"Add objective findings supporting the "
                            f"'{condition}' assessment, including relevant "
                            f"vital signs, lab values, or exam findings."
                        ),
                    ))

        total_conditions = sum(
            1 for c in OBJECTIVE_INDICATORS if c in assessment_lower
        )
        if total_conditions > 0:
            score = max(0, 100 - (unsupported_count / total_conditions * 100))
        else:
            score = 100.0

        return deficiencies, score

    def _check_unsupported_assertions(
        self, sections: Dict[str, str]
    ) -> List[Deficiency]:
        """Check for common unsupported clinical assertions."""
        deficiencies = []
        full_text = " ".join(sections.values()).lower()

        # Patterns indicating assertions without supporting evidence
        unsupported_patterns = [
            (r"\bstable\b", "objective",
             "Assessment states 'stable' but no objective data supports "
             "this determination"),
            (r"\bimproving\b", "objective",
             "Documentation states 'improving' but no comparison data "
             "or trend analysis provided"),
            (r"\bunchanged\b", "objective",
             "Documentation states 'unchanged' without specifying what "
             "parameters were assessed"),
            (r"\bwithin normal limits\b", "objective",
             "States 'within normal limits' without specifying which "
             "values were assessed"),
            (r"\btolerat(?:ing|ed) well\b", "objective",
             "States medication/treatment 'tolerated well' without "
             "specifying monitored parameters"),
        ]

        for pattern, expected_section, message in unsupported_patterns:
            if re.search(pattern, full_text):
                expected_text = sections.get(expected_section, "")
                # Only flag if the supporting section is sparse
                if len(expected_text.split()) < 20:
                    deficiencies.append(Deficiency(
                        category="Coherence",
                        severity="LOW",
                        description=message,
                        recommended_action=(
                            "Provide specific objective data to support "
                            "clinical assertions. Document specific values, "
                            "measurements, or observations."
                        ),
                    ))

        return deficiencies

    def _extract_clinical_terms(self, text: str) -> set:
        """Extract clinically significant terms from text."""
        text_lower = text.lower()
        # Remove common stop words and non-clinical terms
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "shall", "can",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "as", "into", "through", "during", "before", "after", "above",
            "below", "between", "this", "that", "these", "those", "and",
            "but", "or", "nor", "not", "no", "so", "if", "then", "than",
            "too", "very", "just", "about", "also", "patient", "resident",
            "continue", "continued", "per", "note", "see", "noted",
        }
        words = set(re.findall(r"\b[a-z]{3,}\b", text_lower))
        return words - stop_words
