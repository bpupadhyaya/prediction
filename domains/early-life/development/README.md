# Early Life Domain — Development

## Shared Components (Planned)

- `pipelines/genetic/` — newborn genetic data processing
- `features/developmental/` — milestone feature extraction and age-normalization
- `features/pediatric/` — pediatric-specific feature engineering (corrected age, growth charts)
- `privacy/pediatric.py` — consent management for minor data
- `evaluation/sensitivity.py` — sensitivity/specificity for screening tools

## Special Note: Pediatric Privacy

All data collection for this domain requires parental consent frameworks. No child data may be collected or stored without an explicit consent management layer. This must be built before any user-facing features.

## Status

All planned. Priority: consent management framework (prerequisite for all else).
