# Finance Domain

Predictions about economic trajectories, financial health, and wealth outcomes across an individual's lifetime.

## Domain Goals

- Give individuals actionable predictions about their financial future
- Enable early warning of financial distress before crises occur
- Improve retirement planning through accurate long-horizon projections
- Democratize access to financial intelligence currently available only to the wealthy

## Projects

| Project | Prediction Focus | Status |
|---------|-----------------|--------|
| [income-trajectory](projects/income-trajectory/) | Future income based on career, education, geography, and skills | scaffold |
| [financial-distress](projects/financial-distress/) | Risk of bankruptcy, debt crisis, or income disruption | scaffold |
| [retirement-readiness](projects/retirement-readiness/) | Probability of achieving financially secure retirement | scaffold |
| [entrepreneurship](projects/entrepreneurship/) | Business survival probability and growth trajectory prediction | scaffold |
| [stock-market](projects/stock-market/) | Equity direction, magnitude, volatility, and portfolio drawdown risk prediction | scaffold |

## Data Sources (Catalog)

- Federal Reserve Survey of Consumer Finances (SCF)
- Survey of Income and Program Participation (SIPP)
- Bureau of Labor Statistics (BLS) — wages, employment
- OECD Economic Outlook data
- World Bank Open Data
- IRS Statistics of Income (SOI)
- Opportunity Insights (Harvard) — income mobility data
- Crunchbase / PitchBook open data (entrepreneurship)
- Small Business Administration survival statistics

## Ethical Considerations

- Financial predictions must not encode or amplify existing economic inequality
- Predictions of financial distress must lead to support resources, not judgment
- Predictions should be transparent about what they can and cannot account for (macro shocks, discrimination)
- Income predictions that differ by race, gender, or geography must acknowledge structural causes
- No predictions should be used for discriminatory lending or insurance decisions

## Refresh Frequency

| Prediction Type | Suggested Refresh |
|-----------------|------------------|
| Income trajectory | Annually or on major career event |
| Financial distress risk | Monthly |
| Retirement readiness | Quarterly |
| Entrepreneurship survival | Monthly in first 2 years; quarterly thereafter |

## Aggregation

Finance domain predictions feed into:
- [Health](../health/) — financial stress affects health outcomes
- [Social & Behavioral](../social-behavioral/) — financial trajectory affects relationship and mobility outcomes
- [Collective Intelligence](../../collective-intelligence/)
