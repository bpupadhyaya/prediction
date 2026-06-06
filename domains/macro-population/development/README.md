# Macro & Population Domain — Development

## Shared Components (Planned)

- `pipelines/who_data/` — WHO surveillance data ingestion
- `pipelines/economic_indicators/` — shared with finance domain
- `pipelines/conflict_data/` — ACLED conflict event data
- `pipelines/climate_stress/` — climate vulnerability index data
- `models/ensemble/` — ensemble forecasting framework
- `realtime/outbreak_monitor/` — continuous epidemiological surveillance

## Key Technical Note

This domain requires the most robust real-time data pipelines of any domain — particularly for pandemic spread monitoring. Build reliability and alerting into the pipeline from the start.

## Status

All planned. Priority: outbreak monitoring pipeline (highest public health impact, most time-sensitive).
