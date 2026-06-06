# Retirement Readiness

**Domain:** Finance
**Status:** scaffold
**Prediction type:** Probability of achieving a financially secure retirement at target age, with scenario modeling for different savings and lifestyle choices.

## What This Predicts

- Probability of retirement assets lasting through expected lifespan
- Expected monthly income in retirement from all sources
- Age at which retirement becomes financially viable
- Impact of different savings rates, investment returns, and retirement ages

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Current age | self-report | yes |
| Target retirement age | self-report | yes |
| Current retirement savings | self-report | yes |
| Monthly retirement contributions | self-report | yes |
| Expected Social Security / pension | estimate tool | yes |
| Current income | self-report | yes |
| Expected retirement expenses | self-report | yes |
| Investment allocation | self-report | optional |
| Healthcare cost expectations | self-report | optional |
| Life expectancy estimate | linked from health domain | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Retirement readiness probability | percentage | P(assets last through death) |
| Expected monthly retirement income | dollar range | at target retirement age |
| Savings rate recommendation | percentage of income | to hit 90% readiness |
| Retirement age scenarios | table | readiness at ages 60/65/67/70 |
| Sensitivity analysis | tornado chart | which factors matter most |

## Data Sources

- Social Security Administration benefit calculators and actuarial data
- Federal Reserve SCF (retirement savings distribution)
- BLS Consumer Expenditure Survey (retirement spending patterns)
- Vanguard / Fidelity aggregated retirement data (where public)
- EBRI (Employee Benefit Research Institute)
- Monte Carlo simulation of market returns (historical distributions)

## Self-Correction

- **Accuracy metric:** Calibration of savings adequacy prediction vs. actual retirement income sufficiency in longitudinal cohorts
- **Ground truth:** Health and Retirement Study (HRS) longitudinal data
- **Retraining trigger:** calibration slope < 0.85 on HRS validation

## Refresh Frequency

- Quarterly for individuals within 10 years of target retirement age
- Annually otherwise
- On significant financial event (inheritance, job loss, major expense)

## Ethical Considerations

- Most people globally have no formal pension or retirement system — models must be adapted for informal economy workers
- Do not assume Western retirement frameworks — some cultures have family-based elder care as the primary model
- Must be honest about inadequate savings without being fatalistic — always pair with actionable improvement paths
- Inflation assumptions must be conservative and disclosed
