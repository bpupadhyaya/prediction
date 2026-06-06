# Safety & Environment Domain — Development

## Shared Components (Planned)

- `pipelines/geospatial/` — location-based hazard data ingestion (USGS, NOAA, EPA)
- `pipelines/air_quality/` — real-time air quality data pipeline (EPA AQS, satellite)
- `features/location/` — geographic risk feature extraction
- `models/geospatial/` — geospatial ML model utilities
- `realtime/alert_engine/` — real-time hazard alert generation

## Key Technical Challenge

Most predictions in this domain are location-specific and require geospatial data pipelines. Establish the geospatial ingestion layer early — it is a prerequisite for all projects in this domain.

## Status

All planned. Priority: geospatial data ingestion pipeline.
