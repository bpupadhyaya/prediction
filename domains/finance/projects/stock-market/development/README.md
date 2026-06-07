# Stock Market Prediction — Development

## Purpose

Build the data pipelines, feature engineering, model training, backtesting, and prediction serving infrastructure for the stock market prediction project.

## Planned Components

### 1. Data Ingestion Pipeline (Priority: High)
```
src/data/
├── price_feed.py          # daily OHLCV from yfinance / Alpha Vantage
├── macro_feed.py          # FRED indicators (yield curve, CPI, unemployment, Fed rate)
├── fundamentals_feed.py   # SEC EDGAR earnings, P/E, revenue, guidance
├── sentiment_feed.py      # news headlines + Reddit + Google Trends
├── insider_feed.py        # SEC Form 4 insider trades
├── short_interest_feed.py # FINRA bi-weekly short interest
└── scheduler.py           # daily pipeline orchestration
```

### 2. Feature Engineering
```
src/features/
├── technical.py           # RSI, MACD, Bollinger, ATR, volume ratios, momentum
├── fundamental.py         # P/E, P/B, EV/EBITDA, earnings surprise, guidance delta
├── macro.py               # yield curve slope, VIX regime, inflation regime
├── sentiment.py           # news NLP scores, Reddit mention velocity, Google Trends
├── regime.py              # bull/bear/sideways regime classification
└── feature_store.py       # unified feature matrix assembly
```

### 3. Walk-Forward Validation Framework
```
src/validation/
├── walk_forward.py        # rolling train/test split with no look-ahead
├── backtester.py          # transaction-cost-aware strategy backtesting
├── metrics.py             # Sharpe, Sortino, max drawdown, directional accuracy, calibration
└── bias_checker.py        # survivorship bias and look-ahead bias detection
```

### 4. Model Training
```
src/models/
├── baseline.py            # buy-and-hold + simple moving average crossover baselines
├── gbm_model.py           # XGBoost / LightGBM on tabular features
├── lstm_model.py          # sequence model for price time series
├── sentiment_model.py     # BERT-based news sentiment classifier
├── ensemble.py            # weighted ensemble of above
└── regime_model.py        # HMM or threshold-based regime classifier
```

### 5. Accuracy Tracking
```
development/
├── accuracy_log.json      # rolling directional accuracy by ticker/sector/horizon
├── alpha_decay_log.json   # signal predictive power over time
└── backtest_results/      # equity curves and metrics per model version
```

### 6. Prediction API
```
src/api/
├── predict.py             # /predict endpoint — returns prediction + confidence + accuracy
└── portfolio.py           # /portfolio endpoint — portfolio-level risk metrics
```

## Development Standards

- **Walk-forward only** — never train on future data; dates must be enforced programmatically
- **Transaction costs always included** — every backtest uses at minimum 0.1% per trade
- **Accuracy displayed with every prediction** — model's current rolling accuracy must accompany every output
- **No small-cap pump risk** — predictions are only served for stocks with >$1B market cap or major indices

## Dependency Stack (Planned)

```python
# Core
pandas, numpy, scipy

# Market data
yfinance, fredapi, sec-edgar-downloader

# ML
scikit-learn, xgboost, lightgbm, torch (for LSTM)

# NLP / Sentiment
transformers (HuggingFace), praw (Reddit), newsapi-python

# Backtesting
backtrader OR custom walk-forward engine

# Serving
fastapi, uvicorn
```

## Status

All planned. Development start gate: research phase must establish which signals are worth building pipelines for.

## Getting Started

Start with `src/data/price_feed.py` — the price pipeline is the foundation everything else depends on. Build it with caching (don't re-download data you already have) and a clean date-indexed interface that makes look-ahead bias structurally impossible.
