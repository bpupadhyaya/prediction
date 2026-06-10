# Master Factor Taxonomy — Stock Market Prediction Model
*Generated 2026-06-08 via parallel research agents*

---

## Overview

**Total factors identified: 656** across 6 major domains.
This is the comprehensive input universe for the prediction model.
Not all 656 will be used — this is the research inventory from which the model feature set is selected.

---

## Domain Summary

| Domain | Factors | File |
|--------|---------|------|
| Macroeconomic + Monetary | 136 | factors_macroeconomic_monetary.md |
| Corporate Fundamentals + Sector-Specific | 145 | factors_corporate_fundamental_sector.md |
| Cross-Asset + Global Markets + Flow-of-Funds | 112 | factors_cross_asset_global_flows.md |
| Technical + Market Microstructure | 95 | factors_technical_microstructure.md |
| Sentiment + Behavioral + Alternative Data | 95 | factors_sentiment_alternative.md |
| Geopolitical + Political + Regulatory | 73 | geopolitical_political_regulatory_factors.md |
| **TOTAL** | **656** | |

---

## How Factors Enter the Model

Factors are not all equal in how they feed the model. They fall into 4 distinct roles:

### Role 1: Continuous Time-Series Features
*Fed directly into the model as numerical feature columns*
- Technical indicators (momentum, RSI, MAs, volatility, volume)
- Macro time series (yield curve, VIX, credit spreads, DXY, PMIs)
- Fundamental metrics (P/E, ROE, earnings growth, short interest)
- Cross-asset signals (gold/equity ratio, carry trade index, BDI)
- Sentiment scores (AAII bull/bear, put/call ratio, NFCI)

### Role 2: Event/Shock Signals
*Binary or magnitude-scaled flags triggered by discrete events*
- Earnings surprise (magnitude + direction)
- Fed rate decision surprise vs. market expectation
- Geopolitical shock (GPR index spike)
- Short-seller report publication
- Index addition/deletion
- Insider cluster buy/sell
- Credit rating change

### Role 3: Regime Filters / Model Switchers
*Determine which sub-model or feature weights to apply*
- Yield curve regime (normal / flat / inverted / re-steepening)
- Monetary policy regime (hiking / pausing / cutting)
- Credit cycle regime (expansion / stress / crisis)
- Bond-equity correlation regime (negative = diversification works / positive = inflation shock)
- VIX regime (low <15 / normal 15-25 / elevated 25-35 / crisis >35)
- GPR regime (baseline / elevated geopolitical risk)

### Role 4: LLM-Processable (Text → Structured Signal)
*Text inputs that the LLM converts to numerical signals for the model*
- Earnings call transcripts (tone, hedging language, Q&A dynamics)
- FOMC statements + minutes (hawkishness score)
- CEO/CFO language in 8-K filings
- Short-seller research reports
- Analyst report language and estimate revision rationale
- Geopolitical news (GDELT events)
- Supply chain stress signals from multiple transcripts
- FDA/regulatory press releases
- G7/G20 communiqués
- Congressional records (policy sentiment)
- 10-K risk factor changes year-over-year

---

## Free vs. Subscription Data

### Tier A — Free, Public, Daily/Weekly
*Implement immediately — no cost*
```
FRED series: DGS2, DGS10, T10Y2Y, T10Y3M, BAMLC0A0CM, BAMLH0A0HYM2,
             FEDFUNDS, WALCL, SOFR, M2SL, DTWEXBGS, DEXJPUS, DEXUSEU,
             CPIAUCSL, PCEPILFE, UNRATE, PAYEMS, ICSA, T10YIE, DFII10,
             STLFSI, NFCI, DCOILWTICO, PCOPPUSDM, GOLDAMGBD228NLBM, USREC

Yahoo Finance: ^VIX, ^GSPC, ^NDX, ^RUT, ^N225, ^GDAXI, BTC-USD, GC=F, CL=F
               Sector ETFs: XLK, XLE, XLF, XLV, XLU, XLP, XLY, XLI, XLB
               Country ETFs: EEM, EWJ, FXI, EWG

CBOE: VIX term structure, SKEW (^SKEW), VVIX (^VVIX), Put/Call ratio
CFTC: Commitment of Traders (COT) — S&P 500 futures positioning (weekly)
FINRA: Margin debt (monthly), Short interest (bi-monthly)
SEC EDGAR: Form 4 insider transactions (daily)
CME FedWatch: Fed funds futures probabilities
ISM: Manufacturing + Services PMI (monthly)
BLS: CPI, PPI, NFP, JOLTS (monthly)
EIA: Oil inventory, rig count (weekly)
Baker Hughes: Rig count (weekly)
Baltic Exchange: Baltic Dry Index (daily)
GDELT: Geopolitical event data (daily)
GPR Index: Caldara-Iacoviello geopolitical risk (monthly)
EPU Index: Baker-Bloom-Davis policy uncertainty (monthly)
policyuncertainty.com: Free download
NY Fed: GDPNow, recession probability model, term premium (ACM)
Atlanta Fed: GDPNow (weekly)
CoinGecko API: Crypto market cap, stablecoin supply (daily, free API)
```

