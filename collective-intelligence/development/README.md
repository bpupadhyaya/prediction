# Collective Intelligence — Development

## Purpose

Build the software infrastructure that ingests domain-level prediction outputs and synthesizes them into the holistic collective intelligence layer.

## Planned Components

### 1. Domain Output Interface (Priority: High)
Standardize what each domain project outputs so collective intelligence can consume them uniformly:
- Prediction value(s)
- Confidence intervals
- Prediction window
- Last updated timestamp
- Accuracy metrics
- Domain and project identifiers

**File:** `interfaces/domain_output_schema.json`

### 2. Feature Alignment Layer
- Normalize predictions to comparable temporal windows
- Align confidence intervals across domains
- Handle missing domain outputs gracefully

**Directory:** `src/feature_alignment/`

### 3. Interaction Modeling
- Learn cross-domain interactions from training data
- Model mediation (A causes C through B)
- Handle bidirectional interactions (health ↔ finance)

**Directory:** `src/interaction_models/`

### 4. Holistic Life Model
- Integrate all aligned, interaction-modeled features
- Produce trajectory predictions across all domains simultaneously
- Identify compounding risks

**Directory:** `src/holistic_model/`

### 5. Evaluation Pipeline
- Measure accuracy of collective predictions vs. domain-only predictions
- Track whether cross-domain synthesis adds value
- Log accuracy history

**Directory:** `src/evaluation/`

## Status

All components planned — no implementation yet. Collective intelligence development is gated on domain projects reaching evaluation status.

## Getting Started

If you want to contribute, start with the Domain Output Interface specification — defining a clean, stable contract between domains and this layer is the most important prerequisite.
