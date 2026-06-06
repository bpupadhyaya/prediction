# Financial Distress

**Domain:** Finance
**Status:** scaffold
**Prediction type:** Probability of financial crisis events — bankruptcy, severe debt burden, income loss, housing instability — within 6–24 month windows.

## What This Predicts

- Probability of filing bankruptcy within 12/24 months
- Risk of falling behind on housing payments (mortgage or rent)
- Risk of debt-to-income ratio exceeding critical threshold
- Probability of significant income disruption (job loss, medical crisis)

## Why This Matters

Most financial crises don't happen overnight — they develop over months of compounding stress. Early prediction enables early intervention: debt counseling, emergency savings, job search, or benefit enrollment before the crisis arrives.

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Monthly income | self-report | yes |
| Monthly essential expenses | self-report | yes |
| Total debt | self-report | yes |
| Emergency savings (months of expenses) | self-report | yes |
| Employment stability | self-report | yes |
| Industry (recession sensitivity) | self-report | yes |
| Housing cost as % of income | derived | yes |
| Number of dependents | self-report | optional |
| Health insurance status | self-report | optional |
| Credit score | self-report | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Distress probability (12 months) | percentage | probability of crisis event |
| Distress probability (24 months) | percentage | |
| Most likely distress type | categorical | bankruptcy / housing / income loss |
| Resilience score | 0.0–1.0 | buffer against unexpected shocks |
| Recommended actions | ranked list | highest-impact steps to reduce risk |

## Data Sources

- Federal Reserve Survey of Consumer Finances (SCF)
- SIPP (Survey of Income and Program Participation)
- BLS employment and layoff statistics
- CFPB (Consumer Financial Protection Bureau) consumer data
- Opportunity Insights (economic distress by geography)
- Case-Shiller housing data

## Self-Correction

- **Accuracy metric:** AUC for distress event prediction; calibration of probability estimates
- **Ground truth:** user-reported outcomes; public bankruptcy records (aggregate)
- **Retraining trigger:** AUC < 0.72 for any distress category

## Refresh Frequency

- Monthly for individuals with distress probability > 20%
- Quarterly otherwise
- Real-time alert on major expense, income, or debt change

## Ethical Considerations

- Must direct high-risk individuals to free financial counseling resources
- Must not be used by lenders to deny credit — this is a consumer tool
- Income-based predictions should acknowledge that low-income instability is often structural, not behavioral
- Avoid shame-based framing; predictions must feel like a safety system, not a judgment
