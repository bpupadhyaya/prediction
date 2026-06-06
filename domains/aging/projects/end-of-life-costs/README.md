# End-of-Life Costs

**Domain:** Aging
**Status:** scaffold
**Prediction type:** Estimated medical, long-term care, and end-of-life costs in the final 1, 5, and 10 years of life, by health trajectory and care preference.

## What This Predicts

- Expected total healthcare costs in final 10 years by disease trajectory
- Long-term care cost estimate (home care, assisted living, nursing home)
- Out-of-pocket vs. covered cost breakdown
- Impact of advance care planning choices on expected costs
- Geographic variation in care costs

## Why This Matters

The final years of life account for a disproportionate share of lifetime healthcare spending. Most people have no realistic estimate of these costs when making retirement financial plans. The gap between expected and actual end-of-life costs is a leading cause of financial devastation for surviving families.

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Age | self-report | yes |
| Current health conditions | self-report | yes |
| Geographic location | self-report | yes |
| Insurance type (Medicare, private, none) | self-report | yes |
| Advance directive status | self-report | optional |
| Preferred care setting (home, facility) | self-report | optional |
| Linked from caregiver-dependency project | internal | optional |
| Linked from life-expectancy project | internal | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Total end-of-life cost estimate (10 years) | dollar range | 25th/50th/75th percentile |
| Out-of-pocket cost estimate | dollar range | after insurance |
| Long-term care cost estimate | dollar range | |
| Annual cost trajectory | chart | costs by year and care stage |
| Cost reduction from advance planning | delta | financial impact of directives |

## Data Sources

- CMS Medicare claims (public use files)
- Dartmouth Atlas of Health Care
- Genworth Cost of Care Survey
- Kaiser Family Foundation end-of-life cost analysis
- RAND Health and Retirement Study cost modules
- NHPCO (hospice utilization data)

## Self-Correction

- **Accuracy metric:** Mean absolute error vs. actual Medicare costs in validation cohort
- **Ground truth:** CMS Medicare claims longitudinal data
- **Retraining trigger:** MAE > 20% of median actual costs

## Refresh Frequency

- Annually
- After major health event or care transition
- After advance directive changes

## Ethical Considerations

- Must not be used to pressure individuals or families into limiting care to save money
- End-of-life cost information must be presented in the context of supporting informed choice, not rationing
- Must be clear that advance care planning is about preferences, not cost optimization
- Geographic cost variation must not imply that expensive care is better care
- Predictions are estimates with wide ranges — must communicate uncertainty honestly
