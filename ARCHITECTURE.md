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

The **Adaptive Dynamic Prediction System (ADPS)** is the model architecture for the stock-market project. It is a 9-layer, regime-aware, online-learning system that processes 656 exhaustively-researched factors with dynamic per-second weights. The model is custom-written, bundled with the app, and runs fully on-device.

LLMs are a separate, optional enhancement layer: the user downloads a local LLM (e.g., Llama/Mistral) and once present the app automatically uses it to convert unstructured text (earnings calls, FOMC statements, news) into structured numerical features that feed the ADPS. The LLM does not make predictions; the ADPS does.

Two design imperatives beyond prediction accuracy:

1. **Radical transparency** — the user can always see exactly which factors drove a prediction, what their weights were, and why. No black-box output.
2. **User-directed refinement** — the user can inject knowledge the model lacks: paste a news URL, type a context note, boost or suppress specific factors. The model incorporates this in real time and learns from whether the user's override was correct.

### 9-Layer Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Layer 9: User Guidance Interface                        │◄─── user input (news URL,
│  · Free-text context input                               │     text note, factor
│  · URL ingestion → LLM extracts signal                   │     boost/suppress)
│  · Per-factor weight override (boost / suppress)         │
│  · User context injected as high-confidence features     │
│  · User's overrides tracked; feed Layer 5 when correct   │
└──────────────────────────┬───────────────────────────────┘
                           │ user-injected signals
┌──────────────────────────▼───────────────────────────────┐
│  Layer 1: Universal Feature Store (656 factors)          │
│  · Feature value · Timestamp · Staleness score          │
│  · Confidence score · Source reliability score          │
│  · Source tag: SYSTEM | LLM | USER_OVERRIDE             │
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
│    order flow, feature freshness, user overrides)        │
│  · User-overridden weights take precedence               │
│  · Old/stale features down-weighted via staleness score  │
└──────────────────────────┬───────────────────────────────┘
                           │ weighted features
┌──────────────────────────▼───────────────────────────────┐
│  Layer 4: Prediction Engine                              │
│  · Regime-aware ensemble: one sub-model per regime       │
│  · Sub-models: GBM / small neural net per regime bucket  │
│  · Output: directional probability + confidence interval │
│  · Also emits: per-feature SHAP importance scores        │
│  · Walk-forward CV (6-month folds, 2-year min window)   │
└──────────────────────────┬───────────────────────────────┘
                           │ prediction + confidence + SHAP scores
┌──────────────────────────▼───────────────────────────────┐
│  Layer 5: Online Learning Engine                         │
│  · Compares predictions vs. observed outcomes            │
│  · Gradient descent on observed results (slow LR)        │
│  · When user override was correct: reinforces that signal│
│  · Historical predictions stored on-device (user-clearable)│
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────┐
│  Layer 6: LLM Text Pipeline (OPTIONAL — user-downloaded) │
│  · System sources: earnings calls, FOMC, geopolitical    │
│  · User sources: any URL or text the user pastes         │
│  · Output: structured numerical signals → Layer 1 store  │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────┐
│  Layer 7: Extensibility Framework                        │
│  · New parameters start at near-zero weight              │
│  · Earn their weight through online learning             │
│  · No full retraining required to add new signals        │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────┐
│  Layer 8: Transparency & Explainability Engine           │
│  · Consumes SHAP scores from Layer 4                     │
│  · Groups factors by domain (macro, technical, etc.)     │
│  · Generates plain-English rationale per factor          │
│  · Flags user overrides that are active                  │
│  · Exposes structured data to the UI (see UI below)      │
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

### Layer 8: Transparency & Explainability UI

Every prediction ships with a full "prediction receipt" that is surfaced to the user in the app. The user can never be left wondering *why* the model said what it said.

**What is shown:**

```
┌─ AAPL Prediction: BULLISH 73% confidence ──────────────┐
│                                                         │
│  [Why this prediction?]  ← tappable, opens detail sheet│
│                                                         │
│  ▼ Macro Factors           (drove +18% of this call)   │
│    · Yield curve: NORMAL           weight 0.14  ✓ fresh │
│    · HY credit spread: tight       weight 0.11  ✓ fresh │
│    · NFCI financial conditions: −  weight 0.09  ✓ fresh │
│    · M2 growth: 4.1% YoY          weight 0.07  ⚠ 3d old│
│                                                         │
│  ▶ Technical Factors       (drove +22% of this call)   │
│  ▶ Sentiment Factors       (drove +15% of this call)   │
│  ▶ Cross-Asset Factors     (drove +12% of this call)   │
│  ▶ Geopolitical Factors    (drove −8% of this call)    │
│  ▶ User Overrides          (1 active — "tariff news")  │
│                                                         │
│  Active regime: MONETARY=PAUSING · VOL=NORMAL           │
│  Model accuracy on past 90 predictions: 61%             │
└─────────────────────────────────────────────────────────┘
```

