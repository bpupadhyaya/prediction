# Infrastructure

Shared infrastructure for the Prediction project. All components are optional — projects can use domain-specific tooling — but this provides common solutions to common problems.

## Components

### Data Infrastructure
- **Data catalog** — registry of all data sources used across the project, with licensing, update frequency, and access instructions
- **Ingestion framework** — common patterns for pulling from APIs, downloading datasets, and validating data quality
- **Storage conventions** — standard formats and directory conventions for raw, processed, and model data

### Model Infrastructure
- **Model registry** — track all trained models across projects: version, training data, accuracy metrics, deployment status
- **Training pipeline templates** — common patterns for train/validate/test splits, cross-validation, and hyperparameter search
- **Accuracy tracking** — shared accuracy logging format and storage so any project can record prediction accuracy consistently

### API Infrastructure
- **Prediction API standard** — common REST/GraphQL interface spec that all projects should conform to
- **Confidence interval standard** — how predictions with uncertainty are serialized and communicated
- **Refresh scheduler** — AI-driven refresh frequency management for any project

### Privacy Infrastructure
- **Differential privacy utilities** — shared implementations for adding privacy guarantees to sensitive models
- **Data anonymization** — tools for PII removal and k-anonymization
- **Consent management** — framework for tracking what data a user has consented to use

### Monitoring
- **Accuracy drift detection** — alerts when any project's accuracy degrades below threshold
- **Data freshness monitoring** — alerts when data sources haven't been updated as expected
- **Coverage tracking** — what fraction of the human lifespan is currently covered by operational projects

## Research Focus

See [research/](research/) for:
- Privacy-preserving ML approaches (federated learning, differential privacy)
- Efficient data collection and storage at global scale
- Infrastructure for globally distributed contribution

## Development Focus

See [development/](development/) for:
- Implementation of shared infrastructure components
- Documentation and onboarding guides for shared tooling
- CI/CD for the shared infrastructure

## Status

All components planned. Priority order:
1. Accuracy tracking (needed by every project immediately)
2. Data catalog (prevents duplicate work across projects)
3. Prediction API standard (needed for Collective Intelligence integration)
4. Privacy infrastructure (needed before any user data is collected)

## Contributing

Infrastructure contributions have disproportionate impact — they benefit every project that adopts them. If you build a component here, document it thoroughly so projects can use it without help.
