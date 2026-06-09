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

---

## Stock Market Prediction — ADPS Architecture

*Designed 2026-06-08. Supersedes the placeholder GBM model.*

### Overview

The **Adaptive Dynamic Prediction System (ADPS)** is the model architecture for the stock-market project. It is a 7-layer, regime-aware, online-learning system that processes 656 exhaustively-researched factors with dynamic per-second weights. The model is custom-written, bundled with the app, and runs fully on-device.

LLMs are a separate, optional enhancement layer: the user downloads a local LLM (e.g., Llama/Mistral) and once present the app automatically uses it to convert unstructured text (earnings calls, FOMC statements, news) into structured numerical features that feed the ADPS. The LLM does not make predictions; the ADPS does.

### 7-Layer Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Layer 1: Universal Feature Store (656 factors)          │
│  · Feature value · Timestamp · Staleness score          │
│  · Confidence score · Source reliability score          │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────┐
│  Layer 2: Regime Context Engine                          │
│  · Monetary: HIKING | PAUSING | CUTTING                  │
│  · Credit:   EXPANSION | STRESS | CRISIS                 │
│  · Volatility: LOW(<15) | NORMAL(15-25) | ELEVATED | CRISIS│
│  · Yield curve: NORMAL | FLAT | INVERTED | RE-STEEPENING │
│  · Bond-equity correlation: NEGATIVE | POSITIVE          │
└──────────────────────────┬───────────────────────────────┘
                           │ regime vector
┌──────────────────────────▼───────────────────────────────┐
│  Layer 3: Dynamic Weight Generator                       │
│  · Gating neural network: f(regime, news events,         │
│    order flow, feature freshness) → weight vector        │
│  · Weights update on regime changes and live events;     │
│    feature VALUES update every second (price, volume)    │
│  · Old/stale features down-weighted via staleness score  │
└──────────────────────────┬───────────────────────────────┘
                           │ weighted features
┌──────────────────────────▼───────────────────────────────┐
│  Layer 4: Prediction Engine                              │
│  · Regime-aware ensemble: one sub-model per regime       │
│  · Sub-models: GBM / small neural net per regime bucket  │
│  · Output: directional probability + confidence interval │
│  · Walk-forward CV (6-month folds, 2-year min window)   │
└──────────────────────────┬───────────────────────────────┘
                           │ prediction + confidence
┌──────────────────────────▼───────────────────────────────┐
│  Layer 5: Online Learning Engine                         │
│  · Compares predictions vs. observed outcomes            │
│  · Gradient descent on observed results (slow LR)        │
│  · Updates sub-model weights; prevents overfitting       │
│  · Historical predictions stored on-device (user-clearable)│
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────┐
│  Layer 6: LLM Text Pipeline (OPTIONAL — user-downloaded) │
│  · Earnings calls → {tone, hedging, guidance_raised}     │
│  · FOMC statement → {hawkishness_delta, surprise}        │
│  · Geopolitical news → {sector_impact_scores}            │
│  · Output: structured numerical signals → Layer 1 store  │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────┐
│  Layer 7: Extensibility Framework                        │
│  · New parameters start at near-zero weight              │
│  · Earn their weight through online learning             │
│  · No full retraining required to add new signals        │
└──────────────────────────────────────────────────────────┘
```

### 656-Factor Taxonomy

Exhaustive research produced 656 factors across 6 domains (`research/MASTER_FACTOR_TAXONOMY.md`):

| Domain | Count | File |
|--------|-------|------|
| Macroeconomic + Monetary | 136 | `factors_macroeconomic_monetary.md` |
| Corporate Fundamentals + Sector | 145 | `factors_corporate_fundamental_sector.md` |
| Cross-Asset + Global + Flow-of-Funds | 112 | `factors_cross_asset_global_flows.md` |
| Technical + Microstructure | 95 | `factors_technical_microstructure.md` |
| Sentiment + Behavioral + Alternative | 95 | `factors_sentiment_alternative.md` |
| Geopolitical + Political + Regulatory | 73 | `geopolitical_political_regulatory_factors.md` |

Factors fall into 4 roles: continuous time-series features, event/shock signals, regime filter inputs, and LLM-processable text sources.

### Implementation Tiers

**Tier 1 (implement first — 40 free, high-evidence factors):**
- Macro: yield curve, TIPS real yield, HY/IG credit spreads, Fed balance sheet, M2, jobless claims, ISM New Orders, PCE Core, NFCI
- Technical: 6/12-month momentum, 52-week high ratio, Amihud illiquidity, RSI rank, volume ratio, PEAD
- Sentiment: VIX + regime, put/call ratio, COT net positioning, margin debt, Form 4 insider cluster, short interest
- Cross-asset: DXY momentum, gold/equity ratio, copper momentum, USDJPY carry monitor, oil regime, BDI, BTC-equity correlation
- Geopolitical: GPR index, EPU index, pre-FOMC drift flag, buyback blackout calendar

**Tier 2:** Sector flows, VVIX/SKEW, global PMI composite, China credit impulse, calendar effects

**Tier 3:** Full LLM pipeline (earnings NLP, FOMC NLP, geopolitical NLP, 10-K risk factor diff)

### Desktop vs Mobile Split

- **Desktop:** Full 656-feature pipeline, online learning, regime classifier, LLM pipeline, live data ingestion (FRED, Yahoo Finance, CBOE, CFTC, SEC EDGAR)
- **Mobile:** ONNX snapshot of ~40 Tier 1 features, static inference, synced from desktop via GitHub Releases; LLM optional if user downloads model

### Signal Decay

Different factors maintain predictive power for different durations — intraday (order flow, USDJPY) through 1-5 days (earnings surprise, FOMC), 1-4 weeks (ISM, VIX regime), 1-3 months (yield curve, NFCI), up to 3-12 months (momentum, presidential cycle). Staleness scores in the Feature Store down-weight signals past their effective window.

### Key Design Principles

- Model is custom-written, bundled, and shipped with the app — no external ML service calls
- LLMs are user-downloaded, optional, used automatically once present — never bundled
- Prediction is on-demand at the moment the user taps a symbol, using current feature values and weights
- Historical predictions stored on-device; user controls storage and can clear it
- Model evolves via online learning from its own prediction outcomes — no human intervention needed for routine weight updates
