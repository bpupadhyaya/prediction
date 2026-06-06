# Health Domain — Development

## Purpose

This folder contains shared development artifacts for the health domain: common data pipelines, feature engineering utilities, evaluation frameworks, and integration specifications that projects within this domain can reuse.

## Shared Components (Planned)

### Data Pipelines
- `pipelines/fhir_ingestion/` — FHIR-compliant health record ingestion
- `pipelines/genetic_data/` — SNP array and genome data processing
- `pipelines/survey_data/` — BRFSS, NHANES survey data processing
- `pipelines/clinical_trial/` — ClinicalTrials.gov data integration

### Feature Engineering
- `features/lifestyle/` — diet, exercise, sleep, smoking feature extraction
- `features/demographics/` — age, sex, ethnicity normalization
- `features/biomarkers/` — lab value normalization and reference ranges
- `features/genetic/` — polygenic risk score computation

### Evaluation Framework
- `evaluation/calibration.py` — Brier score, calibration curves
- `evaluation/discrimination.py` — AUC-ROC, sensitivity/specificity
- `evaluation/fairness.py` — demographic parity, equalized odds
- `evaluation/accuracy_tracker.py` — longitudinal accuracy tracking

### APIs
- `api/risk_score/` — standard interface for project-level risk scores
- `api/confidence/` — confidence interval serialization standard
- `api/feedback/` — ground truth feedback loop API

## Development Standards

All health domain code must:
- Handle missing data explicitly (health data is almost always incomplete)
- Report predictions with confidence intervals
- Include demographic breakdown in accuracy reporting
- Comply with relevant health data privacy standards (HIPAA in US, GDPR in EU)
- Never store or log raw health data — only derived features

## Status

| Component | Status |
|-----------|--------|
| FHIR ingestion pipeline | planned |
| Genetic data processing | planned |
| Survey data pipeline | planned |
| Feature engineering library | planned |
| Evaluation framework | planned |
| Risk score API | planned |

## Getting Started

*Development has not yet begun. If you want to start a component, open an issue describing your approach and check for existing work.*
