"""
ClinicalDocAnalyzer — Main entry point for clinical documentation analysis.

Orchestrates the multi-module NLP pipeline for detecting documentation
deficiencies in clinical notes from long-term care facilities, community
health centers, and Critical Access Hospitals.

Author: Michael Kwakye Agyapong
"""

import yaml
import json
import os
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from .preprocessor import ClinicalTextPreprocessor
from .copy_paste_detector import CopyPasteDetector
from .completeness_scorer import CompletenessScorer
from .terminology_checker import TerminologyChecker
from .coherence_analyzer import CoherenceAnalyzer
from .deidentifier import Deidentifier
from .report_generator import ReportGenerator


@dataclass
class Deficiency:
    """Represents a single documentation deficiency detected by the analyzer."""
    category: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    text_span: Optional[str] = None
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None
    recommended_action: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "severity": self.severity,
            "description": self.description,
            "text_span": self.text_span,
            "recommended_action": self.recommended_action,
        }


@dataclass
class AnalysisReport:
    """Contains the complete results of a documentation quality analysis."""
    note_type: str
    analysis_date: str
    quality_score: float
    dimension_scores: Dict[str, float]
    deficiencies: List[Deficiency]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        lines = [
            "=" * 60,
            "CLINICAL DOCUMENTATION QUALITY REPORT",
            "=" * 60,
            f"Note Type: {self.note_type}",
            f"Date Analyzed: {self.analysis_date}",
            f"Quality Score: {self.quality_score:.0f}/100",
            "",
            "DIMENSION SCORES:",
        ]
        for dim, score in self.dimension_scores.items():
            lines.append(f"  {dim}: {score:.0f}/100")

        lines.append(f"\nDEFICIENCIES DETECTED: {len(self.deficiencies)}\n")

        for d in self.deficiencies:
            lines.append(f"[{d.severity}] {d.category}: {d.description}")
            if d.recommended_action:
                lines.append(f"  -> Action: {d.recommended_action}")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "note_type": self.note_type,
            "analysis_date": self.analysis_date,
            "quality_score": self.quality_score,
            "dimension_scores": self.dimension_scores,
            "deficiencies": [d.to_dict() for d in self.deficiencies],
            "metadata": self.metadata,
        }


