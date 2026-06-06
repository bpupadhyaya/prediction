# Mental Health Episodes

**Domain:** Social & Behavioral
**Status:** scaffold
**Prediction type:** Prediction of acute mental health crisis events — severe depressive episodes, manic episodes, psychotic episodes — for individuals with existing diagnoses.

## What This Predicts

Short-term prediction (7–30 days) of acute episode onset for individuals with known bipolar disorder, schizophrenia, major depressive disorder, or PTSD. This is a relapse prevention tool, not a screening tool — it is for people who have an existing diagnosis and want early warning.

## Why This Matters

Most acute mental health crises involve a prodromal phase — a window of 1–4 weeks where early intervention can prevent hospitalization. Passive monitoring (sleep, activity, language patterns) can detect these windows without requiring constant self-report.

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Diagnosis type | self-report | yes |
| Medication adherence | self-report | yes |
| Sleep hours and quality | wearable / self-report | yes |
| Daily mood check-in | self-report | yes |
| Social withdrawal indicators | self-report | optional |
| Activity level | wearable | optional |
| Speech pattern changes | voice analysis (opt-in) | optional |
| Life stressor events | self-report | optional |
| Prior episode history | self-report | yes |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Episode risk (7-day) | low/medium/high | |
| Episode risk (30-day) | low/medium/high | |
| Warning signs detected | list | specific observed signals |
| Recommended actions | list | self-care, contact support, contact clinician |
| Crisis resources | link | hotlines, emergency contacts |

## Data Sources

- Bipolar longitudinal studies (STEP-BD, SiGN)
- mHealth research studies (CrossCheck, PRIORI)
- NIMH naturalistic observation studies
- PTSD longitudinal datasets
- Wearable biosignal research in psychiatric conditions

## Self-Correction

- **Accuracy metric:** Sensitivity at high-risk threshold; false positive rate (to avoid alert fatigue)
- **Ground truth:** user-reported episodes; hospitalization records
- **Retraining trigger:** sensitivity < 0.70 OR false positive rate > 0.30 at high-risk threshold

## Refresh Frequency

- Daily monitoring during stable periods
- Continuous during elevated-risk periods
- Real-time alert capability for acute deterioration signals

## Ethical Considerations

- This is the highest-stakes project in the Social & Behavioral domain — false negatives can have life-threatening consequences
- Alert design must balance sensitivity with alert fatigue — too many false alarms reduce compliance
- Crisis resource access must always be one tap/click away
- Passive monitoring (sleep, activity) requires explicit informed consent
- Voice analysis is highly sensitive — must be fully opt-in with clear data deletion rights
- Results must flow to the individual first; sharing with caregivers requires explicit user consent
