# Academic Performance

**Domain:** Education
**Status:** scaffold
**Prediction type:** Future academic performance trajectory — grades, graduation probability, and learning velocity — based on current performance patterns, learning style, and environmental factors.

## What This Predicts

- Expected grade trajectory for the next 1–3 academic terms
- Graduation probability (high school, college) within expected timeline
- Subjects where the student is at risk of falling behind
- Intervention windows where support has highest expected impact

## Why This Matters

Early academic struggles compound over time. A student falling behind in 3rd grade math is statistically likely to struggle in secondary school. Prediction enables targeted intervention before the deficit becomes entrenched.

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Current grades by subject | school records / self-report | yes |
| Attendance rate | school records / self-report | yes |
| Age / grade level | self-report | yes |
| Time spent on homework | self-report | optional |
| Teacher-reported engagement | school records | optional |
| Standardized test scores | test records | optional |
| Socioeconomic indicators | self-report | optional |
| Learning disability diagnosis | records | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Grade trajectory (per subject) | time series | expected GPA next 3 terms |
| Graduation probability | percentage | on-time completion likelihood |
| Risk subjects | ranked list | subjects needing attention |
| Intervention priority | categorical | urgency of support needed |

## Data Sources

- NAEP (National Assessment of Educational Progress)
- PISA (OECD)
- IPEDS (postsecondary)
- State education department longitudinal data (where public)
- Early Warning System research literature

## Self-Correction

- **Accuracy metric:** MAE on grade predictions; graduation prediction AUC
- **Ground truth:** actual grades and graduation outcomes (longitudinal)
- **Retraining trigger:** MAE > 0.5 GPA points on validation cohort

## Refresh Frequency

- Per semester for grade trajectory
- Annually for graduation probability
- Real-time alert on significant attendance or grade drop

## Ethical Considerations

- Predictions must be used to provide support, never to reduce expectations or track students into lower-quality programs
- Socioeconomic factors must be treated as context for intervention, not as destiny
- Disparate prediction accuracy across racial/ethnic groups must be investigated and addressed
