# Entrepreneurship

**Domain:** Finance
**Status:** scaffold
**Prediction type:** Business survival probability, growth trajectory prediction, and failure risk indicators for early-stage ventures.

## What This Predicts

- Probability of business survival at 1, 3, and 5 years
- Key failure risk factors for a specific business profile
- Expected revenue trajectory range
- Probability of reaching profitability within target timeline

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Industry / business type | self-report | yes |
| Business age (months) | self-report | yes |
| Revenue (current) | self-report | yes |
| Monthly burn rate | self-report | yes |
| Runway (months of cash) | self-report | yes |
| Founder prior entrepreneurship experience | self-report | yes |
| Team size | self-report | yes |
| Market size estimate | self-report | optional |
| Funding raised | self-report | optional |
| Geographic market | self-report | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| 1/3/5-year survival probability | percentage | |
| Top 3 failure risk factors | ranked list | specific to this profile |
| Revenue trajectory | distribution | 25th/50th/75th percentile |
| Time to profitability | distribution | months |
| Benchmarks vs. similar companies | comparison | industry survival rates |

## Data Sources

- SBA Small Business survival data
- BLS Business Employment Dynamics
- Kauffman Foundation startup data
- Census Bureau Business Formation Statistics
- Crunchbase aggregated startup outcomes (where public)
- OECD Entrepreneurship at a Glance

## Self-Correction

- **Accuracy metric:** Brier score for survival predictions; calibration by industry
- **Ground truth:** SBA business closure data; longitudinal entrepreneur surveys
- **Retraining trigger:** calibration error > 0.08 for any major industry category

## Refresh Frequency

- Monthly for businesses in first 2 years
- Quarterly for established businesses
- Real-time alert on runway dropping below 6 months

## Ethical Considerations

- Predictions must be empowering, not discouraging — always include success factors alongside risk factors
- Must not be used by investors or lenders in ways that disadvantage founders from underrepresented groups
- Acknowledge that structural barriers (access to capital, networks) explain much of the variation — not just founder quality
