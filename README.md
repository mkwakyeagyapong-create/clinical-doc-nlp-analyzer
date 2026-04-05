# Clinical Documentation NLP Analyzer

An open-access Natural Language Processing toolkit for detecting clinical documentation deficiencies in Electronic Health Records (EHR), with a focus on long-term care facilities, community health centers, and Critical Access Hospitals.

## Overview

Clinical documentation integrity is the foundation of patient safety, accurate billing, regulatory compliance, and public health surveillance. Yet healthcare facilities serving underserved populations, including long-term care facilities, Federally Qualified Health Centers (FQHCs), and Critical Access Hospitals (CAHs), systematically lack access to advanced clinical informatics tools for documentation quality improvement.

This toolkit provides an open-access, deployable NLP pipeline that automatically detects documentation deficiencies in clinical notes, including:

- **Copy-paste detection** — Identifies duplicated text blocks propagated across encounters
- **Completeness scoring** — Verifies presence of required documentation elements (chief complaint, assessment, plan, etc.)
- **Terminology standardization** — Flags non-standard diagnostic language and unmapped clinical terms
- **Narrative coherence analysis** — Assesses semantic consistency between assessment, diagnosis, and care plan sections
- **Temporal consistency checking** — Detects date/time conflicts and anachronistic documentation entries

## Key Features

- Built entirely on open-source tools (Python, NLTK, SpaCy, Scikit-learn)
- Designed for resource-constrained healthcare settings with minimal IT infrastructure
- EHR-agnostic: processes standard clinical text exports (CSV, TXT, JSON, HL7 CDA)
- Modular architecture — deploy individual modules based on facility needs
- Interpretable output with human-readable deficiency reports
- HIPAA-compliant de-identification module included

## Installation

```bash
git clone https://github.com/mkagyapong/clinical-doc-nlp-analyzer.git
cd clinical-doc-nlp-analyzer
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Quick Start

```python
from src.analyzer import ClinicalDocAnalyzer

analyzer = ClinicalDocAnalyzer()

# Analyze a single clinical note
note = """
Patient is a 78-year-old female with history of CHF and diabetes.
Assessment: Patient stable. Continue current medications.
Plan: Follow up in 2 weeks.
"""

report = analyzer.analyze(note, note_type="progress_note")
print(report.summary())
print(f"Quality Score: {report.quality_score}/100")
print(f"Deficiencies Found: {len(report.deficiencies)}")

for deficiency in report.deficiencies:
    print(f"  [{deficiency.severity}] {deficiency.category}: {deficiency.description}")
```

## Modules

### 1. Text Preprocessor (`src/preprocessor.py`)
Normalizes clinical text through tokenization, sentence segmentation, abbreviation expansion, and HIPAA-compliant de-identification.

### 2. Copy-Paste Detector (`src/copy_paste_detector.py`)
Identifies duplicated text blocks across encounters using Jaccard similarity with configurable thresholds.

### 3. Completeness Scorer (`src/completeness_scorer.py`)
Evaluates clinical notes against required documentation elements for each note type (progress notes, assessments, discharge summaries).

### 4. Terminology Checker (`src/terminology_checker.py`)
Flags non-standard clinical terminology and maps clinical terms to SNOMED CT and ICD-10-CM concepts.

### 5. Coherence Analyzer (`src/coherence_analyzer.py`)
Assesses narrative consistency between documentation sections using NLP-based semantic similarity.

### 6. Report Generator (`src/report_generator.py`)
Produces structured quality reports in HTML, JSON, and CSV formats.

## Configuration

Customize detection parameters in `config/settings.yaml`:

```yaml
copy_paste:
  similarity_threshold: 0.85
  min_text_length: 50

completeness:
  required_sections:
    progress_note: ["subjective", "objective", "assessment", "plan"]
    nursing_assessment: ["vitals", "pain_assessment", "functional_status", "care_plan"]

terminology:
  flag_abbreviations: true
  abbreviation_dict: "config/medical_abbreviations.json"
```

## Example Output

```
============================================================
CLINICAL DOCUMENTATION QUALITY REPORT
============================================================
Note Type: Progress Note
Date Analyzed: 2025-03-15
Quality Score: 62/100

DEFICIENCIES DETECTED: 4

[HIGH] Completeness: Missing 'Objective' section — no vitals,
       exam findings, or lab results documented.

[MEDIUM] Copy-Paste: 87% similarity detected with note from
         2025-03-08 — possible carried-forward content without
         clinical update.

[MEDIUM] Terminology: Non-standard abbreviation 'CHF' used
         without expansion — recommend 'Congestive Heart Failure'
         or ICD-10 code I50.9.

[LOW] Coherence: Assessment states 'stable' but no objective
      data supports this determination.

RECOMMENDED ACTIONS:
1. Add objective findings (vitals, physical exam, labs)
2. Review and update carried-forward text
3. Expand clinical abbreviations per facility policy
============================================================
```

## Target Healthcare Settings

This toolkit is specifically designed for:

- **Long-Term Care Facilities** — Skilled nursing facilities, nursing homes
- **Community Health Centers** — Federally Qualified Health Centers (FQHCs)
- **Critical Access Hospitals** — Rural hospitals with ≤25 inpatient beds

These institutions collectively serve over 77 million Americans and systematically lack access to commercial clinical NLP tools.

## Project Structure

```
clinical-doc-nlp-analyzer/
├── README.md
├── LICENSE
├── requirements.txt
├── setup.py
├── .gitignore
├── config/
│   ├── settings.yaml
│   └── medical_abbreviations.json
├── src/
│   ├── __init__.py
│   ├── analyzer.py
│   ├── preprocessor.py
│   ├── copy_paste_detector.py
│   ├── completeness_scorer.py
│   ├── terminology_checker.py
│   ├── coherence_analyzer.py
│   ├── deidentifier.py
│   └── report_generator.py
├── tests/
│   ├── __init__.py
│   ├── test_preprocessor.py
│   └── test_analyzer.py
├── examples/
│   ├── analyze_single_note.py
│   └── batch_analysis.py
└── docs/
    └── METHODOLOGY.md
```

## Research Context

This project is part of an applied research program developing open-access NLP frameworks for clinical documentation quality improvement in underserved U.S. healthcare facilities. Related publications:

1. Agyapong, M. K. "Improving Clinical Documentation Accuracy in Long-Term Care Facilities Using NLP: A Predictive Analytics Framework for EHR Data Integrity." *Journal of Healthcare Informatics Research* (Manuscript in Development).

2. Agyapong, M. K. "Impact of Natural Language Processing on Clinical Documentation Quality: Evidence from the United States of America." *ResearchGate* (Under Review).

## License

MIT License — See [LICENSE](LICENSE) for details.

## Author

**Michael Kwakye Agyapong**
Healthcare Data Analytics | NLP | Clinical Informatics
Tiffin University, Tiffin, Ohio
Email: mkwakyeagyapong@gmail.com

## Citation

If you use this toolkit in your research, please cite:

```bibtex
@software{agyapong2025clinicaldocnlp,
  author = {Agyapong, Michael Kwakye},
  title = {Clinical Documentation NLP Analyzer},
  year = {2025},
  url = {https://github.com/mkagyapong/clinical-doc-nlp-analyzer}
}
```
