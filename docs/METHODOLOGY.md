# Methodology

## Overview

The Clinical Documentation NLP Analyzer employs a multi-module pipeline architecture to detect documentation deficiencies in clinical notes from Electronic Health Records. The pipeline is designed for deployment in long-term care facilities, community health centers, and Critical Access Hospitals — institutions that collectively serve over 77 million Americans but systematically lack access to advanced clinical informatics tools.

## Pipeline Architecture

The analyzer processes each clinical note through five sequential modules:

### Module 1: Text Preprocessing and De-identification

**Purpose:** Normalize raw clinical text and remove protected health information (PHI).

**Methods:**
- Whitespace normalization and formatting artifact removal
- Sentence segmentation tuned for clinical text patterns
- Medical abbreviation expansion using a configurable dictionary
- HIPAA Safe Harbor de-identification using pattern-based PHI detection
- Clinical note section extraction using regex-based header matching

**Implementation:** `src/preprocessor.py`, `src/deidentifier.py`

### Module 2: Copy-Paste Detection

**Purpose:** Identify text blocks duplicated from prior encounters without clinical review.

**Methods:**
- Jaccard similarity coefficient for word-level overlap measurement
- N-gram (trigram) overlap for phrase-level duplication detection
- Combined weighted similarity score (60% Jaccard + 40% n-gram)
- Configurable similarity threshold (default: 0.85)
- Paragraph-level granularity for precise deficiency localization

**Scientific Basis:** Copy-paste propagation has been documented as one of the most prevalent sources of documentation error in EHR systems. Studies have found that up to 82% of clinical notes in some settings contain copied content, with significant implications for data accuracy and patient safety.

**Implementation:** `src/copy_paste_detector.py`

### Module 3: Completeness Scoring

**Purpose:** Verify the presence of required documentation elements for each note type.

**Methods:**
- Section detection using clinical header pattern matching
- Word count-based adequacy assessment per section
- Note-type-specific required section definitions (configurable)
- Severity classification based on section clinical importance

**Section Requirements by Note Type:**
- Progress Notes (SOAP): Subjective, Objective, Assessment, Plan
- Nursing Assessments: Vitals, Pain, Functional Status, Skin, Nutrition, Care Plan
- Discharge Summaries: Admission Dx, Hospital Course, Discharge Dx, Medications, Follow-up
- Admission Assessments: CC, HPI, PMH, Medications, Allergies, Exam, Assessment, Plan

**Implementation:** `src/completeness_scorer.py`

### Module 4: Terminology Checking

**Purpose:** Flag non-standard clinical terminology that impedes accurate coding.

**Methods:**
- Abbreviation detection against a medical abbreviation dictionary (70+ entries)
- Non-standard lay terminology identification with standard equivalents
- ISMP/Joint Commission "Do Not Use" dangerous abbreviation checking
- Contextual verification (checks if abbreviation is already expanded nearby)

**Implementation:** `src/terminology_checker.py`

### Module 5: Coherence Analysis

**Purpose:** Assess narrative consistency between clinical documentation sections.

**Methods:**
- Assessment-Plan term overlap analysis for treatment plan completeness
- Objective-Assessment consistency checking against clinical indicator dictionaries
- Unsupported assertion detection (e.g., "stable" without supporting data)
- Clinical term extraction with domain-specific stop word removal

**Implementation:** `src/coherence_analyzer.py`

## Scoring Methodology

### Composite Quality Score

Each module produces a dimension score on a 0-100 scale. The composite quality score is a weighted average:

| Dimension | Weight |
|-----------|--------|
| Completeness | 30% |
| Copy-Paste Free | 20% |
| Terminology | 15% |
| Coherence | 20% |
| Temporal Consistency | 15% |

### Severity Classification

Detected deficiencies are classified into four severity levels:
- **CRITICAL:** Poses immediate risk to patient safety or regulatory compliance
- **HIGH:** Significant documentation gap affecting coding accuracy or care quality
- **MEDIUM:** Notable deficiency that should be addressed but does not pose immediate risk
- **LOW:** Minor issue or best-practice recommendation

## Design Principles

1. **Open-Source Implementation:** All components use freely available Python libraries (NLTK, SpaCy, Scikit-learn). No proprietary software or licensing fees.

2. **Modular Architecture:** Facilities can deploy individual modules based on their technical capacity and documentation priorities.

3. **EHR-Agnostic:** Processes standard clinical text exports (CSV, TXT, JSON) regardless of source EHR system.

4. **Interpretable Output:** Every detected deficiency includes a human-readable explanation and recommended corrective action.

5. **Configurable Parameters:** All detection thresholds, required sections, and scoring weights are adjustable via YAML configuration.

## Evaluation Metrics

Framework performance is evaluated using:
- **Precision:** Proportion of detected deficiencies that are true deficiencies
- **Recall (Sensitivity):** Proportion of actual deficiencies that are detected
- **F1-Score:** Harmonic mean of precision and recall
- **False Positive Rate:** Proportion of flagged items that are not actual deficiencies

## References

- Davis, J. & Shepheard, J. (2024). Clinical documentation integrity. *Health Information Management Journal*, 53(1), 3-14.
- AHRQ. (2024). Challenges and opportunities for improvement in diagnostic documentation.
- Woo, B.F.Y. et al. (2025). The use of large language models in clinical documentation. *Int. J. Nursing Studies*, 176, 105322.
- Koleck, T.A. et al. (2024). NLP applied to clinical documentation in post-acute care. *JAMIA*, 31(2), 467-479.
