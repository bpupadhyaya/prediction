# Climate Impact

**Domain:** Safety & Environment
**Status:** scaffold
**Prediction type:** Long-term personal and community-level impacts of climate change on a specific location — heat, flooding, drought, sea level rise, air quality, and livability.

## What This Predicts

- Projected changes in temperature, precipitation, and extreme heat days at a specific location over 10, 30, and 50-year horizons
- Sea level rise impact for coastal locations
- Agricultural viability change for rural/farming locations
- Climate-driven livability score trajectory
- Health impacts from climate change at a specific location

## Why This Matters

Climate change is the largest long-term predictor of where on Earth will be livable in 50 years. This information is critical for multi-decade decisions about where to live, where to own property, and where to raise children.

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Geographic location | user input | yes |
| Time horizon of interest | user input | yes |
| Climate scenario preference (SSP2/SSP5) | user input | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Temperature trajectory | trend with CI | annual mean and extreme heat days |
| Extreme precipitation trend | trend | annual flood risk events |
| Sea level rise (coastal) | cm by decade | inundation probability |
| Livability score trajectory | 0.0–1.0 | composite habitability |
| Health risk change | delta | heat-related illness, disease vector change |
| Agricultural impact (rural) | delta | growing season and yield change |

## Data Sources

- IPCC AR6 climate projections
- CMIP6 climate model ensemble data
- NASA Sea Level Change data
- NOAA climate projections
- Climate Central (sea level and flood risk)
- First Street Foundation Flood Model
- EPA Climate Change Indicators

## Self-Correction

- **Accuracy metric:** Hindcast accuracy — how well do 10-year-old projections match what actually happened
- **Ground truth:** historical climate station data; NOAA observed trends
- **Retraining trigger:** hindcast RMSE > 1.5°C for temperature projection

## Refresh Frequency

- Annual — IPCC scenarios and climate model ensembles update
- Real-time updates during extreme events

## Ethical Considerations

- Must present multiple climate scenarios (not just worst case or best case)
- Uncertainty ranges must be clearly communicated
- Must not be used to accelerate displacement of communities from climate-vulnerable areas without addressing structural support
- Climate migration is a justice issue — predictions must be coupled with equity-aware policy context
