"""
Example: Analyze a single clinical note for documentation deficiencies.

This script demonstrates the basic usage of the ClinicalDocAnalyzer
to evaluate a progress note from a long-term care facility.

Author: Michael Kwakye Agyapong
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.analyzer import ClinicalDocAnalyzer


def main():
    # Initialize the analyzer
    analyzer = ClinicalDocAnalyzer()

    # Sample progress note from a long-term care facility
    note = """
    Subjective: Resident states she is feeling "okay today." Reports
    mild pain in right knee, 3/10 on numeric scale. Appetite fair,
    ate 50% of breakfast. Slept well last night per night shift report.

    Objective: BP 142/88, HR 76, Temp 98.2F, RR 18, SpO2 96% on RA.
    Alert and oriented x3 (person, place, time). Ambulates with
    rolling walker, requires standby assist. Right knee mildly swollen,
    no warmth or erythema. Skin intact, no new areas of breakdown.
    Bowel sounds active, abdomen soft.

    Assessment: 1. Hypertension - slightly elevated today, monitor
    trending. 2. Osteoarthritis right knee - chronic, mild flare.
    3. Fall risk - moderate per Morse Fall Scale score 55.
    4. Diabetes mellitus type 2 - last HbA1c 7.1%, at near-goal.

    Plan: 1. Continue lisinopril 10mg daily, recheck BP this evening.
    If sustained >140 systolic, notify provider for dose adjustment.
    2. Acetaminophen 650mg PO Q6H PRN for knee pain. Ice pack to
    right knee 20 min TID. 3. Continue fall precautions, bed alarm
    on at night. PT to evaluate gait stability. 4. Diabetic diet,
    fingerstick AC and HS. Continue metformin 500mg BID.
    """

    # Analyze the note
    report = analyzer.analyze(
        note_text=note,
        note_type="progress_note",
        patient_id="RES-2024-0142",
        encounter_date="2025-03-15",
    )

    # Print the summary report
    print(report.summary())

    # Export to JSON
    output_path = analyzer.export_report(
        report, "output/reports/sample_report.json", format="json"
    )
    print(f"\nReport exported to: {output_path}")

    # Export to HTML
    html_path = analyzer.export_report(
        report, "output/reports/sample_report.html", format="html"
    )
    print(f"HTML report exported to: {html_path}")


if __name__ == "__main__":
    main()
