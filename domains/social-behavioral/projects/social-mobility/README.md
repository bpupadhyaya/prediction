# Social Mobility

**Domain:** Social & Behavioral
**Status:** scaffold
**Prediction type:** Probability and pathway of upward economic and social mobility, given current circumstances and available interventions.

## What This Predicts

- Probability of achieving a higher income quintile within 10 years
- Expected intergenerational mobility (how will children's economic outcomes compare to parents?)
- Impact of specific interventions (education, geographic relocation, training) on mobility probability
- Geographic variation in mobility opportunity

## Why This Matters

Research by Chetty et al. shows that where you grow up is one of the strongest predictors of life outcomes — but most people don't have access to mobility data to inform their decisions. Making this data personal and actionable can change decision-making at scale.

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Current income quintile | derived | yes |
| Parents' income quintile | self-report | yes |
| Geographic location | self-report | yes |
| Education level | self-report | yes |
| Age | self-report | yes |
| Race / ethnicity | self-report | yes (for bias-aware modeling) |
| Network quality | self-report | optional |
| Children's ages | self-report | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| 10-year mobility probability | percentage | P(moving up ≥1 quintile) |
| Geographic mobility map | map | areas with higher mobility for this profile |
| Intervention impact | table | expected mobility gain from specific actions |
| Intergenerational prediction | distribution | children's likely outcomes |

## Data Sources

- Opportunity Insights (Chetty et al.) — the most comprehensive mobility dataset
- Census American Community Survey
- PSID (Panel Study of Income Dynamics)
- NLSY
- World Bank Intergenerational Mobility database

## Self-Correction

- **Accuracy metric:** Predicted vs. actual quintile movement in longitudinal cohorts
- **Ground truth:** PSID, NLSY longitudinal income tracking
- **Retraining trigger:** quintile prediction accuracy < 60%

## Refresh Frequency

- Individual: annually
- Geographic mobility data: annually (Opportunity Insights updates)

## Ethical Considerations

- Mobility predictions must contextualize individual predictions within structural barriers — never imply that low mobility probability is a personal failing
- Must not be used to justify policies that reduce support for low-mobility communities
- Geographic recommendations must acknowledge that relocation is not equally accessible to all
- Race and structural discrimination must be named explicitly, not treated as unexplained variance
