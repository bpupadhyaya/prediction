# Safety & Environment Domain

Predictions about physical safety risks, environmental exposures, and how the physical world affects human health and survival.

## Domain Goals

- Predict individual and community-level safety risks before harm occurs
- Quantify environmental health impacts on specific populations
- Enable climate-informed decision-making for individuals and communities
- Connect environmental conditions to health and economic outcomes

## Projects

| Project | Prediction Focus | Status |
|---------|-----------------|--------|
| [accident-risk](projects/accident-risk/) | Risk of home, road, workplace, and recreational accidents | scaffold |
| [natural-disaster](projects/natural-disaster/) | Exposure risk and impact severity from earthquakes, floods, fires, storms | scaffold |
| [climate-impact](projects/climate-impact/) | Long-term climate change effects on a specific location and population | scaffold |
| [pollution-health](projects/pollution-health/) | Health effects of air, water, and soil pollution exposure | scaffold |

## Data Sources (Catalog)

- EPA Air Quality System (AQS) data
- NOAA climate and weather data
- USGS earthquake and flood data
- NASA Earth observing data (wildfire, flood, drought)
- FEMA National Risk Index
- WHO Environmental Health data
- Global Burden of Disease (pollution attribution)
- IPCC climate scenarios
- OpenStreetMap (infrastructure vulnerability)
- BLS injury and illness data (workplace safety)

## Ethical Considerations

- Environmental risk predictions must highlight the disproportionate burden on low-income and minority communities — do not present as purely geographic when causation includes environmental justice factors
- Disaster risk predictions must account for differential access to preparedness resources
- Avoid predictions that could be used to deny insurance or displace vulnerable populations without alternative support
- Climate predictions should be clear about timescales and uncertainty ranges

## Refresh Frequency

| Prediction Type | Suggested Refresh |
|-----------------|------------------|
| Accident risk | Annually or on lifestyle change |
| Natural disaster exposure | Annually; real-time during active events |
| Climate impact (long-term) | Annually |
| Pollution-health risk | Monthly (air quality); quarterly (water/soil) |

## Aggregation

Safety & Environment predictions feed into:
- [Health](../health/) — environmental exposure is a major disease risk factor
- [Finance](../finance/) — disaster exposure affects financial risk
- [Macro & Population](../macro-population/) — aggregates into population-level risk
- [Collective Intelligence](../../collective-intelligence/)
