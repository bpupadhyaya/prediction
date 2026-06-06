# Income Trajectory

**Domain:** Finance
**Status:** scaffold
**Prediction type:** Projected income over 5, 10, and 20-year horizons based on current career, education, skills, and geographic factors.

## What This Predicts

- Expected income at 5, 10, and 20 years from now
- Income probability distribution (not just point estimate)
- Impact of specific career moves, education, or skill acquisition on income trajectory
- Geographic relocation impact on income

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Current income | self-report | yes |
| Occupation / job title | self-report | yes |
| Industry | self-report | yes |
| Education level | self-report | yes |
| Years of experience | self-report | yes |
| Geographic location | self-report | yes |
| Age | self-report | yes |
| Current skills | self-report | optional |
| Employer size / type | self-report | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Income at 5/10/20 years | distribution | with 25th/50th/75th percentile |
| Career move impact | delta | income change from specific action |
| Skill acquisition ROI | years to payback | for specific certifications/degrees |
| Geographic relocation impact | dollar delta | adjusted for cost of living |

## Data Sources

- BLS Occupational Employment and Wage Statistics
- Census American Community Survey (ACS)
- IPUMS (integrated census/survey microdata)
- Opportunity Insights (career mobility data)
- LinkedIn Salary Insights (aggregated, where available)
- BLS Employment Projections (10-year demand outlook)

## Self-Correction

- **Accuracy metric:** MAE of 5-year income prediction vs. actual; calibration of percentile predictions
- **Ground truth:** longitudinal income tracking (NLSY, PSID panel data); user-reported updates
- **Retraining trigger:** median prediction error > 20% of actual income

## Refresh Frequency

- Individual: annually or on career change
- Labor market data: quarterly (BLS updates)
- Model retraining: annually

## Ethical Considerations

- Income predictions must document structural wage gaps (gender, race) — never present discriminatory patterns as natural
- Predictions must not be used by employers to make compensation decisions
- Geographic predictions must account for cost of living, not just nominal wages
