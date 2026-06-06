# Mental Health Risk

**Domain:** Health
**Status:** scaffold
**Prediction type:** Onset risk for major mental health conditions and prediction of episode recurrence for those with existing diagnoses.

## What This Predicts

Two use cases:
1. **Onset prediction** — probability of developing depression, anxiety, PTSD, bipolar disorder, or psychosis in individuals not yet diagnosed
2. **Episode prediction** — probability of relapse or acute episode in individuals with existing diagnoses

## Why This Matters

50% of mental health conditions begin before age 14; 75% before age 24. Early identification enables early support. For those with existing conditions, episode prediction enables proactive intervention before crisis.

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| PHQ-9 (depression screen) | self-report | yes |
| GAD-7 (anxiety screen) | self-report | yes |
| Sleep quality and patterns | self-report or wearable | yes |
| Stress level | self-report | yes |
| Life events (loss, trauma, transitions) | self-report | yes |
| Social support | self-report | yes |
| Family history of mental illness | self-report | optional |
| Substance use | self-report | optional |
| Physical health conditions | self-report | optional |
| Genetic risk markers | genetic test | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Condition risk score | 0.0–1.0 | probability of onset within 12 months |
| Risk tier | categorical | low/medium/high |
| Key contributing factors | ranked list | for actionable guidance |
| Recommended resources | text | self-help, clinical referral thresholds |

## Data Sources

- NIMH research datasets
- UK Biobank (mental health phenotypes)
- ABCD Study (adolescent mental health longitudinal)
- All of Us (mental health + lifestyle)
- PHQ-9 / GAD-7 validation studies
- NESARC (National Epidemiologic Survey on Alcohol and Related Conditions)

## Self-Correction

- **Accuracy metric:** AUC-ROC, sensitivity at clinical referral threshold
- **Ground truth:** self-reported diagnosis; clinical records where available
- **Retraining trigger:** sensitivity < 0.70 at high-risk threshold
- **Special note:** ground truth acquisition is harder here — symptoms often go unreported

## Refresh Frequency

- Weekly screening for high-risk individuals
- Monthly for medium-risk individuals
- Quarterly for low-risk baseline

## Ethical Considerations

- Mental health predictions carry stigma risk — results must be private by design
- False positives cause unnecessary anxiety; false negatives can be dangerous — calibrate conservatively
- Predictions about suicide or self-harm risk require specific crisis resource protocols
- Must not be used in employment, insurance, or custody decisions
- Self-report bias is significant in mental health data — models must account for underreporting
- Cultural variation in symptom expression requires culturally-adapted models
