# Pandemic Spread

**Domain:** Macro & Population
**Status:** scaffold
**Prediction type:** Infectious disease outbreak detection, spread modeling, and individual exposure risk prediction.

## What This Predicts

- Early detection of emerging outbreak signals
- Spread trajectory (R0 estimate, expected case counts, geographic expansion)
- Individual exposure risk by location, occupation, and behavior
- Healthcare system capacity stress prediction
- Variant emergence and immune escape probability

## Why This Matters

COVID-19 demonstrated that pandemic early warning and individual risk communication can save millions of lives — and that the absence of both causes catastrophic harm. This project builds the infrastructure for continuous, global outbreak monitoring and personalized risk communication.

## Key Inputs

**Population-level (automated):**
- WHO, CDC, ECDC disease surveillance reports
- HealthMap / ProMED outbreak reports
- Wastewater surveillance data
- Flight and mobility data

**Individual-level (user input):**
- Geographic location
- Vaccination status
- Occupation type
- Household composition
- Immune status / prior infection history

## Output

**Population:**
| Output | Type | Interpretation |
|--------|------|---------------|
| Outbreak alert level | categorical | watch/warning/emergency |
| R0 estimate | number with CI | transmissibility |
| Case count trajectory | time series | 4-week projection |
| Geographic spread map | geospatial | |

**Individual:**
| Output | Type | Interpretation |
|--------|------|---------------|
| Personal exposure risk | low/medium/high | |
| Behavioral risk reduction options | ranked list | |
| Vaccine effectiveness estimate | percentage | for current variants |

## Data Sources

- WHO Disease Outbreak News
- CDC FluView and COVID tracking
- ECDC (European Centre for Disease Prevention and Control)
- ProMED-mail
- HealthMap
- Our World in Data (vaccination, cases)
- Biobot Analytics (wastewater surveillance, where public)
- GLEAM (Global Epidemic and Mobility Model)
- FlightAware / OAG (mobility data)

## Self-Correction

- **Accuracy metric:** MAE of 4-week case count projections; calibration of spread trajectory
- **Ground truth:** actual reported case counts with lag adjustment
- **Retraining trigger:** MAE > 30% of actual case counts at 4 weeks

## Refresh Frequency

- Background monitoring: daily
- Active outbreak tracking: every 6 hours
- Individual risk assessment: weekly during active outbreaks; monthly at baseline

## Ethical Considerations

- Outbreak predictions must not incite panic — communicate probability and uncertainty clearly
- Individual risk communication must not lead to discrimination against people from outbreak regions
- Equity: predictions and recommendations must be useful and accessible to people without resources to follow all recommendations
- Prediction failures (false alarms, missed outbreaks) must be documented transparently
