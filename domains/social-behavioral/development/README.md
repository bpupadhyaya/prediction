# Social & Behavioral Domain — Development

## Shared Components (Planned)

- `pipelines/survey_data/` — behavioral survey data ingestion and anonymization
- `features/behavioral/` — lifestyle, social, and behavioral feature extraction
- `features/temporal/` — behavioral change over time features
- `privacy/sensitive_data.py` — enhanced privacy for behavioral and mental health data
- `evaluation/fairness.py` — demographic fairness audits for behavioral predictions

## Special Privacy Note

This domain handles some of the most sensitive data in the project (addiction, mental health, relationships). All development must use privacy-first architecture — raw behavioral data must never leave the user's device in identifiable form.

## Status

All planned. Privacy infrastructure must be completed before any user data collection begins in this domain.
