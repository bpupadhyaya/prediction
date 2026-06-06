# Developmental Milestones

**Domain:** Early Life
**Status:** scaffold
**Prediction type:** Prediction of developmental trajectory and milestone timing in children from birth through age 8, to enable early identification of developmental delays.

## What This Predicts

- Expected timing of developmental milestones (motor, language, social, cognitive)
- Probability of developmental delay in specific domains
- Risk of autism spectrum disorder (ASD) — for early screening purposes
- Overall developmental trajectory score

## Why This Matters

Early intervention for developmental delays (especially before age 3) has dramatically better outcomes than later intervention. Many families wait until school entry to identify delays that could have been supported much earlier.

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Child's age | self-report | yes |
| Current milestone achievements | parent/caregiver report | yes |
| M-CHAT-R/F score (ASD screen, 16–30 months) | assessment | yes (for that age range) |
| Birth history (prematurity, complications) | self-report | yes |
| Language development | parent/caregiver report | yes |
| Motor development | parent/caregiver report | yes |
| Social and play behavior | parent/caregiver report | yes |
| Vision and hearing screening | clinical | optional |
| Family history of developmental conditions | self-report | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Milestone trajectory | chart | expected vs. observed timeline |
| Domain-specific delay probability | 0.0–1.0 | motor / language / social / cognitive |
| ASD screening result | screen positive/negative | referral recommendation only |
| Recommended next assessment | date | |
| Early intervention resources | list | services to contact |

## Data Sources

- CDC developmental milestones (Ages & Stages)
- WHO Child Development Standards
- M-CHAT-R/F validation studies
- ABCD Study (neurodevelopment)
- NIH Toolbox pediatric norms
- ASHA (language development) norms

## Self-Correction

- **Accuracy metric:** Sensitivity and specificity for delay detection vs. formal evaluation outcomes
- **Ground truth:** formal developmental evaluation results for referred children
- **Retraining trigger:** sensitivity for delay detection < 0.80

## Refresh Frequency

- Monthly in first year of life
- Every 2–3 months in years 2–3
- Every 6 months in years 4–8
- Immediately after any parental concern

## Ethical Considerations

- Results must consistently state: this is a screening tool, not a diagnosis
- ASD screening results are especially sensitive — delivery must be careful and supported
- Prematurity adjustments are essential — corrected age must be used
- Cultural variation in milestone timing and parental reporting styles must be modeled
- Developmental support must be accessible to families — predictions without accessible services are incomplete
