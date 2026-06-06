# Cognitive Decline

**Domain:** Aging
**Status:** scaffold
**Prediction type:** Trajectory prediction for cognitive aging, including risk of mild cognitive impairment (MCI) and dementia (Alzheimer's disease and other types).

## What This Predicts

- 5- and 10-year probability of developing mild cognitive impairment
- Probability of MCI converting to dementia within 5 years
- Estimated cognitive trajectory (stable aging vs. accelerated decline)
- Modifiable risk factor impact on decline trajectory

## Why This Matters

Alzheimer's disease affects 1 in 9 people over 65. The pathological process begins 15–20 years before symptoms. Lifestyle interventions (physical activity, sleep, cognitive engagement, vascular risk management) have meaningful impact — but only if started early enough.

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Age | self-report | yes |
| MoCA or MMSE score | assessment | yes (for those 60+) |
| Cardiovascular risk factors (hypertension, diabetes, cholesterol) | self-report | yes |
| Physical activity | self-report | yes |
| Sleep quality / hours | self-report | yes |
| Social engagement | self-report | yes |
| Educational attainment | self-report | yes |
| Hearing loss status | self-report | optional |
| Depression history | self-report | optional |
| APOE4 genetic status | genetic test | optional |
| Family history of dementia | self-report | yes |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| MCI probability (5 years) | percentage | |
| Dementia probability (10 years) | percentage | |
| Cognitive trajectory | time series | expected score decline |
| Modifiable risk score | 0.0–1.0 | proportion of risk that is addressable |
| Protective factor recommendations | ranked list | highest impact first |

## Data Sources

- ADNI (Alzheimer's Disease Neuroimaging Initiative)
- WHICAP (Washington Heights-Inwood Columbia Aging Project)
- Health and Retirement Study (HRS)
- FINGER trial data (lifestyle intervention outcomes)
- UK Biobank (cognitive aging phenotypes)
- CAIDE Dementia Risk Score validation data

## Self-Correction

- **Accuracy metric:** AUC for MCI and dementia onset prediction; calibration in held-out cohorts
- **Ground truth:** longitudinal cognitive assessment outcomes in HRS, ADNI cohorts
- **Retraining trigger:** AUC < 0.72 for 5-year MCI prediction

## Refresh Frequency

- Annual after age 60
- Semi-annual after age 70 or MCI diagnosis

## Ethical Considerations

- Cognitive decline predictions are among the most distressing a person can receive — must be delivered with counseling and support resources
- Right not to know must be explicitly honored — this must be fully opt-in
- Predictions must emphasize the large proportion of risk that is modifiable
- Must not be used in employment, insurance, or legal competency decisions
- APOE4 status disclosure has family implications and psychological impact — specialized counseling support required
