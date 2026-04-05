"""
Example: Batch analysis of multiple clinical notes.

Demonstrates processing a collection of clinical notes from a CSV
export, analyzing each for documentation deficiencies, and generating
a summary report suitable for quality improvement review.

Author: Michael Kwakye Agyapong
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.analyzer import ClinicalDocAnalyzer


# Sample notes simulating a CSV export from an LTC EHR system
SAMPLE_NOTES = [
    {
        "patient_id": "RES-001",
        "encounter_date": "2025-03-10",
        "note_type": "progress_note",
        "text": """
        Subjective: Patient reports no complaints today.
        Objective: Vitals stable. WNL.
        Assessment: Stable.
        Plan: Continue current medications. Follow up PRN.
        """,
    },
    {
        "patient_id": "RES-002",
        "encounter_date": "2025-03-10",
        "note_type": "progress_note",
        "text": """
        Assessment: CHF exacerbation, fluid overload suspected.
        Plan: Increase Lasix, restrict fluids to 1500ml/day, daily weights,
        recheck BMP in AM, notify MD if weight gain >2lbs.
        """,
    },
    {
        "patient_id": "RES-003",
        "encounter_date": "2025-03-10",
        "note_type": "nursing_assessment",
        "text": """
        Vital Signs: BP 118/72, HR 68, Temp 97.8F, RR 16, SpO2 99%.
        Pain Assessment: Denies pain, 0/10 on numeric scale.
        Functional Status: Independent with ADLs. Ambulates independently
        without assistive device. Transfers independently.
        Skin Integrity: Skin warm, dry, intact. No areas of redness or
        breakdown noted. Braden Scale score: 20 (low risk).
        Nutrition: Good appetite, ate 100% of meals today. Weight stable
        at 145 lbs. BMI 24.2.
        Care Plan: Continue current plan of care. Fall risk low. Continue
        to monitor skin integrity per protocol. Encourage ambulation.
        """,
    },
    {
        "patient_id": "RES-004",
        "encounter_date": "2025-03-11",
        "note_type": "progress_note",
        "text": """
        Patient seen today. No changes. Stable. Continue meds.
        """,
    },
]


def main():
    analyzer = ClinicalDocAnalyzer()

    print("=" * 60)
    print("BATCH CLINICAL DOCUMENTATION ANALYSIS")
    print("Facility: Sample Long-Term Care Facility")
    print(f"Notes to Analyze: {len(SAMPLE_NOTES)}")
    print("=" * 60)
    print()

    reports = analyzer.analyze_batch(SAMPLE_NOTES)

    # Generate facility-level summary
    total_deficiencies = sum(len(r.deficiencies) for r in reports)
    avg_score = sum(r.quality_score for r in reports) / len(reports)
    severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "CRITICAL": 0}

    for report in reports:
        for d in report.deficiencies:
            severity_counts[d.severity] = severity_counts.get(d.severity, 0) + 1

    # Category breakdown
    category_counts = {}
    for report in reports:
        for d in report.deficiencies:
            category_counts[d.category] = category_counts.get(d.category, 0) + 1

    print("\n" + "=" * 60)
    print("FACILITY-LEVEL SUMMARY")
    print("=" * 60)
    print(f"Average Quality Score: {avg_score:.1f}/100")
    print(f"Total Deficiencies: {total_deficiencies}")
    print(f"\nBy Severity:")
    for sev, count in sorted(severity_counts.items()):
        if count > 0:
            print(f"  {sev}: {count}")
    print(f"\nBy Category:")
    for cat, count in sorted(category_counts.items()):
        print(f"  {cat}: {count}")

    # Individual note scores
    print(f"\nIndividual Note Scores:")
    for i, report in enumerate(reports):
        patient = SAMPLE_NOTES[i]["patient_id"]
        print(f"  {patient}: {report.quality_score:.0f}/100 "
              f"({len(report.deficiencies)} deficiencies)")

    # Export batch results
    os.makedirs("output/reports", exist_ok=True)
    batch_results = {
        "facility_summary": {
            "average_quality_score": avg_score,
            "total_notes_analyzed": len(reports),
            "total_deficiencies": total_deficiencies,
            "severity_breakdown": severity_counts,
            "category_breakdown": category_counts,
        },
        "individual_reports": [r.to_dict() for r in reports],
    }

    with open("output/reports/batch_summary.json", "w") as f:
        json.dump(batch_results, f, indent=2, default=str)

    print(f"\nBatch report exported to: output/reports/batch_summary.json")


if __name__ == "__main__":
    main()
