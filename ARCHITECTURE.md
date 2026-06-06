# Architecture

## Overview

The Prediction project is organized as a three-tier hierarchy: **Projects → Domains → Collective Intelligence**. Each tier produces predictions that feed into the tier above. At the top, Collective Intelligence aggregates into the AGI Foundation.

```
┌─────────────────────────────────────────────┐
│              AGI Foundation                  │
│     (cross-domain reasoning & synthesis)     │
└─────────────────────┬───────────────────────┘
                      │
┌─────────────────────▼───────────────────────┐
│           Collective Intelligence            │
│     (aggregated domain-level models)         │
└──┬──────┬──────┬──────┬──────┬──────┬───────┘
   │      │      │      │      │      │
 Health  Edu  Finance Social Safety  ...
   │
┌──▼──────────────────────────────────────────┐
│              Domain (e.g., Health)           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ Project  │ │ Project  │ │ Project  │    │
│  │ disease  │ │ life-exp │ │ genetics │    │
│  └──────────┘ └──────────┘ └──────────┘    │
└─────────────────────────────────────────────┘
```

## Domain Structure

Each domain contains two functional areas and a set of projects:

```
domains/<domain>/
├── README.md               # domain overview, goals, project list
├── research/               # academic literature, data source catalog, ethics analysis
│   └── README.md
├── development/            # shared tooling, domain-level APIs, integration specs
│   └── README.md
└── projects/
    └── <project>/          # one specific prediction type
        ├── README.md
        ├── research/       # project-specific research
        └── development/    # project-specific implementation
```

## Project Lifecycle

Every project follows this lifecycle regardless of domain:

### 1. Data Collection
- Identify authoritative data sources (public datasets, APIs, research databases)
- Define data schemas and collection pipelines
- Track data provenance and update timestamps
- Validate data quality and flag anomalies

### 2. Prediction
- Select or develop appropriate model(s) for the prediction type
- Train on historical data
- Generate predictions with confidence intervals
- Document model assumptions and limitations

### 3. Self-Correction
- Record all predictions with timestamps and input parameters
- Compare predictions against ground truth as it becomes available
- Compute accuracy metrics (precision, recall, calibration, RMSE, etc.)
- Trigger retraining when accuracy degrades beyond threshold
- Log accuracy history for transparency

### 4. Data Refresh
- AI agent determines optimal refresh frequency based on:
  - Prediction accuracy drift over time
  - Volatility of underlying data sources
  - Domain-specific knowledge of how fast ground truth changes
- Minimum refresh intervals are defined per domain (see domain READMEs)
- Refresh includes re-validation of source reliability

### 5. Information Validation
- Cross-check data sources against each other
- Flag conflicting information for human review
- Track source reliability scores
- Retire unreliable sources

## Research vs Development

Each domain and project separates two work streams:

**Research** covers:
- Literature review and state of the art
- Data source identification and evaluation
- Ethical considerations and bias analysis
- Model selection rationale
- Accuracy benchmarking against existing work

**Development** covers:
- Data collection pipelines
- Model training and evaluation code
- Prediction APIs and interfaces
- Monitoring and alerting
- Documentation and deployment

## Collective Intelligence Layer

The collective intelligence layer is not a simple average. It is a synthesis model that:

- Takes outputs from all domain-level predictions
- Models dependencies between domains (e.g., health ↔ finance ↔ social)
- Generates holistic life-stage predictions
- Weights predictions by historical accuracy
- Identifies gaps where no project yet covers a prediction type

## AGI Framework

The AGI framework sits atop collective intelligence and provides:

- Cross-domain causal reasoning (why does X predict Y across domains)
- Generalization to novel prediction types not explicitly modeled
- Natural language interfaces to the prediction stack
- Feedback loops that improve all underlying models

## Technology Choices

Technology choices are made at the project level — not imposed globally. Projects can use:
- Any open-source ML framework (PyTorch, scikit-learn, JAX, etc.)
- Any programming language
- Any open data format

Shared infrastructure (see [infrastructure/](infrastructure/)) provides optional common tooling for data pipelines, model registries, and accuracy tracking that projects can adopt.

## Accuracy Standards

All projects must:
- Report accuracy metrics alongside predictions
- Define the accuracy threshold below which predictions are flagged as unreliable
- Publish accuracy history publicly
- Never present predictions without confidence levels

## Scalability

The architecture is designed to scale in three dimensions:

1. **Contributor scale** — any number of contributors can work on any project independently
2. **Data scale** — collection pipelines are designed for global-scale data
3. **Geographic scale** — predictions should work across geographies; bias toward any population must be documented and addressed

## Hardware Extension (Future)

When capable robotic systems are available, the development layer of each project will be extended to include hardware interfaces — translating predictions into physical interventions. The research and prediction layers remain unchanged; only the development layer gains new actuators.
