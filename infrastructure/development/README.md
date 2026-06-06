# Infrastructure — Development

## Purpose

Implement shared infrastructure components used by all projects in the Prediction project.

## Priority Components

### 1. Accuracy Tracker (Priority: Highest)
Every project needs to record prediction accuracy over time. This provides a common format and storage solution.

```python
# Planned interface
from prediction_infra import AccuracyTracker

tracker = AccuracyTracker(project="health/disease-risk")
tracker.log_prediction(
    prediction_id="pred_123",
    prediction={"cardiovascular_5yr": 0.12},
    confidence={"cardiovascular_5yr": (0.08, 0.16)},
    timestamp="2026-01-01"
)
tracker.log_outcome(
    prediction_id="pred_123",
    outcome={"cardiovascular_5yr": False},
    outcome_timestamp="2031-01-15"
)
metrics = tracker.compute_accuracy()  # AUC, calibration, etc.
```

**Status:** planned
**Directory:** `src/accuracy_tracker/`

### 2. Data Catalog
Registry of all data sources used across the project.

**Schema:**
```json
{
  "source_id": "cdc_brfss",
  "name": "CDC BRFSS",
  "url": "https://www.cdc.gov/brfss/",
  "license": "public domain",
  "update_frequency": "annual",
  "last_updated": "2025-09-01",
  "domains": ["health", "social-behavioral"],
  "format": "SAS / CSV",
  "access_method": "download",
  "quality_score": null
}
```

**Status:** planned
**File:** `data_catalog.json`

### 3. Prediction API Standard
Standard REST interface that all projects should expose.

```
GET /predict
  ?domain=health
  &project=disease-risk
  &inputs={...}

Returns:
{
  "predictions": [{
    "target": "cardiovascular_5yr",
    "value": 0.12,
    "confidence_interval": [0.08, 0.16],
    "prediction_window": "5 years",
    "model_version": "1.2.0",
    "last_trained": "2026-01-01",
    "accuracy_metrics": {...}
  }],
  "timestamp": "2026-06-06T12:00:00Z"
}
```

**Status:** draft spec
**File:** `api_spec/prediction_api.yaml`

### 4. Privacy Utilities
Differential privacy and anonymization tools.

**Status:** planned
**Directory:** `src/privacy/`

## Conventions

### Code
- Python 3.10+
- Type annotations required
- Tests required for all shared components (pytest)
- Docstrings for all public interfaces

### Data
- Raw data: never committed to git (use .gitignore)
- Processed features: stored in parquet format
- Model artifacts: tracked in model registry (DVC or similar)

## Getting Started

If you want to build a component, open an issue first to avoid duplicate work. Start with the Accuracy Tracker — it has the clearest spec and the broadest benefit.