**UI implementation:**
- Bottom sheet / modal panel triggered by "Why this prediction?" button on prediction card
- Factor groups are collapsible sections; each shows top 3-5 contributing factors with weight, value, freshness indicator, and a one-line plain-English explanation
- Staleness warnings shown inline (⚠ 3d old) so user can judge data quality
- Active regime displayed prominently — helps user understand which sub-model fired
- User overrides shown in their own section so user knows their input was counted
- Historical accuracy shown so user can calibrate trust ("model was right 61% of the time on similar conditions")
- "Full factor list" link shows all 656 factors with their current values and weights in a searchable, filterable list

**Data contract from Layer 4:**
```json
{
  "ticker": "AAPL",
  "direction": "BULLISH",
  "probability": 0.73,
  "horizon": "1w",
  "regime": {"monetary": "PAUSING", "vol": "NORMAL", "yield_curve": "NORMAL"},
  "top_factors": [
    {"id": "T10Y2Y", "domain": "macro", "value": 0.42, "weight": 0.14,
     "direction_contribution": "+", "staleness_days": 0, "explanation": "Yield curve is normal — no recession signal"},
    ...
  ],
  "user_overrides_active": [
    {"label": "tariff news", "source_url": "...", "injected_signal": 0.65}
  ],
  "model_accuracy_90d": 0.61
}
```

---

### Layer 9: User Guidance Interface

The user has knowledge the model doesn't. This layer captures it and injects it into the prediction pipeline in real time.

**Input modalities:**

| Mode | What user does | How it works |
|------|---------------|--------------|
| **Paste a URL** | User pastes a news link, earnings report URL, SEC filing, etc. | LLM (if available) extracts structured signal; without LLM, keyword extraction; injected into Feature Store with source=USER |
| **Free-text note** | "Company just lost a $2B contract" / "CEO sold all shares last week" | LLM converts to sentiment/magnitude signal; keyword fallback |
| **Factor boost/suppress** | Slider per factor group: "I think geopolitical risk is higher than the model thinks" | Multiplies that domain's weight by user-specified scalar (0.5× to 3×) |
| **Factor pin** | "Always weight short interest heavily for this ticker" | Ticker-specific weight floor; persists across predictions |
| **Override source link** | "Use this data source instead of the default" | Data URL added to ingestion queue for that factor |

**Lifecycle of a user input:**

```
User pastes URL or types note
        ↓
Layer 6 (LLM) extracts structured signal
        ↓
Injected into Layer 1 Feature Store
  · source_tag = USER_OVERRIDE
  · confidence = 0.9 (user input presumed intentional)
  · staleness = 0 (fresh at injection time)
        ↓
Layer 3 Weight Generator sees USER_OVERRIDE tag
  → applies user-specified weight or default boost
        ↓
Layer 4 Prediction Engine runs with user signal included
        ↓
Layer 8 Transparency UI shows user override in its own section
        ↓
When outcome known: Layer 5 Online Learning records
  · "user override X → outcome Y"
  · If user was right: increase that signal type's base weight
  · If user was wrong: decrease (slowly, with floor to avoid overfit)
```

**UI implementation:**
- Persistent "Add context" button on every prediction card and stock detail screen
- In-app bottom sheet with 4 tabs: Paste URL / Write note / Adjust weights / Manage overrides
- Active overrides shown as chips on the prediction card (e.g., "📎 1 user signal active")
- "Manage overrides" screen shows all active user inputs per ticker — user can delete, edit, or mark as expired
- Weight adjustment is per-domain (not per-factor) to avoid overwhelming the user; power users can expand to factor-level
- No override is permanent by default — each has an expiry (default: 7 days) that user can extend

---

### Desktop vs Mobile Split

- **Desktop:** Full 656-feature pipeline, online learning, regime classifier, LLM pipeline, live data ingestion (FRED, Yahoo Finance, CBOE, CFTC, SEC EDGAR)
- **Mobile:** ONNX snapshot of ~40 Tier 1 features, static inference, synced from desktop via GitHub Releases; LLM optional if user downloads model

---

### Data Persistence Requirements (all platforms)

#### Core Rule
**Prediction history and user guidance signals must survive indefinitely as long as the app is installed.**
Only a full app uninstall may erase this data. App upgrades must never touch existing data.

#### Desktop
- **DB:** DuckDB file at `~/.prediction/stock-market/market.duckdb`
- **Upgrade safety:** `init_db()` uses `CREATE TABLE IF NOT EXISTS` — never drops or truncates tables
- **Migration pattern:** `_safe_alter()` wraps every `ALTER TABLE` in try/except, so adding columns to existing DBs is safe
- **User-initiated clear:** not yet implemented — add a "Clear prediction history" option in Settings (future)

