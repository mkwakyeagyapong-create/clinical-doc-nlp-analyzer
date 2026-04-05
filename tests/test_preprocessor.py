"""
Tests for ClinicalTextPreprocessor module.

Author: Michael Kwakye Agyapong
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.preprocessor import ClinicalTextPreprocessor


class TestClinicalTextPreprocessor(unittest.TestCase):
    """Test cases for clinical text preprocessing."""

    def setUp(self):
        self.config = {
            "terminology": {"abbreviation_dict": "config/medical_abbreviations.json"},
            "completeness": {
                "required_sections": {
                    "progress_note": ["subjective", "objective", "assessment", "plan"],
                },
                "min_section_words": 5,
            },
        }
        self.preprocessor = ClinicalTextPreprocessor(self.config)

    def test_normalize_whitespace(self):
        text = "Patient   has    multiple   spaces"
        result = self.preprocessor._normalize_whitespace(text)
        self.assertNotIn("   ", result)

    def test_normalize_line_endings(self):
        text = "Line 1\r\nLine 2\rLine 3"
        result = self.preprocessor._normalize_line_endings(text)
        self.assertNotIn("\r", result)
        self.assertEqual(result.count("\n"), 2)

    def test_clean_formatting_artifacts(self):
        text = "Header\n==========\nContent\n***\nMore content"
        result = self.preprocessor._clean_formatting_artifacts(text)
        self.assertNotIn("==========", result)
        self.assertNotIn("***", result)

    def test_process_full_pipeline(self):
        text = "  Patient   is a   78 y/o female.\r\n\r\n\r\n\r\nAssessment:  stable.  "
        result = self.preprocessor.process(text)
        self.assertFalse(result.startswith(" "))
        self.assertFalse(result.endswith(" "))
        self.assertNotIn("\r", result)

    def test_tokenize(self):
        text = "Patient has CHF and diabetes mellitus type 2."
        tokens = self.preprocessor.tokenize(text)
        self.assertIn("Patient", tokens)
        self.assertIn("CHF", tokens)
        self.assertIn("diabetes", tokens)

    def test_word_count(self):
        text = "This is a five word sentence."
        count = self.preprocessor.get_word_count(text)
        self.assertEqual(count, 6)

    def test_extract_sections_soap_note(self):
        text = """
        Subjective: Patient reports feeling tired and short of breath.
        Objective: BP 140/90, HR 88, SpO2 94% on room air.
        Assessment: Exacerbation of CHF, possible fluid overload.
        Plan: Increase Lasix to 40mg BID, restrict fluids, recheck BMP tomorrow.
        """
        sections = self.preprocessor.extract_sections(text, "progress_note")
        self.assertIn("subjective", sections)
        self.assertIn("objective", sections)
        self.assertIn("assessment", sections)
        self.assertIn("plan", sections)

    def test_extract_sections_missing(self):
        text = """
        Assessment: Patient is stable.
        Plan: Continue current medications.
        """
        sections = self.preprocessor.extract_sections(text, "progress_note")
        self.assertEqual(sections.get("subjective", ""), "")
        self.assertEqual(sections.get("objective", ""), "")

    def test_segment_sentences(self):
        text = "Patient has CHF. Blood pressure is elevated. Will increase diuretics."
        sentences = self.preprocessor.segment_sentences(text)
        self.assertEqual(len(sentences), 3)

    def test_empty_input(self):
        result = self.preprocessor.process("")
        self.assertEqual(result, "")

    def test_special_characters(self):
        text = "Temp: 98.6°F, BP: 120/80 mmHg, O2 Sat: 98%"
        result = self.preprocessor.process(text)
        self.assertIn("98.6", result)
        self.assertIn("120/80", result)


class TestSectionExtraction(unittest.TestCase):
    """Test section extraction for different note types."""

    def setUp(self):
        self.config = {
            "terminology": {},
            "completeness": {
                "required_sections": {
                    "progress_note": ["subjective", "objective", "assessment", "plan"],
                    "nursing_assessment": ["vitals", "pain_assessment",
                                           "functional_status", "care_plan"],
                },
                "min_section_words": 5,
            },
        }
        self.preprocessor = ClinicalTextPreprocessor(self.config)

    def test_nursing_assessment_sections(self):
        text = """
        Vital Signs: BP 130/85, HR 72, Temp 98.4F, RR 18, SpO2 97%.
        Pain Assessment: Patient reports pain level 3/10 in lower back.
        Functional Status: Patient requires moderate assist with transfers.
        ADL assistance needed for bathing and dressing.
        Care Plan: Continue pain management protocol. Physical therapy
        3x weekly. Monitor vitals q shift.
        """
        sections = self.preprocessor.extract_sections(text, "nursing_assessment")
        self.assertIn("vitals", sections)
        self.assertIn("pain_assessment", sections)
        self.assertIn("functional_status", sections)
        self.assertIn("care_plan", sections)


if __name__ == "__main__":
    unittest.main()
