# Economic Impact

**Domain:** Macro & Population
**Status:** scaffold
**Prediction type:** Macroeconomic event prediction — recession probability, unemployment trajectory, sector disruption — and individual impact by demographic and occupation profile.

## What This Predicts

**Macro:**
- Recession probability (next 6/12 months)
- Unemployment rate trajectory by country and region
- Sector-specific disruption probability (technology, manufacturing, services, etc.)
- Inflation trajectory

**Individual:**
- Personal job loss risk given macro outlook and occupation profile
- Expected income impact from macroeconomic scenario
- Best-positioned sectors for career transitions in current macro environment

## Key Inputs

**Automated (macro data):**
- GDP growth, leading indicators, yield curve
- Employment statistics
- PMI, consumer confidence, credit spreads

**Individual:**
- Occupation and industry
- Geographic location
- Employment type (employee vs. contractor vs. owner)

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Recession probability (12 months) | percentage | |
| Unemployment projection | time series | by country/region |
| Sector stress index | 0.0–1.0 | per sector |
| Personal job loss risk | low/medium/high | given macro + individual profile |
| Career pivot recommendations | list | sectors with better macro outlook |

## Data Sources

- Federal Reserve FRED (economic indicators)
- BLS employment statistics
- IMF World Economic Outlook
- World Bank economic data
- OECD leading indicators
- Conference Board leading economic index
- St. Louis Fed recession probability models
- Sahm Rule real-time indicator

## Self-Correction

- **Accuracy metric:** Brier score for recession prediction; RMSE for unemployment trajectory
- **Ground truth:** actual GDP and employment outcomes
- **Retraining trigger:** Brier score > 0.20 for 12-month recession prediction

## Refresh Frequency

- Macro indicators: monthly (following major data releases)
- Model update: quarterly
- Individual risk assessment: monthly

## Ethical Considerations

- Recession probability communication must be carefully calibrated to avoid self-fulfilling dynamics
- Sector disruption predictions must be paired with retraining resources, not just warnings
- Predictions must be honest about model limitations — economic forecasting has a weak track record on timing
