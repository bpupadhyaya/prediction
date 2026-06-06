# Pollution-Health

**Domain:** Safety & Environment
**Status:** scaffold
**Prediction type:** Personal health risk from air, water, and soil pollution exposure based on location and lifestyle.

## What This Predicts

- Cumulative health risk from long-term air pollution exposure (PM2.5, ozone, NO2)
- Drinking water contamination risk by location
- Soil contamination risk for specific locations (near industrial sites, etc.)
- Health outcome risk increase from combined pollution exposures

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Home address / location | user input | yes |
| Years at current location | self-report | yes |
| Work location (if different) | user input | optional |
| Outdoor activity level | self-report | optional |
| Pre-existing respiratory or cardiovascular conditions | self-report | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| PM2.5 annual exposure estimate | µg/m³ | vs. WHO guideline of 5 µg/m³ |
| Health risk increase (all-cause mortality) | percentage delta | vs. clean air baseline |
| Water contamination risk | low/medium/high | by contaminant type |
| Lung cancer risk delta from air pollution | percentage | additional risk above baseline |
| Recommendations | list | filtration, activity adjustments |

## Data Sources

- EPA Air Quality System (AQS) — monitoring station data
- NASA MODIS aerosol optical depth — satellite PM2.5 estimates
- EPA Safe Drinking Water Act violation data
- EPA ECHO (Enforcement and Compliance History)
- EPA Superfund site database
- EWG Tap Water Database
- WHO Global Air Pollution data
- GBD (Global Burden of Disease) — pollution attribution

## Self-Correction

- **Accuracy metric:** Correlation between exposure estimates and health outcomes in epidemiological cohorts
- **Ground truth:** GBD pollution-attributable mortality data; epidemiological cohort studies
- **Retraining trigger:** exposure-outcome correlation < 0.60 in validation cohorts

## Refresh Frequency

- Air quality: daily (real-time monitoring data)
- Water contamination: quarterly (violation reports)
- Soil/Superfund: annually
- Health risk model: annually

## Ethical Considerations

- Pollution burden falls disproportionately on low-income communities and communities of color — must name this explicitly
- Predictions must not be used by insurers or employers
- Must connect predictions to community advocacy resources, not just individual behavior change
- Individual action recommendations must be honest about their limited impact vs. systemic change
