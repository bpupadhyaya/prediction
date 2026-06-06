# Mobility Loss

**Domain:** Aging
**Status:** scaffold
**Prediction type:** Physical mobility decline trajectory and fall risk prediction for older adults, to enable preventive intervention and home safety planning.

## What This Predicts

- Annual fall risk probability
- 3- and 5-year trajectory of physical mobility decline
- Expected timeline to mobility aid requirement (cane, walker, wheelchair)
- Probability of fall-related hospitalization
- Impact of specific interventions (exercise, home modification) on trajectory

## Why This Matters

Falls are the leading cause of injury death in adults over 65. One-third of adults over 65 fall annually; 20% of falls result in serious injury. Fall risk is highly predictable and highly preventable.

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Age | self-report | yes |
| Timed Up and Go (TUG) test result | self-assessment | yes |
| Prior fall history (12 months) | self-report | yes |
| Gait speed | self-assessment | yes |
| Balance assessment | self-assessment | yes |
| Medications (especially sedatives, antihypertensives) | self-report | yes |
| Vision status | self-report | yes |
| Home hazard assessment | self-report | optional |
| Physical activity level | self-report | yes |
| Grip strength | self-assessment | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Annual fall probability | percentage | |
| Mobility trajectory (3/5 years) | time series | expected function level |
| Fall risk tier | low/moderate/high/very high | |
| Home hazard priority list | ranked list | most dangerous modifiable factors |
| Exercise prescription type | categorical | balance/strength/combined |

## Data Sources

- STEADI (CDC Stopping Elderly Accidents, Deaths & Injuries) data
- NHATS (National Health and Aging Trends Study)
- Health and Retirement Study (HRS)
- Published TUG and gait speed normative data
- Exercise intervention (OTAGO, Tai Chi) clinical trial data

## Self-Correction

- **Accuracy metric:** Sensitivity/specificity for fall prediction; calibration of annual probability
- **Ground truth:** self-reported and clinical fall records; HRS longitudinal data
- **Retraining trigger:** AUC < 0.72 for fall prediction

## Refresh Frequency

- Quarterly for high-risk individuals
- Semi-annually for moderate risk
- Annually for low risk
- Immediately after any fall

## Ethical Considerations

- Predictions must be paired with specific, accessible interventions (many are low-cost or free)
- Must not be used to prematurely remove independence or driving privileges
- Home modification recommendations must acknowledge financial barriers
- Predictions must be available in low-literacy formats