### Tier B — Free with Lag or Limited Detail
*Useful but with caveats*
- AAII sentiment survey (weekly, some delay)
- Conference Board LEI, Consumer Confidence (monthly)
- University of Michigan sentiment (monthly, partial free)
- OECD CLI (monthly, free download)
- CPB World Trade Monitor (monthly, free)
- SIA semiconductor billings (monthly, free)
- MBA mortgage applications (weekly, free headline)
- EPFR fund flows (summary in financial media weekly)
- Caixin PMI (free headline, subscription for full)
- NBS China PMI (free)

### Tier C — Subscription Required
*Highest institutional alpha but requires paid access*
- Credit card transaction data (Second Measure, Bloomberg Second Measure): $$$
- Satellite data — parking lots, oil tanks, ports (Planet Labs, Kayrros): $$$
- Options analytics — GEX, IV surface (SpotGamma, OptionMetrics): $$
- CDS spreads real-time (Markit/ICE): $$
- EPFR full fund flow data: $$
- Prime brokerage L/S exposure (GS, MS clients only): not available
- Bloomberg terminal (many factors above): $$$$

---

## Implementation Priority Tiers

### Tier 1: Implement First (Free + High Academic Evidence)
*These 40 factors alone would dramatically improve current model*

**Macro/Monetary (10):**
- 2Y-10Y yield curve spread (T10Y2Y)
- Real 10Y TIPS yield (DFII10)
- HY credit spread (BAMLH0A0HYM2)
- IG credit spread (BAMLC0A0CM)
- Fed balance sheet weekly change (WALCL)
- M2 growth YoY (M2SL)
- Initial jobless claims (ICSA)
- ISM Manufacturing New Orders subindex
- PCE Core YoY (PCEPILFE)
- Chicago Fed NFCI financial conditions (NFCI)

**Technical (8):**
- 6-month and 12-month momentum (cross-sectional rank)
- 52-week high ratio
- Low-volatility anomaly (historical 20-day vol)
- Amihud illiquidity ratio (from OHLCV)
- RSI cross-sectional percentile rank
- Volume ratio (today vs. 20-day avg)
- Post-Earnings Announcement Drift (PEAD)

**Sentiment/Positioning (8):**
- VIX level + regime
- VIX term structure (contango vs. backwardation)
- CBOE equity put/call ratio
- CFTC COT net speculative positioning (S&P futures)
- FINRA margin debt month-over-month change
- Form 4 insider cluster buy signal
- Short interest % of float + change

**Cross-Asset (7):**
- DXY dollar index momentum
- Gold/equity ratio trend
- Copper price momentum ("Dr. Copper")
- USDJPY rate-of-change (carry unwind monitor)
- Oil price regime (supply vs. demand shock classification)
- BDI Baltic Dry trend
- Bitcoin-equity 30-day correlation

**Geopolitical/Policy (4):**
- GPR Index level and change (FRED)
- EPU Index level and change
- FOMC meeting calendar (pre-FOMC drift flag)
- Earnings blackout calendar (buyback window open/close)

**Fundamental (3):**
- Earnings revision momentum (analyst estimate changes)
- Earnings surprise magnitude + direction
- Short interest days-to-cover

### Tier 2: Add After Tier 1 Validated (Free with More Engineering)
- Sector ETF relative flows (XLU+XLV vs. XLK+XLY ratio)
- Semiconductor book-to-bill ratio
- Global PMI composite trend
- China credit impulse (PBOC ASF data)
- VVIX level (volatility-of-vol warning signal)
- CBOE SKEW index
- Russell reconstitution calendar
- S&P 500 index addition/deletion events
- Presidential cycle year indicator
- Options expiration calendar effects (weekly, monthly, quarterly)
- Variance Risk Premium (VIX² - realized vol²)

### Tier 3: LLM Pipeline (Implement After Core Model Works)
- Earnings call NLP → tone score, hedging language score, Q&A surprise
- FOMC statement NLP → hawkishness delta vs. prior statement
- CEO/CFO 8-K language → confidence/uncertainty score
- Short-seller report flag + magnitude estimate
- Geopolitical news NLP via GDELT → sector impact score
- 10-K risk factor change detector (year-over-year diff)
- Supply chain stress: cross-transcript NLP across sector peers

