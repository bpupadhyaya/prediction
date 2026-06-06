# Accident Risk

**Domain:** Safety & Environment
**Status:** scaffold
**Prediction type:** Personal risk prediction for accidents across home, road, workplace, and recreational contexts.

## What This Predicts

- Annual probability of accident by type (fall, vehicle, workplace, recreational)
- Most significant personal risk factors for accidents
- Probability of accident-related hospitalization
- Impact of behavioral changes on risk reduction

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Age | self-report | yes |
| Occupation type | self-report | yes |
| Driving frequency and habits | self-report | yes |
| Home type (stairs, bathtub, etc.) | self-report | yes |
| Physical activity level | self-report | yes |
| Balance / mobility (for fall risk, older adults) | assessment | optional |
| Vision and hearing status | self-report | optional |
| Medication use (affects alertness) | self-report | optional |
| Prior accident history | self-report | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Annual accident probability (by type) | percentage | |
| Top risk factors | ranked list | modifiable factors first |
| Fall risk score (age 65+) | low/medium/high | |
| Intervention recommendations | list | highest-impact risk reductions |

## Data Sources

- CDC Injury Facts (WISQARS)
- BLS Census of Fatal Occupational Injuries (CFOI)
- NHTSA crash statistics
- NEISS (National Electronic Injury Surveillance System)
- CDC Fall Prevention data
- OSHA workplace injury statistics

## Self-Correction

- **Accuracy metric:** Calibration of annual probability vs. population rates by demographic
- **Ground truth:** aggregate accident rates in validation cohorts
- **Retraining trigger:** probability calibration error > 0.05

## Refresh Frequency

- Annual review
- Reassessment on age milestone, occupation change, or new medication

## Ethical Considerations

- Accident predictions must lead to actionable safety guidance, not just risk labeling
- Workplace risk must not be used by employers to discriminate
- Fall risk predictions for elderly individuals are particularly sensitive — frame supportively
