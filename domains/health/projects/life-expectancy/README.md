# Life Expectancy

**Domain:** Health
**Status:** scaffold
**Prediction type:** Estimated remaining lifespan and probability of surviving to specific ages, based on health, lifestyle, genetics, and environment.

## What This Predicts

Personalized life expectancy estimates and survival probability curves. Unlike actuarial tables that use population averages, this project builds individual-level models using the full range of health, behavioral, genetic, and environmental inputs available.

## Why This Matters

Life expectancy prediction informs retirement planning, insurance decisions, and — most importantly — motivates health behavior change when people can see the concrete impact of lifestyle choices on their remaining years.

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Age, sex | self-report | yes |
| Smoking history | self-report | yes |
| BMI | self-report | yes |
| Chronic conditions | self-report | yes |
| Exercise frequency | self-report | yes |
| Diet quality | self-report | yes |
| Alcohol consumption | self-report | yes |
| Geographic location | self-report | yes |
| Income / socioeconomic status | self-report | yes |
| Sleep quality | self-report | optional |
| Genetic longevity markers | genetic test | optional |
| Environmental exposures | location-derived | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Life expectancy estimate | years | median expected age at death |
| Survival curve | probability by age | P(survive to age X) |
| Years gained/lost by factor | years | modifiable factor impact |
| Uncertainty range | confidence interval | 80% CI on estimate |

## Data Sources

- Social Security Administration actuarial tables (baseline)
- NHANES longitudinal mortality follow-up
- Health and Retirement Study (HRS)
- UK Biobank mortality outcomes
- WHO Life Tables by country

## Self-Correction

- **Accuracy metric:** Mean absolute error in predicted vs. actual age at death (validation cohort)
- **Ground truth:** longitudinal mortality tracking in study cohorts
- **Retraining trigger:** MAE degrades > 2 years on held-out cohort
- **Accuracy log:** `development/accuracy_log.json`

## Refresh Frequency

- Full reassessment: annually or on significant health event
- Geographic/environmental component: annually

## Ethical Considerations

- Communicate uncertainty clearly — a single point estimate without confidence interval is misleading
- Predictions must not be used by insurers to deny or price coverage
- Avoid framing that induces fatalism — always pair with modifiable factor breakdown
- Different populations have very different baseline life expectancies due to structural factors (racism, poverty) — models must not treat these as purely individual