#### iOS (feature sync — implement when porting desktop features to mobile)
- **DB:** SQLite via GRDB, stored in `Application Support/<bundle-id>/` (NOT `Documents/`)
  - `Application Support` is not user-visible and is excluded from iCloud backup by default — set `isExcludedFromBackup = false` on the DB file so iCloud DOES back it up (user's prediction history is valuable)
  - Using `Documents/` would expose it in Files app — avoid
- **Upgrade safety:** use GRDB migrations (`migrator.registerMigration("v1") { db in ... }`) — each migration runs exactly once and is recorded in `grdb_migrations` table; never use destructive migrations
- **Schema evolution:** only additive changes (new tables, new nullable columns with defaults) — never `DROP TABLE`, never remove columns
- **Uninstall warning:** iOS cannot intercept uninstall. Instead:
  - Settings screen must show: "⚠️ Uninstalling this app will permanently delete all prediction history and guidance signals stored on this device."
  - Offer iCloud backup toggle in Settings so user can protect data
- **Prediction history:** store one row per prediction call in a `predictions` table (same schema as desktop). The `/predict` screen "View History" button opens a sheet showing the same chart + table as desktop.
- **User signals:** stored in `user_signals` table, same schema as desktop, persist across upgrades
- **Data clear in-app:** provide "Clear all prediction history" in Settings → destructive action alert with two-step confirmation ("Are you sure? This cannot be undone.")

#### Android (feature sync — implement when porting desktop features to mobile)
- **DB:** Room database in app's private data directory (`/data/data/<package>/databases/`)
  - This directory is wiped on uninstall but survives upgrades, sideloads, and OS updates
  - Enable Auto Backup (`android:allowBackup="true"`, `android:fullBackupContent`) so Google One Backup includes the DB
- **Upgrade safety:** Room `Migration` objects — define `Migration(oldVersion, newVersion)` for every schema change; never use `fallbackToDestructiveMigration()` in production
- **Schema evolution:** same rule as iOS — additive only; never drop tables or columns
- **Uninstall warning:**
  - Android cannot intercept uninstall natively. Instead:
    - Settings screen must show: "⚠️ Uninstalling this app or clearing app data in Android Settings will permanently delete all prediction history and guidance signals."
    - Offer "Export history to CSV" in Settings as a manual backup option
  - **Clearing app data** (Settings → Apps → Clear Data) also wipes the DB — this is a platform constraint; the warning in-app is the only protection
- **Prediction history:** same `predictions` table via Room entity; "View History" opens a BottomSheet with the same chart (MPAndroidChart or Vico) + LazyColumn table
- **User signals:** `user_signals` Room entity, same lifecycle as predictions

#### Feature Parity Checklist (desktop → mobile sync)
When implementing mobile prediction history, ensure:
- [ ] `predictions` table created in first DB migration (v1)
- [ ] Every `predict()` call writes a row (ticker, horizon, timestamp, direction, probability, expected_return_low/high, volatility, regime_label)
- [ ] "View History" button on prediction card opens sheet/modal
- [ ] History chart: Prob(UP) % over time, green/red tint zones, one point per day (last of day)
- [ ] History table: date, direction badge, confidence %, expected return range, regime label
- [ ] Horizon picker (1d / 1w / 1m) and days filter (30 / 60 / 90 / 180) in history view
- [ ] Settings screen: uninstall warning text, data clear option with confirmation
- [ ] App upgrade tested: existing DB rows survive, new columns added cleanly via migration

---

### Signal Decay

Different factors maintain predictive power for different durations — intraday (order flow, USDJPY) through 1-5 days (earnings surprise, FOMC), 1-4 weeks (ISM, VIX regime), 1-3 months (yield curve, NFCI), up to 3-12 months (momentum, presidential cycle). Staleness scores in the Feature Store down-weight signals past their effective window.

### Key Design Principles

- Model is custom-written, bundled, and shipped with the app — no external ML service calls
- LLMs are user-downloaded, optional, used automatically once present — never bundled
- Prediction is on-demand at the moment the user taps a symbol, using current feature values and weights
- Historical predictions stored on-device; user controls storage and can clear it
- Model evolves via online learning from its own prediction outcomes — no human intervention needed for routine weight updates
- **Every prediction is fully explainable** — the user can always see which factors drove it, with what weight, and how fresh the data was; no black-box output ever
- **User knowledge always wins** — the user can inject context the model lacks (news, URLs, notes, weight overrides) and that input is treated as high-confidence signal; the model learns from whether the user was right
- **Trust is earned incrementally** — model accuracy is surfaced per-ticker and per-regime so the user can decide how much weight to give any individual prediction
