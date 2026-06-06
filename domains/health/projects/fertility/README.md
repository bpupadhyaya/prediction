# Fertility

**Domain:** Health
**Status:** scaffold
**Prediction type:** Reproductive health and fertility outcome prediction, including conception probability, pregnancy complication risk, and age-related fertility trajectory.

## What This Predicts

- Probability of conceiving naturally within 6/12 months given age, health, and lifestyle
- Risk of common pregnancy complications (gestational diabetes, preeclampsia, preterm birth)
- Estimated ovarian reserve trajectory (for those with ovaries)
- IVF success probability by protocol and patient characteristics

## Why This Matters

Infertility affects 1 in 6 people globally; most fertility-relevant decisions (when to try, whether to freeze eggs, when to seek help) are made without personalized prediction information.

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Age | self-report | yes |
| Sex / reproductive anatomy | self-report | yes |
| Menstrual cycle regularity | self-report | yes |
| BMI | self-report | yes |
| Smoking status | self-report | yes |
| Known reproductive conditions (PCOS, endometriosis, etc.) | self-report | optional |
| AMH level | lab result | optional |
| Antral follicle count | clinical imaging | optional |
| Semen analysis | lab result | optional (for sperm-producing partners) |
| Prior pregnancy history | self-report | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| 12-month conception probability | percentage | natural conception likelihood |
| Complication risk (per condition) | 0.0–1.0 | relative to population baseline |
| Optimal conception window | date range | for cycle-tracking integration |
| IVF success probability | percentage | if applicable |
| Egg freezing urgency | categorical | low/moderate/high |

## Data Sources

- SART (Society for Assisted Reproductive Technology) — IVF outcome data
- NSFG (National Survey of Family Growth)
- WHO reproductive health data
- ESHRE (European Society of Human Reproduction and Embryology) data
- Published AMH normative data by age

## Self-Correction

- **Accuracy metric:** Calibration of conception probability vs. actual conception within window
- **Ground truth:** user-reported pregnancy outcomes; SART registry for IVF outcomes
- **Retraining trigger:** calibration error > 0.05

## Refresh Frequency

- Baseline fertility assessment: annually
- During active conception attempts: monthly
- Pregnancy complication risk: each trimester

## Ethical Considerations

- Fertility predictions touch deeply personal and often painful experiences — tone and framing are critical
- Predictions about fertility decline must not be used to pressure individuals into reproductive decisions
- Must cover all biological sexes and family structures without heteronormative assumptions
- Racial disparities in fertility treatment access and outcomes must be documented, not obscured
