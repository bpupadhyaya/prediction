# Caregiver Dependency

**Domain:** Aging
**Status:** scaffold
**Prediction type:** Prediction of the timeline to needing assistance with activities of daily living (ADLs) and progression to requiring full-time caregiver support or assisted living.

## What This Predicts

- Estimated years to needing help with instrumental ADLs (managing finances, driving, cooking)
- Estimated years to needing help with basic ADLs (bathing, dressing, eating, toileting)
- Probability of needing memory care specifically
- Probability of aging in place vs. requiring facility care
- Expected caregiver hours per week at each stage

## Why This Matters

Most people underestimate the likelihood and cost of late-life care dependency. Planning for caregiver needs 10–20 years in advance fundamentally changes financial, family, and living situation decisions.

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Age | self-report | yes |
| Current ADL and IADL function | self-assessment | yes |
| Chronic condition profile | self-report | yes |
| Cognitive status (MoCA) | assessment | yes |
| Living situation | self-report | yes |
| Available family support | self-report | yes |
| Income and assets | self-report | optional |
| Linked from cognitive-decline project | internal | optional |
| Linked from mobility-loss project | internal | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| IADL assistance timeline | years | estimated onset |
| ADL assistance timeline | years | estimated onset |
| Full-time care probability (5/10 years) | percentage | |
| Aging in place probability | percentage | |
| Caregiver hours trajectory | chart | hours/week by year |
| Planning recommendations | list | financial, family, housing |

## Data Sources

- NLTCS (National Long-Term Care Survey)
- NHATS (National Health and Aging Trends Study)
- Health and Retirement Study (HRS) — ADL transitions
- Genworth Cost of Care Survey (care cost data)
- Medicare claims data (public use files)

## Self-Correction

- **Accuracy metric:** MAE for ADL onset timing; calibration of care transition probabilities
- **Ground truth:** HRS longitudinal ADL transition data
- **Retraining trigger:** MAE > 2 years for IADL onset prediction

## Refresh Frequency

- Annually
- After any significant health event or functional change

## Ethical Considerations

- Dependency predictions must be framed as planning tools — never as loss of personhood
- Must not be used to pressure individuals into care arrangements against their wishes
- Cultural variation in family caregiving norms must be respected
- Predictions must acknowledge that caregiver availability is not equally distributed — single people, those without local family, and those without financial resources need specialized planning paths
