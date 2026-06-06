# Macro & Population Domain

Predictions at population and societal scale — events and trends that affect millions of people simultaneously and shape the conditions in which all other predictions operate.

## Domain Goals

- Predict large-scale events (pandemics, economic crises, migration waves) with enough lead time for preparation
- Provide geographic and demographic breakdowns of macro risks
- Feed macro context into individual-level predictions across all domains
- Inform policy decisions with prediction intelligence

## Projects

| Project | Prediction Focus | Status |
|---------|-----------------|--------|
| [pandemic-spread](projects/pandemic-spread/) | Infectious disease outbreak spread, severity, and individual exposure risk | scaffold |
| [economic-impact](projects/economic-impact/) | Recession probability, unemployment trajectory, sector-level disruption | scaffold |
| [migration-pressure](projects/migration-pressure/) | Population movement drivers, refugee flows, urbanization trends | scaffold |

## Research Focus

See [research/](research/) for:
- Epidemiological modeling literature (SIR models, agent-based models)
- Economic forecasting research
- Climate-migration research
- Ensemble forecasting approaches for macro prediction

## Development Focus

See [development/](development/) for:
- Real-time epidemiological data ingestion (WHO, CDC, ECDC)
- Economic indicator aggregation pipelines
- Geospatial population flow models
- Ensemble forecasting infrastructure

## Data Sources (Catalog)

- WHO Global Health Observatory
- Our World in Data
- World Bank Open Data
- IMF World Economic Outlook
- UN Population Division data
- ACLED (Armed Conflict Location & Event Data)
- Internal Displacement Monitoring Centre (IDMC)
- UNHCR refugee data
- BLS employment data
- Federal Reserve FRED (economic indicators)
- ProMED / HealthMap (disease outbreak monitoring)
- GLEAM (Global Epidemic and Mobility Model) outputs

## Ethical Considerations

- Economic predictions can be self-fulfilling — communication of recession predictions must be careful
- Migration predictions must not be used to justify border restrictions or surveillance of vulnerable populations
- Pandemic predictions must be communicated to help, not create panic or discrimination
- All macro predictions must acknowledge uncertainty ranges honestly

## Refresh Frequency

| Prediction Type | Suggested Refresh |
|-----------------|------------------|
| Pandemic spread | Daily during active outbreaks; weekly baseline |
| Economic impact | Monthly |
| Migration pressure | Monthly |

## Aggregation

Macro & Population predictions provide environmental context for all other domains:
- [Health](../health/) — pandemic context; population health trends
- [Finance](../finance/) — macroeconomic backdrop for individual financial predictions
- [Safety & Environment](../safety-environment/) — disaster and displacement risk
- [Collective Intelligence](../../collective-intelligence/) — essential macro layer
