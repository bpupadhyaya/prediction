# Migration Pressure

**Domain:** Macro & Population
**Status:** scaffold
**Prediction type:** Population movement driver prediction — conflict, climate, economic, and health-driven migration flows — and their community-level impacts.

## What This Predicts

- Regions where migration pressure is likely to increase in 1–5 year horizon
- Drivers of migration (climate, conflict, economic, health) by region
- Population flow direction and magnitude projections
- Receiving community impact predictions (housing, healthcare, labor market)
- Refugee flow predictions following conflict or disaster events

## Why This Matters

Migration is one of the most consequential demographic forces of the 21st century. Accurate prediction of migration pressure enables receiving communities to prepare, and enables sending communities to address root causes.

## Key Inputs (All Automated)

- Climate stress indices by region
- Conflict event data (ACLED)
- Economic hardship indices
- Disease burden data
- Historical migration flow patterns
- Political stability indices

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Migration pressure index | 0.0–1.0 | per region, 12-month horizon |
| Primary driver | categorical | climate/conflict/economic/health |
| Expected flow magnitude | population range | people likely to move |
| Destination probability | ranked list | likely destination regions |
| Receiving community stress | low/medium/high | per destination |

## Data Sources

- UNHCR refugee data
- IOM (International Organization for Migration) data
- IDMC (Internal Displacement Monitoring Centre)
- ACLED (conflict event data)
- Climate vulnerability indices (Notre Dame ND-GAIN)
- World Bank economic indicators by country
- INFORM Risk Index

## Self-Correction

- **Accuracy metric:** Correlation of predicted vs. actual migration flows (with 12-month lag)
- **Ground truth:** UNHCR and IOM actual flow data
- **Retraining trigger:** flow magnitude prediction RMSE > 40% of actual

## Refresh Frequency

- Monthly baseline updates
- Real-time updates on conflict events or climate disasters
- Quarterly model retraining

## Ethical Considerations

- Migration predictions must not be weaponized for border militarization or refugee exclusion
- Must distinguish between voluntary migration and forced displacement
- Community impact predictions must be balanced — migration has both costs and benefits for receiving communities
- Predictions about people fleeing conflict or disaster must be handled with dignity
- Avoid framing that dehumanizes migrants or presents migration as inherently threatening