class ClinicalDocAnalyzer:
    """
    Main analyzer class that orchestrates the clinical documentation
    quality analysis pipeline.

    The pipeline processes clinical notes through multiple modules:
    1. Text Preprocessing & De-identification
    2. Copy-Paste Detection
    3. Completeness Scoring
    4. Terminology Checking
    5. Coherence Analysis

    Each module produces deficiency findings and dimension scores that
    are aggregated into a composite quality report.

    Parameters
    ----------
    config_path : str, optional
        Path to the YAML configuration file.
        Defaults to 'config/settings.yaml'.

    Example
    -------
    >>> analyzer = ClinicalDocAnalyzer()
    >>> report = analyzer.analyze(note_text, note_type="progress_note")
    >>> print(report.summary())
    """

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "config", "settings.yaml"
            )

        self.config = self._load_config(config_path)

        # Initialize pipeline modules
        self.preprocessor = ClinicalTextPreprocessor(self.config)
        self.deidentifier = Deidentifier(self.config)
        self.copy_paste_detector = CopyPasteDetector(self.config)
        self.completeness_scorer = CompletenessScorer(self.config)
        self.terminology_checker = TerminologyChecker(self.config)
        self.coherence_analyzer = CoherenceAnalyzer(self.config)
        self.report_generator = ReportGenerator(self.config)

        # Note history for cross-note analysis (copy-paste detection)
        self.note_history: List[Dict[str, Any]] = []

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Config not found at {config_path}, using defaults.")
            return self._default_config()

    def _default_config(self) -> dict:
        """Return default configuration values."""
        return {
            "copy_paste": {
                "similarity_threshold": 0.85,
                "min_text_length": 50,
                "lookback_window": 10,
            },
            "completeness": {
                "required_sections": {
                    "progress_note": ["subjective", "objective", "assessment", "plan"],
                    "nursing_assessment": ["vitals", "pain_assessment",
                                           "functional_status", "care_plan"],
                },
                "min_section_words": 5,
            },
            "terminology": {
                "flag_abbreviations": True,
                "flag_unmapped_terms": True,
            },
            "coherence": {
                "assessment_plan_threshold": 0.3,
                "check_dx_med_consistency": True,
            },
            "scoring": {
                "weights": {
                    "completeness": 0.30,
                    "copy_paste_free": 0.20,
                    "terminology": 0.15,
                    "coherence": 0.20,
                    "temporal": 0.15,
                }
            },
            "deidentification": {
                "enabled": True,
                "method": "safe_harbor",
                "replacement_format": "[{entity_type}]",
            },
        }

    def analyze(
        self,
        note_text: str,
        note_type: str = "progress_note",
        patient_id: Optional[str] = None,
        encounter_date: Optional[str] = None,
        prior_notes: Optional[List[str]] = None,
    ) -> AnalysisReport:
        """
        Analyze a clinical note for documentation deficiencies.

        Parameters
        ----------
        note_text : str
            The raw clinical note text to analyze.
        note_type : str
            Type of clinical note (progress_note, nursing_assessment,
            discharge_summary, admission_assessment).
        patient_id : str, optional
            De-identified patient identifier for cross-note analysis.
        encounter_date : str, optional
            Date of the clinical encounter (YYYY-MM-DD format).
        prior_notes : list of str, optional
            List of prior note texts for copy-paste comparison.

        Returns
        -------
        AnalysisReport
            Comprehensive documentation quality analysis results.
        """
        all_deficiencies = []
        dimension_scores = {}

        # Step 1: Preprocess text
        processed_text = self.preprocessor.process(note_text)

        # Step 2: De-identify if enabled
        if self.config.get("deidentification", {}).get("enabled", True):
            processed_text = self.deidentifier.deidentify(processed_text)

        # Step 3: Parse note into sections
        sections = self.preprocessor.extract_sections(processed_text, note_type)

        # Step 4: Copy-paste detection
        comparison_notes = prior_notes or [n["text"] for n in self.note_history[-10:]]
        cp_deficiencies, cp_score = self.copy_paste_detector.detect(
            processed_text, comparison_notes
        )
        all_deficiencies.extend(cp_deficiencies)
        dimension_scores["copy_paste_free"] = cp_score

        # Step 5: Completeness scoring
        comp_deficiencies, comp_score = self.completeness_scorer.score(
            sections, note_type
        )
        all_deficiencies.extend(comp_deficiencies)
        dimension_scores["completeness"] = comp_score

        # Step 6: Terminology checking
        term_deficiencies, term_score = self.terminology_checker.check(
            processed_text
        )
        all_deficiencies.extend(term_deficiencies)
        dimension_scores["terminology"] = term_score

        # Step 7: Coherence analysis
        coh_deficiencies, coh_score = self.coherence_analyzer.analyze(
            sections, note_type
        )
        all_deficiencies.extend(coh_deficiencies)
        dimension_scores["coherence"] = coh_score

        # Step 8: Temporal consistency (basic implementation)
        dimension_scores["temporal"] = 100.0  # Default if no temporal issues

        # Step 9: Calculate composite quality score
        weights = self.config.get("scoring", {}).get("weights", {})
        quality_score = sum(
            dimension_scores.get(dim, 100.0) * weight
            for dim, weight in weights.items()
        )

        # Update note history for future cross-note analysis
        self.note_history.append({
            "text": processed_text,
            "note_type": note_type,
            "patient_id": patient_id,
            "date": encounter_date or datetime.now().strftime("%Y-%m-%d"),
        })

        return AnalysisReport(
            note_type=note_type,
            analysis_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            quality_score=quality_score,
            dimension_scores=dimension_scores,
            deficiencies=all_deficiencies,
            metadata={
                "patient_id": patient_id,
                "encounter_date": encounter_date,
                "word_count": len(processed_text.split()),
                "section_count": len(sections),
            },
        )

    def analyze_batch(
        self,
        notes: List[Dict[str, Any]],
        output_format: str = "json",
    ) -> List[AnalysisReport]:
        """
        Analyze a batch of clinical notes.

        Parameters
        ----------
        notes : list of dict
            Each dict should contain 'text', 'note_type', and optionally
            'patient_id' and 'encounter_date'.
        output_format : str
            Output format for batch report ('json', 'csv', 'html').

        Returns
        -------
        list of AnalysisReport
            Analysis results for each note.
        """
        reports = []
        for i, note_data in enumerate(notes):
            print(f"Analyzing note {i + 1}/{len(notes)}...")
            report = self.analyze(
                note_text=note_data["text"],
                note_type=note_data.get("note_type", "progress_note"),
                patient_id=note_data.get("patient_id"),
                encounter_date=note_data.get("encounter_date"),
            )
            reports.append(report)

        # Generate batch summary
        avg_score = sum(r.quality_score for r in reports) / len(reports) if reports else 0
        total_deficiencies = sum(len(r.deficiencies) for r in reports)

        print(f"\n{'=' * 60}")
        print(f"BATCH ANALYSIS COMPLETE")
        print(f"Notes Analyzed: {len(reports)}")
        print(f"Average Quality Score: {avg_score:.1f}/100")
        print(f"Total Deficiencies Found: {total_deficiencies}")
        print(f"{'=' * 60}")

        return reports

    def export_report(self, report: AnalysisReport, output_path: str,
                      format: str = "json") -> str:
        """Export an analysis report to file."""
        return self.report_generator.generate(report, output_path, format)
