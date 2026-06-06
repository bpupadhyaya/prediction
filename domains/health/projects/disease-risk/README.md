# Disease Risk

**Domain:** Health
**Status:** scaffold
**Prediction type:** Probability of developing major diseases within defined time windows, based on lifestyle, demographics, biomarkers, and (optionally) genetic data.

## What This Predicts

Personalized risk scores for major disease categories including cardiovascular disease, type 2 diabetes, cancer (by type), chronic kidney disease, and chronic respiratory disease. Outputs a probability of developing each condition within a 5- and 10-year window. Works with lifestyle and demographic data alone; genetic data improves accuracy when available.

## Why This Matters

Cardiovascular disease and diabetes alone account for over 20 million deaths annually and are highly preventable with early lifestyle intervention. Most people never receive a systematic risk assessment.

## Target Diseases (Initial)

- Cardiovascular disease (heart attack, stroke)
- Type 2 diabetes
- Colorectal cancer
- Breast cancer (separate model)
- Chronic obstructive pulmonary disease (COPD)
- Chronic kidney disease

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Age, sex | self-report | yes |
| Smoking status | self-report | yes |
| BMI | self-report | yes |
| Blood pressure | self-report or device | yes |
| Physical activity | self-report | yes |
| Family history | self-report | optional |
| Cholesterol (total/HDL) | lab report | optional |
| Blood glucose / HbA1c | lab report | optional |
| Genetic risk scores | genetic test | optional |

## Output

| Output | Type | Range |
|--------|------|-------|
| Risk score per disease | float | 0.0–1.0 |
| 5-year probability | percentage | 0–100% |
| 10-year probability | percentage | 0–100% |
| Risk tier | categorical | low/medium/high/very high |
| Modifiable risk factors | list | ranked by impact |

## Data Sources

- UK Biobank — validated outcome data for model training
- NHANES (National Health and Nutrition Examination Survey) — US population representative
- Framingham Heart Study data — cardiovascular baseline
- ACCORD / UKPDS trial data — diabetes prediction

## Research

See [research/](research/) — comparison of existing tools: Framingham Risk Score, QRISK3, AHA/ACC Pooled Cohort Equations, SCORE2 (European).

## Self-Correction

- **Accuracy metric:** AUC-ROC, calibration error (Brier score)
- **Ground truth:** longitudinal outcome tracking in validation cohort; ICD code matching
- **Retraining trigger:** AUC < 0.75 or calibration error > 0.05
- **Accuracy log:** `development/accuracy_log.json`

## Refresh Frequency

- Lifestyle-based inputs: quarterly, or on significant lifestyle change
- Biomarker inputs: on new lab results
- Model retraining: annually or on accuracy trigger

## Ethical Considerations

- Predictions are risk estimates, not diagnoses — must be communicated clearly
- Results should recommend clinical follow-up, not replace it
- Training data must be demographically diverse — current clinical risk tools are often poorly calibrated for non-European populations
- Avoid creating anxiety without actionable guidance

## Status Log

| Date | Status | Notes |
|------|--------|-------|
| 2026-06-06 | scaffold | initial setup |
