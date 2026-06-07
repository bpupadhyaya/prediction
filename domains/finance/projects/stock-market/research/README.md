# Stock Market Prediction — Research

## Purpose

Answer the foundational questions before committing to a model architecture: what is actually predictable in equity markets, at what horizons, with what signals, and with what honest accuracy?

## Active Research Areas

### Predictability Benchmarks
- [ ] Literature review: ML equity prediction accuracy meta-analysis — what directional accuracy is reported, and does it survive transaction costs?
- [ ] Efficient market hypothesis revisited — which market anomalies have survived post-publication?
- [ ] Time horizon analysis — is 1-day, 1-week, or 1-month most predictable?
- [ ] Market cap effect — are small-cap stocks more predictable than large-cap?

### Factor Investing
- [ ] Fama-French 5-factor model review — value, size, profitability, investment, momentum
- [ ] Factor decay analysis — which factors remain profitable after widespread adoption?
- [ ] Low-volatility anomaly literature
- [ ] Earnings surprise (SUE) predictive power

### Sentiment and Alternative Data
- [ ] Social media sentiment → price prediction accuracy (Reddit, Twitter literature)
- [ ] News NLP for earnings surprise prediction
- [ ] Google Trends as retail attention proxy
- [ ] Insider trading signal predictive value (Form 4 data)

### Model Architectures
- [ ] Transformer models for financial time series (survey)
- [ ] LSTM vs. gradient boosting on OHLCV data — benchmark comparison
- [ ] Walk-forward validation methodology best practices
- [ ] Ensemble methods for financial prediction

### Backtesting Integrity
- [ ] Survivorship bias sources and mitigation
- [ ] Look-ahead bias taxonomy — where it hides in financial ML pipelines
- [ ] Transaction cost models for retail vs. institutional

## Key Research Questions

1. What is the realistic directional accuracy ceiling for daily stock prediction — accounting for transaction costs?
2. Which signals remain predictive in recent data (post-2020), not just historical backtests?
3. Does sentiment add predictive value beyond price and fundamental features?
4. What is the minimum model that beats buy-and-hold on a risk-adjusted basis?
5. How quickly does model alpha decay once signals become widely known?

## Honesty Standard

Financial ML literature is rife with overfitting and survivorship bias. Every paper reviewed must note:
- Whether results survive transaction costs
- Whether out-of-sample period is truly out-of-sample
- Whether the claimed strategy could realistically be executed by a retail investor
- Whether results hold post-publication (many don't)

## Contributing

Add literature reviews as `review_<topic>.md` files. Each review must include a "Does it survive?" section: would a retail investor actually profit from this signal after costs?
