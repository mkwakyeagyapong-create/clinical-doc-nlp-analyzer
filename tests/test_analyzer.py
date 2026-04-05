"""
Tests for ClinicalDocAnalyzer main module.

Author: Michael Kwakye Agyapong
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.analyzer import ClinicalDocAnalyzer, Deficiency, AnalysisReport


class TestDeficiency(unittest.TestCase):
    """Test Deficiency data class."""

    def test_deficiency_creation(self):
        d = Deficiency(
            category="Completeness",
            severity="HIGH",
            description="Missing objective section",
            recommended_action="Add vitals and exam findings",
        )
        self.assertEqual(d.category, "Completeness")
        self.assertEqual(d.severity, "HIGH")

    def test_deficiency_to_dict(self):
        d = Deficiency(
            category="Copy-Paste",
            severity="MEDIUM",
            description="90% similarity with prior note",
        )
        result = d.to_dict()
        self.assertIsInstance(result, dict)
        self.assertEqual(result["category"], "Copy-Paste")
        self.assertIn("severity", result)


class TestAnalysisReport(unittest.TestCase):
    """Test AnalysisReport data class."""

    def test_report_summary(self):
        report = AnalysisReport(
            note_type="progress_note",
            analysis_date="2025-03-15 10:00:00",
            quality_score=75.0,
            dimension_scores={"completeness": 80.0, "coherence": 70.0},
            deficiencies=[
                Deficiency(
                    category="Completeness",
                    severity="HIGH",
                    description="Missing objective section",
                ),
            ],
        )
        summary = report.summary()
        self.assertIn("QUALITY REPORT", summary)
        self.assertIn("75", summary)
        self.assertIn("Missing objective", summary)

    def test_report_to_dict(self):
        report = AnalysisReport(
            note_type="nursing_assessment",
            analysis_date="2025-03-15",
            quality_score=90.0,
            dimension_scores={"completeness": 100.0},
            deficiencies=[],
        )
        result = report.to_dict()
        self.assertEqual(result["quality_score"], 90.0)
        self.assertEqual(len(result["deficiencies"]), 0)


class TestClinicalDocAnalyzer(unittest.TestCase):
    """Test the main ClinicalDocAnalyzer pipeline."""

    def setUp(self):
        self.analyzer = ClinicalDocAnalyzer()

    def test_analyze_complete_soap_note(self):
        note = """
        Subjective: Patient reports feeling well today. No new complaints.
        Appetite is good. Sleeping well at night. Denies pain.

        Objective: BP 128/78, HR 72, Temp 98.4F, RR 16, SpO2 98%.
        Alert and oriented x4. Lungs clear bilaterally. Heart regular
        rate and rhythm. Abdomen soft, non-tender. Skin intact.
        BMP within normal limits. Hemoglobin 12.5.

        Assessment: Hypertension, well-controlled on current regimen.
        Diabetes mellitus type 2, HbA1c 6.8% at goal. Chronic kidney
        disease stage 3, stable creatinine at 1.4.

        Plan: Continue lisinopril 20mg daily. Continue metformin 1000mg
        BID. Recheck BMP and HbA1c in 3 months. Follow up in 4 weeks.
        """
        report = self.analyzer.analyze(note, note_type="progress_note")
        self.assertIsInstance(report, AnalysisReport)
        self.assertGreater(report.quality_score, 0)
        self.assertIn("completeness", report.dimension_scores)

    def test_analyze_incomplete_note(self):
        note = """
        Assessment: Patient stable. Continue current medications.
        Plan: Follow up in 2 weeks.
        """
        report = self.analyzer.analyze(note, note_type="progress_note")
        self.assertIsInstance(report, AnalysisReport)
        # Should detect missing subjective and objective sections
        comp_deficiencies = [
            d for d in report.deficiencies if d.category == "Completeness"
        ]
        self.assertGreater(len(comp_deficiencies), 0)

    def test_analyze_with_copy_paste(self):
        note1 = "Patient is a 78-year-old female with history of CHF " * 10
        note2 = "Patient is a 78-year-old female with history of CHF " * 10
        report = self.analyzer.analyze(
            note2, note_type="progress_note", prior_notes=[note1]
        )
        cp_deficiencies = [
            d for d in report.deficiencies if d.category == "Copy-Paste"
        ]
        self.assertGreater(len(cp_deficiencies), 0)

    def test_analyze_with_metadata(self):
        note = "Assessment: Stable. Plan: Continue meds."
        report = self.analyzer.analyze(
            note,
            note_type="progress_note",
            patient_id="TEST001",
            encounter_date="2025-03-15",
        )
        self.assertEqual(report.metadata["patient_id"], "TEST001")
        self.assertEqual(report.metadata["encounter_date"], "2025-03-15")

    def test_batch_analysis(self):
        notes = [
            {"text": "Assessment: Stable. Plan: Continue.", "note_type": "progress_note"},
            {"text": "Assessment: Improving. Plan: Discharge planning.", "note_type": "progress_note"},
        ]
        reports = self.analyzer.analyze_batch(notes)
        self.assertEqual(len(reports), 2)

    def test_quality_score_range(self):
        note = "Some brief clinical text."
        report = self.analyzer.analyze(note, note_type="progress_note")
        self.assertGreaterEqual(report.quality_score, 0)
        self.assertLessEqual(report.quality_score, 100)

    def test_empty_note(self):
        report = self.analyzer.analyze("", note_type="progress_note")
        self.assertIsInstance(report, AnalysisReport)
        self.assertEqual(report.metadata["word_count"], 0)


if __name__ == "__main__":
    unittest.main()
