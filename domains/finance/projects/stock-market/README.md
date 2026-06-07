# Stock Market Prediction

**Domain:** Finance
**Status:** scaffold
**Prediction type:** Equity market direction, magnitude, volatility, and risk prediction across individual stocks, sectors, and major indices.

## What This Predicts

Four prediction targets at multiple time horizons (1-day, 1-week, 1-month, 3-month):

1. **Direction** — probability that price moves up or down
2. **Magnitude** — expected return range (e.g., +2% to +5%)
3. **Volatility** — expected price variance (VIX-style for individual stocks)
4. **Drawdown risk** — probability of a loss exceeding a threshold (e.g., >10% loss within 3 months)

Also produces portfolio-level predictions for users with diversified holdings.

## Why This Matters

Individual investors systematically underperform the market due to behavioral biases, information asymmetry, and poor timing. Better predictions — particularly around risk and drawdown — help individuals make more rational allocation decisions without requiring institutional-grade tools.

## Prediction Targets

| Target | Horizon | Output |
|--------|---------|--------|
| Index direction (S&P 500, FTSE, Nikkei, etc.) | 1-day, 1-week | probability up/down |
| Index expected return | 1-month, 3-month | distribution (mean ± std) |
| Sector rotation signal | 1-month | overweight / underweight per sector |
| Individual stock direction | 1-day, 1-week | probability up/down + confidence |
| Individual stock volatility | 1-month | annualized vol estimate |
| Portfolio drawdown risk | 3-month | P(loss > X%) |
| Recession-driven bear market probability | 6-month | probability index falls >20% |

## Key Inputs

### Market / Macro (automated)
| Input | Source | Frequency |
|-------|--------|-----------|
| OHLCV price data | Exchange feeds / Yahoo Finance API | Daily |
| Index constituents and weights | Exchange | Quarterly |
| Earnings reports (EPS, revenue, guidance) | SEC EDGAR, company filings | Quarterly |
| Macro indicators (CPI, unemployment, GDP, Fed rate) | FRED, BLS, BEA | Monthly |
| Yield curve (2Y-10Y spread) | FRED | Daily |
| VIX and options implied volatility | CBOE | Daily |
| Insider trading filings | SEC Form 4 | Daily |
| Short interest data | FINRA | Bi-weekly |
| News sentiment (financial news NLP) | RSS feeds, NewsAPI | Daily |
| Social sentiment (Reddit, Twitter/X) | Reddit API, social APIs | Daily |

### Individual (user-provided, for portfolio predictions)
| Input | Source | Required |
|-------|--------|----------|
| Holdings (ticker, quantity) | self-report | yes |
| Purchase prices | self-report | optional |
| Investment horizon | self-report | yes |
| Risk tolerance | self-report | yes |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Direction probability | 0.0–1.0 | P(price higher at horizon) |
| Expected return distribution | mean ± CI | probability-weighted return range |
| Volatility estimate | annualized % | expected price variance |
| Drawdown risk | percentage | P(loss exceeds threshold) |
| Sector signals | ranked list | relative strength by sector |
| Confidence tier | low/medium/high | based on signal strength and model accuracy |
| Model accuracy (current period) | metric | displayed alongside every prediction |

## Data Sources

**Price and fundamentals:**
- Yahoo Finance API / yfinance — free historical OHLCV + fundamentals
- Alpha Vantage — free tier (limited) for fundamentals
- SEC EDGAR — earnings, 10-K, 10-Q, Form 4 (insider trades)
- FRED (Federal Reserve) — macro indicators (500+ series, all free)
- CBOE — VIX historical data
- FINRA — short interest reports

**Alternative data (free/low-cost):**
- Reddit API (r/wallstreetbets, r/investing) — retail sentiment
- NewsAPI — financial news headlines
- GDELT Project — global news sentiment
- Google Trends — search interest as retail attention proxy

