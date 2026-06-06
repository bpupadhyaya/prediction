# Natural Disaster

**Domain:** Safety & Environment
**Status:** scaffold
**Prediction type:** Location-based risk assessment for natural disaster exposure — earthquakes, floods, wildfires, hurricanes/cyclones, tornadoes — with both chronic risk and real-time situational awareness.

## What This Predicts

- Annual probability of significant disaster exposure by type for a specific location
- Expected severity distribution (minor damage vs. displacement vs. life-threatening)
- Long-term risk trajectory as climate changes alter disaster frequency and intensity
- Real-time elevated risk during active events

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Geographic location (lat/long or address) | user input | yes |
| Housing type (wood-frame, concrete, mobile) | self-report | optional |
| Elevation | derived (DEM data) | automatic |
| Distance to flood zone, fault line, fire risk zone | derived | automatic |
| Local building code era | derived | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Annual risk probability (per disaster type) | percentage | |
| 30-year risk trajectory | trend | accounting for climate change |
| Severity distribution | histogram | expected damage levels |
| Real-time alert | notification | during active elevated risk |
| Preparedness recommendations | list | specific to location and risk |

## Data Sources

- USGS National Seismic Hazard Maps
- FEMA National Flood Hazard Layer
- FEMA National Risk Index
- NOAA storm track and intensity data
- USFS wildfire risk data
- NASA FIRMS (Fire Information for Resource Management System)
- Global Earthquake Model (GEM)
- IPCC climate projections (future disaster frequency)

## Self-Correction

- **Accuracy metric:** Calibration of annual probability vs. historical event rates by location
- **Ground truth:** SHELDUS (Spatial Hazard Events and Losses for the US); EM-DAT (international)
- **Retraining trigger:** location-type calibration error > 0.05

## Refresh Frequency

- Chronic risk assessment: annually (climate models and hazard maps update)
- Real-time situational awareness: continuous during active events

## Ethical Considerations

- Predictions must be delivered with preparedness resources, not just risk scores
- Low-income communities in high-risk zones often lack options for relocation — risk communication must acknowledge this
- Real-time predictions carry responsibility — must be reliable and not create panic
- Climate risk trajectory must be clearly communicated, not minimized