---

## Regime-Switching Architecture

The model should NOT be a single model. It should be a **regime-aware ensemble**:

```
Regime Classifier
├── Monetary regime: HIKING | PAUSING | CUTTING
├── Credit regime: EXPANSION | STRESS | CRISIS
├── Vol regime: LOW (<15) | NORMAL (15-25) | ELEVATED (>25) | CRISIS (>35)
├── Yield curve regime: NORMAL | FLAT | INVERTED | RE-STEEPENING
└── Bond-equity correlation: NEGATIVE (diversification) | POSITIVE (inflation)

→ Each regime combination activates a different sub-model
→ Sub-models have different feature weights and even different feature sets
→ Output: weighted ensemble of applicable sub-models
```

This directly mirrors what Renaissance Technologies discovered: markets have multiple regimes where the same signal works differently.

---

## LLM Role in the Architecture

```
Text Inputs (unstructured)
    ↓
LLM Processing Layer (on-device, user-downloaded model)
    ↓
Structured numerical signals
    ↓
Feeds into main prediction model as additional features

Examples:
- Earnings call → {tone_score: 0.72, hedging_intensity: 0.31, guidance_raised: 1}
- FOMC statement → {hawkishness_delta: +0.15, surprise_vs_prior: 0.08}
- Geopolitical news → {sector_impact: "energy:+0.6, defense:+0.8, airlines:-0.5"}
```

The LLM does NOT make the prediction. It converts unstructured text into structured features that the ONNX model uses. Clean separation of concerns.

---

## Signal Decay Matrix

Different factors maintain predictive power for different durations:

| Timeframe | Best Factors |
|-----------|-------------|
| Intraday | Order flow delta, USDJPY rate-of-change, GEX, VIX intraday |
| 1-5 days | Pre-FOMC drift, earnings surprise, short-seller reports, USDJPY carry alert |
| 1-4 weeks | ISM PMI, NFP, JOLTS, IG/HY spreads, VIX regime, put/call ratio |
| 1-3 months | Yield curve, NFCI, housing starts, M2 growth, earnings revision momentum |
| 3-12 months | 6/12-month momentum, SLOOS lending standards, GPR regime, presidential cycle |
| >12 months | Yield curve inversion duration, debt-to-GDP, demographic flows, ESG structural |

---

## Data Sources Summary

| Source | URL | Cost | Update Freq |
|--------|-----|------|-------------|
| FRED (St. Louis Fed) | fred.stlouisfed.org | Free | Daily/Monthly |
| Yahoo Finance | finance.yahoo.com | Free | Real-time/Daily |
| CBOE | cboe.com/tradable_products/vix | Free | Daily |
| CFTC COT | cftc.gov/MarketReports/CommitmentsofTraders | Free | Weekly (Fri) |
| FINRA | finra.org/investors/learn-to-invest/advanced-investing/short-sale-statistics | Free | Bi-monthly |
| SEC EDGAR Form 4 | efts.sec.gov/LATEST/search-index?q=%22form-type%22%3A%224%22 | Free | Daily |
| CME FedWatch | cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html | Free | Real-time |
| ISM | ismworld.org | Free (headline) | Monthly |
| EIA | eia.gov | Free | Weekly/Monthly |
| Baker Hughes | bakerhughes.com/rig-count | Free | Weekly |
| Baltic Exchange | balticexchange.com | Free (BDI) | Daily |
| GDELT | gdeltproject.org | Free | Daily |
| GPR Index | matteoiacoviello.com/gpr.htm | Free | Monthly |
| EPU Index | policyuncertainty.com | Free | Monthly |
| NY Fed | newyorkfed.org/research/policy_and_analysis | Free | Various |
| Atlanta Fed GDPNow | atlantafed.org/cqer/research/gdpnow | Free | Weekly |
| CoinGecko API | coingecko.com/en/api | Free tier | Daily |
| Caixin PMI | caixin.com | Free (headline) | Monthly |
| NBS China | stats.gov.cn | Free | Monthly |
| CPB Netherlands | cpb.nl/en/worldtrademonitor | Free | Monthly |

---

## Next Steps

1. **Build data ingestion pipeline** — FRED API, Yahoo Finance, CBOE, CFTC, SEC EDGAR
2. **Implement regime classifier** — yield curve + VIX + credit spread regimes
3. **Build Tier 1 feature set** — 40 factors above
4. **Train regime-aware ensemble** — one sub-model per major regime combination
5. **Add LLM text pipeline** — earnings calls, FOMC, geopolitical
6. **Export to ONNX** — bundle for mobile deployment
7. **Add Tier 2 factors** — after Tier 1 validated
8. **Continuous signal decay monitoring** — track which factors are working, kill what isn't