**Research benchmarks:**
- Fama-French factor data (free from Kenneth French's website)
- AQR capital management factor datasets
- Published academic ML-for-finance datasets (Kaggle financial datasets)

## Model Approaches

This is a multi-model ensemble problem. Initial approaches to research:

| Approach | Strengths | Weaknesses |
|----------|-----------|------------|
| ARIMA / GARCH | Volatility modeling, interpretable | Can't capture non-linear patterns |
| Gradient boosting (XGBoost, LightGBM) | Feature importance, tabular data | Doesn't capture temporal patterns natively |
| LSTM / Transformer | Temporal sequence modeling | Needs large data, prone to overfitting |
| Regime-switching models | Captures bull/bear regimes | Complex to fit |
| Ensemble of above | Reduced variance, robust | Harder to interpret |
| Sentiment + price fusion | Captures retail-driven moves | Sentiment data quality varies |

## Research Focus

See [research/](research/) for:
- [ ] Literature review: ML-for-stock-prediction accuracy benchmarks (what is actually achievable?)
- [ ] Factor investing review: Fama-French, momentum, quality, low-volatility factors
- [ ] Sentiment analysis approaches for financial text
- [ ] Benchmark: buy-and-hold vs. prediction-based strategies on historical data
- [ ] Efficient market hypothesis implications — what signals survive transaction costs?

## Development Focus

See [development/](development/) for:
- Data pipeline for daily price and macro ingestion
- Feature engineering (technical indicators, fundamental ratios, macro signals)
- Model training and walk-forward validation framework
- Backtesting engine (accounting for transaction costs and slippage)
- Real-time prediction API

## Self-Correction Mechanism

Stock prediction is uniquely self-defeating: as a model becomes known, arbitrage erodes its edge. Self-correction here is critical and ongoing.

- **Accuracy metric:** Directional accuracy, Sharpe ratio of prediction-based strategy, calibration of probability estimates
- **Ground truth:** Actual price at prediction horizon (always available)
- **Retraining trigger:** Directional accuracy drops below 52% on rolling 60-day window (below 50% means the inverse is predictive), OR calibration error > 0.05
- **Walk-forward validation:** Models are always trained on past data and validated on future data — no look-ahead bias ever
- **Accuracy log:** `development/accuracy_log.json` with rolling metrics by ticker, sector, and time horizon
- **Alpha decay monitoring:** Track whether each signal's predictive power degrades over time

## Refresh Frequency

| Component | Refresh |
|-----------|---------|
| Price data ingestion | Daily (after market close) |
| Macro indicator update | Monthly (follows data release calendar) |
| Sentiment analysis | Daily |
| Model retraining | Weekly (walk-forward roll) |
| Full model rebuild | Monthly or on accuracy trigger |
| Individual predictions | Daily (next-day), Weekly (next-week) |

## Backtesting Standards

All backtests must:
- Use walk-forward validation (no look-ahead bias)
- Account for transaction costs (at minimum 0.1% per trade)
- Account for slippage (assume execution at next-day open, not signal price)
- Report full equity curve, not just Sharpe ratio
- Test across multiple market regimes (bull, bear, sideways, high-vol, low-vol)
- Report maximum drawdown alongside returns

## Ethical Considerations

- **Predictions are probabilistic, not guaranteed** — must be communicated clearly with confidence levels; never present as financial advice
- **Accuracy must be displayed alongside every prediction** — hiding model performance is unacceptable
- **No pump-and-dump potential** — if this project gains scale, coordinated predictions could move small-cap stocks; do not provide predictions for very small-cap or thinly traded stocks
- **Conflicts of interest** — the project and its contributors must not trade on predictions before they are published; embargo period or simultaneous publication required
- **This is not financial advice** — must be explicit in all interfaces; users must accept this
- **Retail vs. institutional disadvantage** — predictions should acknowledge that institutional players have lower transaction costs and faster execution; retail users may not be able to act on short-horizon predictions profitably

## Connection to Other Projects

- Feeds into [retirement-readiness](../retirement-readiness/) — equity market returns are a key input to retirement projection
- Feeds into [financial-distress](../financial-distress/) — portfolio losses can trigger financial distress
- Influenced by [economic-impact](../../macro-population/projects/economic-impact/) — macro recession predictions affect equity bear market risk

## Status Log

| Date | Status | Notes |
|------|--------|-------|
| 2026-06-06 | scaffold | initial setup |
