# Technical, Price-Based, and Market Microstructure Factors
# Exhaustive Catalog for Equity Return Prediction

**Research area:** Factor investing, signal engineering
**Status:** Reference catalog — v1.0 (2026-06-08)
**Scope:** 95 factors across 12 categories
**Purpose:** Canonical input list for feature engineering and factor research phases

---

## How to Use This Document

Each factor entry contains:
- **Factor ID** — unique reference code for engineering pipelines
- **Description** — how it is computed
- **Optimal timeframe** — where predictive power is strongest based on literature
- **Signal direction** — what the factor predicts (continuation / reversal / vol expansion, etc.)
- **Evidence** — strength of academic/practitioner evidence
- **Data availability** — what is needed to compute it (all assumed available via yfinance + CBOE + FINRA + SEC EDGAR)
- **Survival note** — does the signal survive transaction costs and post-publication decay?

Evidence ratings: **Strong** = survives out-of-sample, replicated, survives transaction costs. **Moderate** = survives in academic setting, mixed real-world. **Weak** = data-mined, does not survive costs or fades post-publication.

---

## Category 1: Price Momentum (Cross-Sectional and Time-Series)

### F001 — 1-Day Return (Overnight + Intraday)
**Description:** Raw return from prior close to current close. Two sub-components: overnight return (close-to-open) and intraday return (open-to-close) carry different information.
**Optimal timeframe:** Signal for next 1–5 days
**Signal direction:** Short-term reversal (for liquid large-caps). Continuation at weekly horizon for small-caps.
**Evidence:** Moderate. Jegadeesh (1990) documents 1-month reversal. Overnight vs. intraday decomposition (Lou, Polk, Skouras 2019) shows overnight returns contain informed trading; intraday reflects noise-driven reversals.
**Data availability:** OHLCV (daily) — standard
**Survival note:** Reversal in large-caps is largely arbitraged. Residual edge in small-caps is real but transaction costs eat most of it.

---

### F002 — 1-Week Momentum (5-Day Return)
**Description:** Return over prior 5 trading days, excluding the most recent day (to avoid 1-day reversal contamination).
**Optimal timeframe:** Predicts next 5–10 days
**Signal direction:** Continuation
**Evidence:** Moderate. Part of the broader momentum phenomenon. Shorter than canonical momentum; less studied independently.
**Data availability:** OHLCV (daily)
**Survival note:** Partially survives for small/mid-caps. Marginal after costs for large-caps.

---

### F003 — 1-Month Momentum (21-Day Return)
**Description:** Return over prior 21 trading days, skip most recent day.
**Optimal timeframe:** Next 5–21 days
**Signal direction:** Continuation
**Evidence:** Moderate-Strong. The short end of the Jegadeesh-Titman (1993) momentum horizon. Reversal tendency begins to appear beyond this.
**Data availability:** OHLCV (daily)
**Survival note:** Survives costs in smaller stocks; marginal for S&P 500 constituents.

---

### F004 — 3-Month Momentum (63-Day Return)
**Description:** Return over prior 63 trading days, skip 1 day.
**Optimal timeframe:** Next 1–3 months
**Signal direction:** Continuation
**Evidence:** Strong. Canonical intermediate momentum range. Jegadeesh & Titman (1993, 2001), Fama & French (1996). Factor decay is documented but momentum remains one of the most robust anomalies.
**Data availability:** OHLCV (daily)
**Survival note:** Survives after costs in academic replication. Post-2000 Sharpe lower but still positive. Crashes in momentum reversals (2009, 2020 March-April).

---

### F005 — 6-Month Momentum (126-Day Return)
**Description:** Return over prior 126 trading days, skip 1 day. Core Jegadeesh-Titman formation period.
**Optimal timeframe:** Next 1–6 months
**Signal direction:** Continuation
**Evidence:** Strong. The most replicated horizon. Fama-French 5-factor model includes MOM factor at this horizon. Survives international replication (Rouwenhorst 1998, Asness et al. 2013).
**Data availability:** OHLCV (daily)
**Survival note:** Best risk-adjusted among momentum signals. Drawdown during momentum crashes is severe (−40% in 2009). Must be combined with crash protection.

---

### F006 — 12-Month Momentum (252-Day Return)
**Description:** Return over prior 252 trading days, skip 1 month (skip most recent 21 days to avoid short-term reversal contamination).
**Optimal timeframe:** Next 1–12 months
**Signal direction:** Continuation up to ~12 months; reversal beyond
**Evidence:** Strong. Standard in factor investing. Carhart (1997) 4-factor model. Also called "price momentum" or "52-week high momentum."
**Data availability:** OHLCV (daily)
**Survival note:** Still survives post-publication. Best when combined with low-volatility overlay to avoid momentum crash risk.

---

### F007 — 24-Month Momentum (504-Day Return)
**Description:** Return over prior 504 trading days, skip 1 month.
**Optimal timeframe:** Next 3–12 months
**Signal direction:** Continuation, but reversal tendency strengthens
**Evidence:** Moderate. At 2-year horizon the mean-reversion literature (De Bondt and Thaler 1985) begins to dominate. Best used as part of a combined momentum-reversal framework.
**Data availability:** OHLCV (daily)
**Survival note:** Borderline. Long-formation momentum merges with value; combined factor is stronger than either alone.

---

### F008 — 52-Week High Ratio
**Description:** Current price divided by the 52-week high. Stocks near their 52-week high outperform.
**Optimal timeframe:** Next 1–6 months
**Signal direction:** Continuation (high ratio = bullish)
**Evidence:** Strong. George & Hwang (2004): 52-week high is a better momentum predictor than raw past return. Behavioral anchor effect — investors anchor to 52-week high as resistance, creating predictable breakout patterns.
**Data availability:** OHLCV (daily)
**Survival note:** Robust. Outperforms raw return momentum in several studies. Survives transaction costs for daily-rebalanced portfolios only marginally; monthly rebalancing works better.

---

### F009 — Price Distance from All-Time High (ATH Ratio)
**Description:** Current price / all-time high price. Stocks near ATH have different momentum characteristics than those far below.
**Optimal timeframe:** 1–3 months
**Signal direction:** Stocks near ATH tend to continue; extreme ATH drawdown stocks show reversal at long horizons
**Evidence:** Moderate. Extension of 52-week high literature. Less studied but used in practitioner factor frameworks.
**Data availability:** Full OHLCV history required
**Survival note:** Weak standalone; useful as regime indicator combined with other signals.

---

### F010 — Cross-Sectional Momentum Rank
**Description:** Percentile rank of a stock's return relative to a universe (e.g., S&P 500 constituents) over a given lookback period. More robust than raw return because it removes market-wide effects.
**Optimal timeframe:** 3–12 months
**Signal direction:** High rank = buy, low rank = sell
**Evidence:** Strong. Standard implementation in AQR, Dimensional, and other factor investing frameworks. Cross-sectional rank removes beta bias and is more diversified than absolute return.
**Data availability:** OHLCV for all universe members
**Survival note:** Strong. Cross-sectional implementation is more robust than time-series momentum. Key factor in most live factor investing products.

---

### F011 — Residual Momentum (Idiosyncratic Momentum)
**Description:** Momentum calculated on residuals after removing market and factor exposures (alpha component only). Blitz, Huij & Martens (2011).
**Optimal timeframe:** 6–12 months
**Signal direction:** Continuation
**Evidence:** Strong. Outperforms raw momentum in both return and Sharpe. Less prone to momentum crashes because market-wide reversals cancel out.
**Data availability:** OHLCV + Fama-French factor returns (free from Ken French website)
**Survival note:** Best-in-class momentum variant. Still requires monthly rebalancing minimum.

---

## Category 2: Mean Reversion Factors

### F012 — 3–5 Year Reversal (Long-Run Reversal)
**Description:** Return over prior 3–5 years. Losers outperform winners at this horizon.
**Optimal timeframe:** Predicts next 12–36 months
**Signal direction:** Reversal (past losers outperform)
**Evidence:** Strong. De Bondt & Thaler (1985). Fama & French (1996) attributes this to value factor overlap. True reversal vs. value exposure debate is unresolved.
**Data availability:** Full OHLCV history (5+ years)
**Survival note:** Moderate. Much of the return is concentrated in January (tax-loss selling reversal). Net of transaction costs and controlling for size/value, weaker than reported.

---

### F013 — Short-Term Reversal (1-Month)
**Description:** Most recent 1-month return (no skip). Stocks with strong prior-month returns underperform next month.
**Optimal timeframe:** Next 5–21 days
**Signal direction:** Reversal
**Evidence:** Strong. Jegadeesh (1990). Robust across markets and time periods. Mechanism: bid-ask bounce, liquidity provision pricing, inventory adjustment.
**Data availability:** OHLCV (daily)
**Survival note:** Mostly arbitraged away for large-caps by liquidity providers. Real edge only for patient market makers, not retail investors.

---

### F014 — Overnight Gap Reversal
**Description:** Large overnight gap (open much higher/lower than prior close) tends to reverse intraday.
**Optimal timeframe:** Intraday (open to close on gap day)
**Signal direction:** Reversal of gap direction
**Evidence:** Moderate. Large body of practitioner literature. Gap fill rates for common gaps are ~70%+. News-driven gaps (earnings, macro) reverse less reliably.
**Data availability:** OHLCV (intraday or daily OHLC)
**Survival note:** Moderate. Works better for index ETFs (SPY, QQQ) than individual stocks. Transaction costs reduce edge significantly for small gaps.

---

### F015 — Intraday Mean Reversion (High-Frequency)
**Description:** Deviations from VWAP during the day revert. Stocks trading significantly below VWAP in first two hours tend to recover toward VWAP.
**Optimal timeframe:** Intraday (minutes to hours)
**Signal direction:** Reversion to VWAP
**Evidence:** Moderate. Well-documented in market microstructure literature. Foundation of statistical arbitrage strategies.
**Data availability:** Intraday OHLCV (1-min or 5-min bars) — requires non-standard data feed
**Survival note:** Real but requires low-latency execution. Retail investors cannot capture reliably.

---

## Category 3: Moving Averages

### F016 — Simple Moving Average (SMA) 10-Day
**Description:** 10-day equally-weighted average of closing prices. Price / SMA10 ratio or price crossing SMA10.
**Optimal timeframe:** 1–5 days
**Signal direction:** Price above SMA = bullish; crossover = trend initiation signal
**Evidence:** Moderate. Most commonly tested MA. Older academic studies (Brock, Lakonishok, LeBaron 1992) find significant performance. More recent studies (Faber 2007) validate at monthly timescale.
**Data availability:** OHLCV (daily)
**Survival note:** Weak at daily timescale, moderate at weekly/monthly. Mostly useful as regime filter, not standalone signal.

---

### F017 — SMA 20-Day
**Description:** 20-day SMA. One of the most widely watched levels by market participants.
**Optimal timeframe:** 5–20 days
**Signal direction:** Price above = bullish trend; crossover signals
**Evidence:** Moderate. Self-fulfilling component due to widespread monitoring. Reflexivity argument (Soros): because everyone watches it, it works.
**Data availability:** OHLCV (daily)
**Survival note:** Weak standalone. Used as input to multi-signal frameworks. Best as regime filter.

---

### F018 — SMA 50-Day
**Description:** 50-day SMA. Most commonly cited trend filter for medium-term.
**Optimal timeframe:** 1–2 months
**Signal direction:** Continuation when price stays above; reversal when decisively broken
**Evidence:** Moderate. Widely studied. Meb Faber's 10-month SMA (200-day) is the most validated equivalent. 50-day is weaker.
**Data availability:** OHLCV (daily)
**Survival note:** Moderate at monthly rebalancing. Transaction costs consume much of the edge at daily rebalancing.

---

### F019 — SMA 200-Day (Meb Faber Moving Average)
**Description:** 200-day (10-month) SMA. Most studied long-term trend filter. Buy when price > SMA200; sell to cash when price < SMA200.
**Optimal timeframe:** 1–12 months
**Signal direction:** Trend following / drawdown reduction
**Evidence:** Strong. Faber (2007), subsequent replications across multiple asset classes. Primary value is drawdown reduction (avoids major bear markets) not return enhancement.
**Data availability:** OHLCV (daily)
**Survival note:** Strong for drawdown reduction. Return over buy-and-hold is modest but risk-adjusted performance is substantially better. Tax drag is a cost.

---

### F020 — Exponential Moving Average (EMA) 9-Day
**Description:** Exponentially weighted MA with 9-day span. More sensitive to recent prices than SMA.
**Optimal timeframe:** 1–5 days
**Signal direction:** Trend direction, faster signals than SMA
**Evidence:** Weak standalone. Used primarily as component in MACD and other oscillators.
**Data availability:** OHLCV (daily)
**Survival note:** Weak standalone. Value is as component in multi-signal frameworks.

---

### F021 — EMA 12/26 Crossover (MACD Basis)
**Description:** Crossover of 12-day and 26-day EMAs. Forms the MACD signal.
**Optimal timeframe:** 2–6 weeks
**Signal direction:** Bullish crossover (12 crosses above 26); bearish crossover
**Evidence:** Moderate. MACD crossover is one of the most-tested technical rules. Evidence in academic studies is positive but small. Hudson, Dempsey & Keasey (1996), Brock et al. (1992).
**Data availability:** OHLCV (daily)
**Survival note:** Moderate. Works better in trending markets. Fails in choppy/ranging markets. Best used with trend regime filter.

---

### F022 — VWAP (Volume-Weighted Average Price)
**Description:** Cumulative (price × volume) / cumulative volume, reset daily at open. Widely used institutional benchmark.
**Optimal timeframe:** Intraday to daily
**Signal direction:** Price below VWAP = potential value; above = momentum. Institutional buy orders target below VWAP.
**Evidence:** Moderate. Well-established execution benchmark. Predictive value of daily VWAP deviations for next-day returns is moderate.
**Data availability:** Intraday data required for precise VWAP; approximated from OHLCV daily bars
**Survival note:** Real intraday mean reversion toward VWAP exists. Closing price / daily VWAP ratio has modest next-day predictive power.

---

### F023 — Anchored VWAP (AVWAP)
**Description:** VWAP computed from a significant price anchor point (earnings date, 52-week low, major pivot). Price relationship to AVWAP provides dynamic support/resistance.
**Optimal timeframe:** Days to weeks after anchor event
**Signal direction:** Support/resistance dynamic around AVWAP level
**Evidence:** Moderate (practitioner evidence). Used by institutional traders as execution reference. Academic study limited.
**Data availability:** Requires intraday data and identification of anchor dates
**Survival note:** Useful as execution benchmark; predictive value for returns is not formally established.

---

### F024 — Hull Moving Average (HMA)
**Description:** HMA = WMA(2 × WMA(n/2) − WMA(n), sqrt(n)). Reduces lag of standard MAs while maintaining smoothness.
**Optimal timeframe:** 10–30 days
**Signal direction:** Trend direction with lower false-signal rate than SMA
**Evidence:** Weak (formal academic evidence). Practitioner evidence suggests lower lag benefits in trending markets.
**Data availability:** OHLCV (daily)
**Survival note:** Marginally better than SMA/EMA in trending markets; not significantly better in academic testing.

---

### F025 — Kaufman Adaptive Moving Average (KAMA)
**Description:** MA that adapts its speed based on the Efficiency Ratio (directional change / total path length). Moves quickly in trending markets, slowly in choppy markets.
**Optimal timeframe:** 10–30 days depending on market regime
**Signal direction:** Trend direction, regime-aware
**Evidence:** Moderate. Kaufman (1995). Better noise filtering than fixed-period MAs in volatile markets. Few independent academic replications.
**Data availability:** OHLCV (daily)
**Survival note:** Moderate. Adaptive nature is genuinely useful in regime-switching markets. Most useful as input to regime-detection layer.

---

### F026 — Moving Average Convergence/Divergence (MACD)
**Description:** MACD line = EMA(12) − EMA(26). Signal line = EMA(9) of MACD. Histogram = MACD − Signal. Three sub-signals: line crossover, zero-line crossover, histogram divergence.
**Optimal timeframe:** 2–8 weeks
**Signal direction:** Bullish when MACD > Signal and rising; bearish when MACD < Signal and falling
**Evidence:** Moderate. One of the most studied oscillators. Positive but small returns to MACD signals. Works better in trending than mean-reverting regimes.
**Data availability:** OHLCV (daily)
**Survival note:** Weak to moderate. Transaction costs erode most of the edge. More useful as trend confirmation than primary signal.

---

### F027 — Moving Average Envelope
**Description:** Upper/lower bands at fixed percentage above/below a MA (e.g., SMA20 ± 5%). Price touching bands = potential reversion.
**Optimal timeframe:** 10–30 days
**Signal direction:** Reversion when outside bands; trend when staying inside
**Evidence:** Weak. Less studied than Bollinger Bands. Concept is sound but fixed-percentage bands are inferior to volatility-adjusted bands.
**Data availability:** OHLCV (daily)
**Survival note:** Weak standalone. Use Bollinger Bands instead.

---

## Category 4: Oscillators

### F028 — Relative Strength Index (RSI) 14-Day
**Description:** RSI = 100 − 100/(1 + RS), where RS = avg 14-day up-closes / avg 14-day down-closes. Range 0–100. Classic overbought >70, oversold <30.
**Optimal timeframe:** 5–21 days
**Signal direction:** Oversold (<30) = buy signal; overbought (>70) = sell signal for mean reversion; divergence with price = trend reversal signal
**Evidence:** Moderate. Well-studied. Oversold signals show positive returns at 5–10 day horizon in multiple studies. Overbought signals are less reliable (momentum stocks stay overbought). Divergence signals are practitioner-validated but less formally studied.
**Data availability:** OHLCV (daily)
**Survival note:** Moderate. Oversold reversal works well in bear market rallies. Overbought signals fade in trending markets. Best at 2-day and 14-day periods.

---

### F029 — RSI 2-Day (Connors RSI Variant)
**Description:** Very short-period RSI. Extreme readings (<10 or >90) signal high-probability short-term reversals. Developed by Larry Connors.
**Optimal timeframe:** 1–5 days
**Signal direction:** Extreme oversold = 5-day buy; extreme overbought = 5-day sell
**Evidence:** Moderate. Connors (2009) documents high historical accuracy rates. Works best on index ETFs (SPY, QQQ). Requires timing against longer trend.
**Data availability:** OHLCV (daily)
**Survival note:** Moderate for index ETFs. Works when market is above 200-day MA. Dangerous in strong trends (adds to losers against the trend).

---

### F030 — Stochastic Oscillator (%K and %D)
**Description:** %K = 100 × (Close − Lowest Low 14) / (Highest High 14 − Lowest Low 14). %D = 3-day SMA of %K. Crossovers and extreme levels (80/20) are signals.
**Optimal timeframe:** 5–15 days
**Signal direction:** Oversold (<20) reversal; overbought (>80) reversal; crossovers
**Evidence:** Moderate. Studied in multiple markets. Slightly weaker than RSI in most head-to-head comparisons. Strong practitioner following.
**Data availability:** OHLCV (daily)
**Survival note:** Similar to RSI. Weak standalone, useful in multi-factor frameworks.

---

### F031 — Commodity Channel Index (CCI)
**Description:** CCI = (Typical Price − SMA of Typical Price) / (0.015 × Mean Deviation). Typical Price = (H + L + C) / 3. Range usually −200 to +200.
**Optimal timeframe:** 14–20 days
**Signal direction:** Above +100 = overbought/momentum; below −100 = oversold. Divergence signals trend reversals.
**Evidence:** Moderate. Lambert (1980). Originally for commodities but applied to equities. Similar evidence base to RSI and Stochastic.
**Data availability:** OHLCV (daily)
**Survival note:** Similar to RSI. One study advantage: captures commodity-like cyclical stocks (energy, materials) better than RSI.

---

### F032 — Williams %R
**Description:** %R = (Highest High − Close) / (Highest High − Lowest Low) × −100. Inverted stochastic. Range −100 to 0.
**Optimal timeframe:** 10–14 days
**Signal direction:** −80 to −100 = oversold (reversal signal); −20 to 0 = overbought
**Evidence:** Moderate. Larry Williams (1973). Essentially equivalent to Stochastic oscillator mathematically. Similar evidence base.
**Data availability:** OHLCV (daily)
**Survival note:** Weak standalone. Correlation with %D stochastic is very high; limited independent information.

---

### F033 — Ultimate Oscillator
**Description:** Weighted average of three RSI-like oscillators over 7, 14, and 28 periods. Reduces false divergence signals from single-period oscillators.
**Optimal timeframe:** 14–28 days
**Signal direction:** Divergence + oscillator crossing 30/70 levels
**Evidence:** Weak. Williams (1985). The multi-timeframe weighting is theoretically sound but academic evidence is limited.
**Data availability:** OHLCV (daily)
**Survival note:** Weak. Multi-period construction does reduce whipsaw vs. single-period oscillators but independent predictive evidence is thin.

---

### F034 — Rate of Change (ROC) / Momentum Oscillator
**Description:** ROC = (Close / Close[n periods ago] − 1) × 100. Simplest momentum measure.
**Optimal timeframe:** 5–63 days depending on lookback
**Signal direction:** Positive = bullish; negative = bearish; direction change = signal
**Evidence:** Moderate. The raw return underlying all momentum factors. Statistical significance is similar to price momentum.
**Data availability:** OHLCV (daily)
**Survival note:** Identical evidence base to momentum factors (F001–F011). ROC is just unnormalized momentum.

---

### F035 — Chande Momentum Oscillator (CMO)
**Description:** CMO = 100 × (Sum of Up-days − Sum of Down-days) / (Sum of Up-days + Sum of Down-days) over n periods. Range −100 to +100.
**Optimal timeframe:** 14–20 days
**Signal direction:** Extreme readings signal reversals; center-line crossovers signal trend changes
**Evidence:** Weak. Chande (1994). Mathematically related to RSI but different scaling. Limited independent academic evidence.
**Data availability:** OHLCV (daily)
**Survival note:** Weak. No strong independent evidence over RSI or Stochastic.

---

### F036 — Aroon Oscillator
**Description:** Aroon Up = 100 × (25 − Days since 25-day high) / 25. Aroon Down = 100 × (25 − Days since 25-day low) / 25. Aroon Oscillator = Aroon Up − Aroon Down.
**Optimal timeframe:** 25 days
**Signal direction:** Positive oscillator = uptrend; negative = downtrend; crossover = trend change
**Evidence:** Weak-Moderate. Chande (1995). Directly measures whether recent high/lows are occurring — conceptually linked to momentum. Limited formal academic study.
**Data availability:** OHLCV (daily)
**Survival note:** Moderate intuition, weak evidence. Useful as trend classification input.

---

## Category 5: Volume-Based Indicators

### F037 — On-Balance Volume (OBV)
**Description:** Cumulative volume added on up-days, subtracted on down-days. OBV divergence from price signals accumulation/distribution.
**Optimal timeframe:** 5–30 days
**Signal direction:** OBV rising ahead of price = accumulation (bullish); OBV falling while price holds = distribution (bearish)
**Evidence:** Moderate. Granville (1963). Widely used in practice. Academic evidence is mixed — Balsara (2007) finds marginal predictive value. Volume-price divergence is theoretically grounded in informed trading.
**Data availability:** OHLCV with volume (daily)
**Survival note:** Moderate. Value as divergence detector; weak as momentum signal. Contaminated by index rebalancing and ETF flows.

---

### F038 — Volume Price Trend (VPT)
**Description:** VPT = VPT[prev] + Volume × (Close − Close[prev]) / Close[prev]. Like OBV but weights by magnitude of price change.
**Optimal timeframe:** 10–30 days
**Signal direction:** Divergence with price signals reversal
**Evidence:** Moderate. Slight theoretical improvement over OBV. Limited head-to-head academic studies.
**Data availability:** OHLCV with volume (daily)
**Survival note:** Similar to OBV. Marginal improvement in theory; no strong empirical advantage.

---

### F039 — Accumulation/Distribution Line (A/D)
**Description:** A/D = A/D[prev] + (Close Location Value × Volume). CLV = ((Close − Low) − (High − Close)) / (High − Low). Measures where in the day's range the stock closed.
**Optimal timeframe:** 10–30 days
**Signal direction:** Rising A/D = accumulation; falling = distribution. Divergence with price = reversal signal.
**Evidence:** Moderate. Chaikin (1980). CLV construction is more nuanced than OBV. Captures intraday buyer/seller pressure.
**Data availability:** OHLCV with volume (daily)
**Survival note:** Moderate. Better intraday price location capture than OBV. Still subject to noise from institutional rebalancing.

---

### F040 — Chaikin Money Flow (CMF)
**Description:** CMF = Sum(A/D Volume, n) / Sum(Volume, n) over typically 20 days. Normalized version of A/D.
**Optimal timeframe:** 20 days
**Signal direction:** CMF > 0 = buying pressure; CMF < 0 = selling pressure; crossover of zero line
**Evidence:** Moderate. Chaikin. Normalized construction makes cross-sectional comparison meaningful.
**Data availability:** OHLCV with volume (daily)
**Survival note:** Moderate. Cross-sectional CMF ranking has predictive value in some studies.

---

### F041 — Volume Profile (Point of Control, Value Area)
**Description:** Distribution of volume at each price level over a time window. Point of Control (POC) = highest volume price level. Value Area = price range containing 70% of volume. Price at POC = magnetic level.
**Optimal timeframe:** Days to weeks (daily volume profile) or long-term (yearly profile)
**Signal direction:** Price returning to POC tends to stall; break below/above POC with volume is directional
**Evidence:** Moderate (practitioner evidence). Foundation of Market Profile theory (Steidlmayer, 1985). Limited formal academic study.
**Data availability:** Intraday data required for precise volume profile; approximated from daily data
**Survival note:** Used by professional futures traders. Approximations from daily data lose significant information.

---

### F042 — Relative Volume (RVOL)
**Description:** Current volume / average volume for same time period over past N days. RVOL > 2 indicates unusual activity.
**Optimal timeframe:** Intraday or daily
**Signal direction:** High RVOL on up-day = institutional accumulation; high RVOL on down-day = distribution. Breakouts on high RVOL are more likely to hold.
**Evidence:** Moderate. Volume-confirms-price is a fundamental principle of technical analysis. Academic evidence supports: high-volume breakouts perform better than low-volume breakouts (Gervais, Kaniel & Mingelgrin 2001).
**Data availability:** OHLCV with volume (daily)
**Survival note:** Moderate. High-volume breakouts do outperform in the short term. Effect is more pronounced for smaller, less liquid stocks.

---

### F043 — Dollar Volume Turnover
**Description:** Daily dollar volume = Close × Volume. Normalized by market cap = turnover ratio. High turnover signals attention and often precedes return.
**Optimal timeframe:** 5–21 days
**Signal direction:** Abnormal turnover precedes price moves (direction depends on context)
**Evidence:** Moderate. Gervais et al. (2001): high-volume weeks followed by strong returns. Huang & Heian (2010).
**Data availability:** OHLCV with volume + market cap (daily)
**Survival note:** Moderate. Turnover as liquidity measure is well-established. Attention effect is real; direction is noisy.

---

### F044 — Volume-Weighted Momentum
**Description:** Price momentum weighted by relative volume during the formation period. Days with high volume count more.
**Optimal timeframe:** 21–63 days
**Signal direction:** Continuation
**Evidence:** Moderate. Lee & Swaminathan (2000) show high-volume past winners outperform. Volume interacts with price momentum significantly.
**Data availability:** OHLCV with volume (daily)
**Survival note:** Moderate. Lee-Swaminathan enhancement is well-replicated. Adds value over raw momentum.

---

## Category 6: Volatility Indicators

### F045 — Average True Range (ATR) 14-Day
**Description:** ATR = average of True Range over 14 days. True Range = max(H−L, |H−C[prev]|, |C[prev]−L|). Measures volatility in price-units.
**Optimal timeframe:** 10–20 days
**Signal direction:** Rising ATR = increasing volatility (often bearish regime); falling ATR = compression (often precedes breakout)
**Evidence:** Strong. Wilder (1978). ATR is the foundation of multiple volatility-based systems. Normalized ATR (ATR/Price) is comparable across stocks.
**Data availability:** OHLCV (daily)
**Survival note:** ATR itself is not a return predictor but is essential for position sizing and stop placement. ATR compression signals are moderate return predictors.

---

### F046 — Bollinger Bands (BBands)
**Description:** Upper/Lower bands = SMA(20) ± 2 × StdDev(20). Bandwidth = (Upper − Lower) / Middle. %B = (Price − Lower) / (Upper − Lower).
**Optimal timeframe:** 10–30 days
**Signal direction:** %B < 0 (below lower band) = oversold reversal signal; %B > 1 (above upper band) = overbought. Bandwidth squeeze followed by expansion = breakout signal.
**Evidence:** Moderate. Bollinger (1992). %B and Bandwidth are two distinct signals. Bollinger Band squeeze (low bandwidth) is moderately predictive of subsequent volatility expansion. Walk-forward studies show marginal positive returns.
**Data availability:** OHLCV (daily)
**Survival note:** Moderate. Squeeze-to-expansion signal survives better than mean-reversion signals within bands. Direction of expansion from squeeze is hard to predict.

---

### F047 — Keltner Channels
**Description:** Middle = EMA(20). Upper/Lower = EMA(20) ± 2 × ATR(10). Less affected by gap distortions than Bollinger Bands.
**Optimal timeframe:** 10–20 days
**Signal direction:** Breakout above/below channel = trend initiation; return inside channel from breach = failure
**Evidence:** Moderate. Chester Keltner (1960), revised by Linda Bradford Raschke. ATR-based channel is more stable than std-dev-based BBands.
**Data availability:** OHLCV (daily)
**Survival note:** Similar to Bollinger Bands. Combination of both (BBands outside Keltner = squeeze) is well-studied.

---

### F048 — Historical Volatility (HV) / Close-to-Close Volatility
**Description:** Annualized standard deviation of daily log returns over N days (typically 20 or 60). HV20, HV60 are standard.
**Optimal timeframe:** 20–60 day lookback; predicts next 20–60 days
**Signal direction:** Low HV predicts higher forward returns (low-volatility anomaly); high HV predicts lower risk-adjusted returns
**Evidence:** Strong. Low-volatility anomaly documented in Ang et al. (2006), Baker et al. (2011). Stocks with low idiosyncratic volatility outperform on a risk-adjusted basis. Contradicts CAPM.
**Data availability:** OHLCV (daily)
**Survival note:** Strong. One of the most robust anomalies. Survives transaction costs and has been replicated internationally.

---

### F049 — Realized Volatility (Parkinson, Garman-Klass)
**Description:** Parkinson: vol = sqrt(1/(4n ln2) × sum(ln(H/L)^2)). Garman-Klass: uses OHLC for more efficient estimator. More efficient than close-to-close using intraday range.
**Optimal timeframe:** 10–20 day lookback
**Signal direction:** Same as HV but more precise estimate
**Evidence:** Strong. Parkinson (1980), Garman & Klass (1980). More statistically efficient estimators than close-to-close. Better vol forecasting.
**Data availability:** OHLCV (daily — uses High/Low)
**Survival note:** Strong as volatility estimator. Use wherever vol estimation is needed.

---

### F050 — Volatility of Volatility (Vol-of-Vol)
**Description:** Standard deviation of the rolling daily realized volatility series. High vol-of-vol indicates unstable regime.
**Optimal timeframe:** 60-day rolling window of daily HV
**Signal direction:** High vol-of-vol = regime instability = higher uncertainty = risk-off signal
**Evidence:** Moderate. Used in options pricing and risk management. As return predictor for equities, evidence is limited but negative relationship with forward returns is intuitive.
**Data availability:** OHLCV (daily) — computed from HV series
**Survival note:** Useful as regime indicator; weak standalone return predictor.

---

### F051 — Implied Volatility (IV) from Options
**Description:** Implied volatility backed out from option prices (Black-Scholes). Forward-looking. VIX is the index-level IV. Stock-level IV is available for optionable stocks.
**Optimal timeframe:** 1-month forward (standard 30-day IV)
**Signal direction:** High IV = fear premium = contrarian buy signal at extremes; IV crush after earnings = well-known risk
**Evidence:** Strong. Volatility risk premium (selling options at high IV) is one of the most documented risk premia. High IV stocks subsequently underperform on realized vol (overpaying for uncertainty).
**Data availability:** Options data (CBOE) — requires options chain data, not just OHLCV
**Survival note:** Strong. IV risk premium is real and exploitable but requires options trading access.

---

### F052 — IV/HV Ratio (Volatility Risk Premium Proxy)
**Description:** IV30 / HV20 ratio. When IV >> HV, options are expensive relative to realized vol. Contrarian indicator.
**Optimal timeframe:** 20–30 days
**Signal direction:** IV/HV > 1.5 = options overpriced = mean-reversion buy for realized vol; stock-level: high IV/HV stocks underperform
**Evidence:** Strong. Volatility risk premium literature. Carr & Wu (2009). IV consistently exceeds HV on average — the premium exists.
**Data availability:** Options data (IV) + OHLCV (HV)
**Survival note:** Strong as volatility premium signal. Return prediction from IV/HV is moderate.

---

### F053 — Volatility Ratio (Short-term vs. Long-term)
**Description:** HV10 / HV60 ratio. When short-term vol exceeds long-term, market is in elevated stress state.
**Optimal timeframe:** 10–60 day comparison
**Signal direction:** Ratio > 1.5 = acute volatility regime = mean reversion more likely; ratio < 0.7 = complacency = potential vol expansion ahead
**Evidence:** Moderate. Used as regime filter in quantitative strategies. Academic evidence is limited but practitioners widely use it.
**Data availability:** OHLCV (daily)
**Survival note:** Moderate as regime detector. Weak as standalone directional signal.

---

## Category 7: Market Breadth Indicators

### F054 — Advance/Decline Line (A/D Line)
**Description:** Cumulative sum of (advances − declines) each day across NYSE or S&P 500. Divergence from index is key signal.
**Optimal timeframe:** Weeks to months for divergence signals
**Signal direction:** A/D Line making new highs while index lags = healthy broad rally (bullish). A/D Line failing to confirm index highs = negative divergence = caution.
**Evidence:** Strong. One of the oldest and most respected breadth indicators. Colby (2003). Negative divergence preceded all major bear markets historically.
**Data availability:** Market breadth data from NYSE/NASDAQ (daily) — available from free sources (StockCharts API, Barchart)
**Survival note:** Strong as risk indicator. Not a precise timing tool but excellent for identifying market vulnerability.

---

### F055 — Advance/Decline Ratio
**Description:** (Advances / Declines) on a given day. Extreme readings signal overbought/oversold breadth.
**Optimal timeframe:** 1–5 days
**Signal direction:** Extreme low ratio (<0.2) = panicked selling = bounce signal; extreme high ratio (>5) = euphoria = short-term top signal
**Evidence:** Moderate. Well-studied as short-term sentiment indicator. Extreme readings are contrarian.
**Data availability:** Daily breadth data (advances, declines count)
**Survival note:** Moderate. Works for identifying short-term oversold bounces. Less useful for directional prediction.

---

### F056 — New 52-Week Highs / New 52-Week Lows
**Description:** Count of stocks making new 52-week highs vs. new 52-week lows. Net new highs = new highs − new lows.
**Optimal timeframe:** Weekly reading, predicts 1–4 weeks
**Signal direction:** Expanding new highs = healthy bull market. Divergence (index up but new highs shrinking) = distribution phase. High new lows = panic = contrarian buy.
**Evidence:** Strong. Classic breadth indicator. Norman Fosback's High-Low Logic Index is a well-studied variant. Multiple academic confirmations.
**Data availability:** 52-week high/low lists from NYSE/NASDAQ daily
**Survival note:** Strong as market health indicator. Confirms or denies index trends.

---

### F057 — McClellan Oscillator
**Description:** Difference between 19-day and 39-day EMAs of (advances − declines). Oscillates around zero. McClellan Summation Index = cumulative sum.
**Optimal timeframe:** 5–20 days (oscillator); weeks to months (summation index)
**Signal direction:** Above zero = breadth expanding (bullish); below zero = breadth contracting. Extreme readings are contrarian.
**Evidence:** Moderate-Strong. Sherman and Marian McClellan (1969). Well-documented in technical analysis literature. Academic study limited but practitioner adoption is very high.
**Data availability:** Daily advances/declines
**Survival note:** Strong for market-level breadth assessment. Less useful for individual stock prediction.

---

### F058 — Arms Index (TRIN — Trading Index)
**Description:** TRIN = (Advances/Declines) / (Advance Volume/Decline Volume). TRIN > 1 = more volume in declining stocks (bearish); TRIN < 1 = more volume in advancing stocks (bullish). Inverted.
**Optimal timeframe:** Intraday to 1-day
**Signal direction:** TRIN > 2 = panic selling = short-term reversal buy signal; TRIN < 0.5 = euphoric buying = short-term exhaustion
**Evidence:** Moderate. Richard Arms (1967). Well-studied short-term sentiment measure. Extreme TRIN readings reliably identify panic episodes.
**Data availability:** Daily advances/declines + advance/decline volume
**Survival note:** Moderate for identifying extreme market stress points. Less useful as continuous predictor.

---

### F059 — Percent of Stocks Above Moving Average
**Description:** Percentage of S&P 500 stocks trading above their 50-day or 200-day SMA. Breadth confirmation of index trend.
**Optimal timeframe:** Weeks to months
**Signal direction:** Above 80% = overbought breadth; below 20% = washout. Divergence from index = warning.
**Evidence:** Strong. Widely used institutional breadth measure. Martin Pring, various technical texts. Empirically well-supported as market health metric.
**Data availability:** Requires constituent-level OHLCV for index universe
**Survival note:** Strong as regime indicator. Extreme readings (>90% or <10%) are highly predictive of short-term reversals.

---

### F060 — Zweig Breadth Thrust
**Description:** 10-day EMA of (Advancing Issues / (Advancing + Declining Issues)). A thrust from below 0.40 to above 0.615 within 10 days historically signals new bull market.
**Optimal timeframe:** 10-day formation; signal lasts months to years
**Signal direction:** Thrust confirmed = powerful buy signal
**Evidence:** Moderate-Strong. Martin Zweig (1986). Rare signal (< 20 occurrences since 1945) but historically very bullish — large 1-year forward returns in all instances.
**Data availability:** Daily advances/declines
**Survival note:** Strong when it occurs (very rare). Cannot be primary strategy due to infrequency.

---

## Category 8: Market Microstructure

### F061 — Bid-Ask Spread (Absolute and Relative)
**Description:** Ask price − Bid price (absolute). Relative spread = (Ask − Bid) / Midpoint. Measures transaction cost and liquidity.
**Optimal timeframe:** Real-time to daily average
**Signal direction:** Widening spreads = liquidity withdrawal = increased risk. Stocks with persistently narrow spreads have better return predictability (less noise).
**Evidence:** Strong. Amihud & Mendelson (1986), Brennan & Subrahmanyam (1996). Illiquidity premium is well-documented. Stocks with wide spreads earn higher returns (compensation for illiquidity risk).
**Data availability:** Level 1 quotes (requires real-time or end-of-day quote data) — not in standard free OHLCV
**Survival note:** Strong for illiquidity premium research. Real-time spread data requires premium data subscription.

---

### F062 — Amihud Illiquidity Ratio
**Description:** ILLIQ = |Return| / Dollar Volume. Monthly ILLIQ = average of daily |r|/dolvol. Stocks with high ILLIQ are less liquid.
**Optimal timeframe:** Monthly ILLIQ computed from daily data; predicts next 1–12 months
**Signal direction:** High ILLIQ stocks earn a liquidity premium (higher expected returns)
**Evidence:** Strong. Amihud (2002). One of the most robust equity anomalies. Survives transaction costs because illiquid stocks are typically held longer.
**Data availability:** OHLCV with volume (daily) — fully computable from standard data
**Survival note:** Strong. The illiquidity premium is real. However, the most illiquid stocks are often untradeable for institutional investors; small-fund or retail advantage.

---

### F063 — Order Book Depth / Market Depth
**Description:** Total bid and ask volume at multiple price levels in the order book. Depth imbalance = (bid depth − ask depth) / (bid depth + ask depth).
**Optimal timeframe:** Real-time
**Signal direction:** Positive imbalance (more bids) = short-term upward pressure; negative = downward pressure
**Evidence:** Strong. Glosten & Milgrom (1985). Depth imbalance is predictive of next 1–30 minute returns in multiple studies.
**Data availability:** Level 2 (order book) data — requires exchange data subscription, not available in standard free feeds
**Survival note:** Real edge but requires infrastructure (low latency, L2 data). Not accessible to most retail investors.

---

### F064 — Trade Size Distribution
**Description:** Distribution of trade sizes (clip sizes) throughout the day. Unusual concentration in large clip sizes = institutional activity. Unusual small clips = retail activity or algorithmic splitting.
**Optimal timeframe:** Intraday
**Signal direction:** Large institutional clips on upticks = accumulation; large clips on downticks = distribution
**Evidence:** Moderate-Strong. Meulbroek (1992), Kyle (1985). Informed traders use specific trade size signatures. Empirically, trades >$100K on upticks predict next-day positive returns.
**Data availability:** Trade-level data (TAQ database or similar) — not available in standard free feeds
**Survival note:** Real but requires premium tick data and sophisticated processing.

---

### F065 — Effective Spread (Kyle's Lambda)
**Description:** Price impact of a trade as a function of order flow. Lambda = price change per unit of signed order flow. High lambda = high price impact = illiquid.
**Optimal timeframe:** Estimated daily or intraday
**Signal direction:** High lambda = illiquid = expect higher returns (premium) but also more extreme moves
**Evidence:** Strong. Kyle (1985). Foundation of microstructure theory. Empirically estimated lambda is predictive of future return volatility.
**Data availability:** Requires trade-level data for precise estimation; approximated from daily data using Hasbrouck's (1991) estimator
**Survival note:** Strong conceptually. Approximated daily measures are usable; precise estimates require tick data.

---

## Category 9: Order Flow Indicators

### F066 — Order Flow Delta (Buy Volume − Sell Volume)
**Description:** Classify each trade as buyer-initiated (at/above ask) or seller-initiated (at/below bid). Delta = buy volume − sell volume over an interval.
**Optimal timeframe:** Intraday (bar-by-bar)
**Signal direction:** Positive delta = buying pressure; negative = selling pressure. Cumulative delta trending against price = divergence warning.
**Evidence:** Strong. Steidlmayer (1985) Market Profile, Dalton (1990). Widely used by professional futures traders. Empirical studies confirm short-term predictive power.
**Data availability:** Tick data required — requires premium data
**Survival note:** Real edge at intraday timescale. Not accessible from standard OHLCV.

---

### F067 — Cumulative Delta Divergence
**Description:** Cumulative delta trending down while price trends up (or vice versa) = bearish divergence signal. Shows that price gains are being made on decreasing buy pressure.
**Optimal timeframe:** Intraday to daily
**Signal direction:** Bearish divergence = price reversal warning; bullish divergence = price strength ahead
**Evidence:** Moderate. Well-documented in Market Profile and order flow literature. Formal academic study is limited.
**Data availability:** Tick data required
**Survival note:** Moderate. Real signal for professional traders; tick data barrier limits accessibility.

---

### F068 — Footprint Chart Imbalances
**Description:** Volume at each price at bid vs. ask for each candle. Imbalances (much more volume on one side) at swing highs/lows signal institutional positioning.
**Optimal timeframe:** Intraday
**Signal direction:** Selling imbalances at highs = distribution; buying imbalances at lows = accumulation
**Evidence:** Moderate (practitioner). Used by professional futures traders. Limited formal academic evidence.
**Data availability:** Requires tape-reading or specialized footprint software
**Survival note:** Moderate for professional intraday traders. High data and infrastructure barrier.

---

### F069 — VPIN (Volume-Synchronized Probability of Informed Trading)
**Description:** Probability that a trade is initiated by an informed trader, estimated from volume imbalance in time-buckets synchronized to volume rather than clock time.
**Optimal timeframe:** Intraday; predicts liquidity crises and flash crash risk
**Signal direction:** High VPIN = elevated informed trading = expect larger price moves; useful for risk management
**Evidence:** Strong (academic). Easley, Lopez de Prado, O'Hara (2012). Predicted the 2010 Flash Crash. Widely cited in market microstructure literature.
**Data availability:** Trade-level data — requires TAQ or similar
**Survival note:** Strong for market stability research. Operationalizing it for return prediction is complex.

---

## Category 10: Price Patterns and Levels

### F070 — Opening Gap (Gap Up / Gap Down)
**Description:** (Today's open − Yesterday's close) / Yesterday's close. Classifies as full gap (open outside prior day's range) or common gap.
**Optimal timeframe:** Intraday and 1-5 day
**Signal direction:** Full gap down on no news: 70%+ fill rate intraday. Gap up into resistance: high fade rate. News-driven gaps continue 60%+ of time.
**Evidence:** Moderate. Academic studies: Bhootra & Hur (2015). Practitioner evidence: Cooper et al. (1999) find opening gap statistics are tradeable.
**Data availability:** OHLCV (daily open)
**Survival note:** Moderate. Direction-dependent. Gap fill trading on indices (SPY) works better than on individual stocks.

---

### F071 — Inside Bar Pattern
**Description:** Today's high < yesterday's high AND today's low > yesterday's low. Range contraction. Breakout of inside bar's range = directional signal.
**Optimal timeframe:** 1–3 days post-signal
**Signal direction:** Breakout of parent bar high = bullish continuation; breakdown of parent bar low = bearish
**Evidence:** Moderate (practitioner). Toby Crabel (1990) Day Trading with Short Term Price Patterns. Limited formal academic study but widely used.
**Data availability:** OHLCV (daily)
**Survival note:** Moderate. Works best when inside bar follows a strong trend (continuation) rather than in ranging markets.

---

### F072 — Key Reversal Day
**Description:** Upside key reversal: stock makes new high for the move, then closes below prior day's close. Downside key reversal: new low then closes above prior close. High/Low close proximity matters.
**Optimal timeframe:** 1–5 days
**Signal direction:** Reversal signal (exhaustion)
**Evidence:** Moderate (practitioner). Part of classical bar charting (Edwards & Magee, 1948). Limited formal academic study.
**Data availability:** OHLCV (daily)
**Survival note:** Weak standalone. Useful as exhaustion alert when combined with oscillator readings.

---

### F073 — Pivot Points (Daily, Weekly, Monthly)
**Description:** Pivot = (H + L + C) / 3. Support/Resistance levels derived from prior period's high, low, close. Multiple calculation methods (standard, Fibonacci, Camarilla, Woodie's).
**Optimal timeframe:** Intraday (daily pivots), 1-week (weekly pivots)
**Signal direction:** Support/resistance at pivot levels; reversals or breakouts at these levels
**Evidence:** Moderate (practitioner). Self-fulfilling — widely watched by professionals. Banks and market makers use pivot levels for target pricing.
**Data availability:** OHLCV (daily) — computable from prior day's OHLC
**Survival note:** Moderate. Self-fulfilling component gives them real predictive value. Best for intraday setups.

---

### F074 — Support and Resistance Levels (Horizontal)
**Description:** Price levels where the stock has previously reversed multiple times. Identified algorithmically as local maxima/minima with multiple touches.
**Optimal timeframe:** Variable (defined by the timeframe of the chart)
**Signal direction:** Price approaching support = potential bounce; approaching resistance = potential reversal
**Evidence:** Moderate. Osler (2000): significant clustering of stop orders at round numbers and prior highs/lows. Academic evidence supports price clustering behavior.
**Data availability:** OHLCV (historical) — algorithmically identifiable
**Survival note:** Moderate. Round number and prior extreme levels do create real order clusters. Exploitable with limit orders.

---

### F075 — Fibonacci Retracement Levels (38.2%, 50%, 61.8%)
**Description:** Key ratios derived from Fibonacci sequence applied to significant price swings. 38.2%, 50%, and 61.8% retracement levels are the most watched.
**Optimal timeframe:** Depends on swing timeframe (days to months)
**Signal direction:** Retracements to Fibonacci levels often halt and reverse (potential support)
**Evidence:** Weak-Moderate. Controversial. Osler (2000) finds some evidence for clustering at Fibonacci levels in FX markets. For equity markets, evidence is weak and self-fulfilling at best.
**Data availability:** OHLCV (requires swing identification algorithm)
**Survival note:** Weak. The statistical evidence for Fibonacci levels in equities is not convincingly different from random levels. Self-fulfilling component is real but small. Use round-number analysis instead.

---

### F076 — Price Round Number Clustering
**Description:** Prices cluster at round numbers ($50, $100, $500, etc.). Significant breakouts above/below round numbers are more persistent.
**Optimal timeframe:** Days to weeks
**Signal direction:** Breaking above a major round number on volume = breakout signal; failure at round number = resistance
**Evidence:** Moderate. Donaldson & Kim (1993): S&P 500 attracts and repels at round numbers. Coval & Shumway (1998). Real psychological anchoring effect.
**Data availability:** OHLCV (daily)
**Survival note:** Moderate. Round number effects are statistically significant. Easily computed.

---

## Category 11: Options-Derived Signals

### F077 — Put/Call Ratio (PCR)
**Description:** Volume of put options / volume of call options. Total market PCR or stock-specific PCR. High PCR = bearish sentiment = contrarian buy; low PCR = complacency = contrarian sell.
**Optimal timeframe:** 5–21 days (contrarian); longer-term trend in PCR matters
**Signal direction:** Extreme high PCR (>1.5) = contrarian buy; extreme low PCR (<0.5) = contrarian sell
**Evidence:** Strong. Simon & Wiggins (2001), Blau et al. (2014). PCR is one of the most studied sentiment indicators. Contrarian effect is statistically significant.
**Data availability:** CBOE options volume data (free daily PCR from CBOE website)
**Survival note:** Strong for market-level PCR. Individual stock PCR is noisier. Free data available.

---

### F078 — Max Pain Level
**Description:** Strike price at which option sellers (market makers) face minimum total loss at expiration. Price tends to gravitate toward max pain in the weeks before expiration.
**Optimal timeframe:** Weeklies to monthly options expiration cycles
**Signal direction:** Price drift toward max pain strike in final 1–2 weeks before expiration
**Evidence:** Moderate (practitioner evidence). Theory: market makers gamma-hedge, which mechanically pulls price toward max pain. Academic evidence is limited; some studies support modest effect.
**Data availability:** Options chain data (strikes, open interest) — available via yfinance or CBOE
**Survival note:** Moderate. Max pain drift is real but effect size is small and timing is imprecise. Not a standalone signal.

---

### F079 — Gamma Exposure (GEX) — Dealer Gamma
**Description:** Net gamma of all options held by market makers. Market makers are typically short gamma (sold options). They must buy the underlying when price rises and sell when it falls (delta-hedging), amplifying moves when gamma is negative (negative GEX = volatile regime).
**Optimal timeframe:** Days to 2-3 weeks; recalculated daily
**Signal direction:** Positive GEX = market makers act as stabilizers (pin action); negative GEX = market makers amplify moves (volatile regime)
**Evidence:** Strong. Bolla et al. (2020), SpotGamma research. GEX transition from positive to negative correlates with volatility regime changes. Confirmed by market microstructure researchers.
**Data availability:** Options open interest by strike — via CBOE or options data providers. Requires modeling dealer positioning (hedging assumption).
**Survival note:** Strong. GEX is the best available indicator of structural volatility in the market. Used by professional quants and options desks.

---

### F080 — Implied Volatility Skew (Put Skew)
**Description:** Difference in IV between out-of-the-money puts and out-of-the-money calls at the same delta. High skew = market pays more to protect downside = fear premium.
**Optimal timeframe:** 1–4 weeks
**Signal direction:** Extreme skew = overpayment for downside protection = contrarian buy (near-term reversal likely). Skew collapse after fear episode = risk-on signal.
**Evidence:** Strong. Bates (2000), Pan (2002). Skew is priced as jump risk premium. Extreme skew predicts positive forward equity returns (contrarian).
**Data availability:** Options chain with IV at multiple strikes — CBOE, options data providers
**Survival note:** Strong. IV skew is well-studied and the return predictability from extreme skew is robust.

---

### F081 — Options Open Interest Changes
**Description:** Day-over-day changes in open interest at specific strikes. Large OI build at certain strikes signals institutional positioning or hedging.
**Optimal timeframe:** Days to monthly expiration
**Signal direction:** Large put OI build = institutional hedging (bullish underlying stance); large call OI = potential upside speculation
**Evidence:** Moderate. Pan & Poteshman (2006): options order imbalance predicts next-day stock returns. Stock-level OI changes have information content.
**Data availability:** Options OI data (daily) via CBOE or yfinance
**Survival note:** Moderate. Information in OI is partially front-run by the market makers. Pan & Poteshman find significant alphas before costs.

---

### F082 — VIX Level and Term Structure
**Description:** VIX = 30-day implied volatility of S&P 500. VIX term structure = ratio of VIX (30-day) to VIX3M (90-day). Backwardation (VIX > VIX3M) = acute fear.
**Optimal timeframe:** 1–30 days
**Signal direction:** VIX > 30 = elevated fear = contrarian buy for equity. VIX term structure in backwardation = elevated near-term risk. VIX spike + backwardation reversal = strong buy signal.
**Evidence:** Strong. Numerous studies confirm VIX spike = buy signal for equity markets. VIX term structure slope is a systematic market timing factor.
**Data availability:** CBOE VIX (free daily from CBOE, Yahoo Finance)
**Survival note:** Strong. VIX-based market timing has real Sharpe improvement. Classic combination: buy SPY when VIX spikes >40, hold until VIX < 25.

---

## Category 12: Alternative Price-Based and Sentiment Signals

### F083 — Short Interest Ratio (Days to Cover)
**Description:** Short Interest / Average Daily Volume = days required to cover all short positions. High ratio = heavily shorted = potential squeeze candidate; also a bearish signal in normal regimes.
**Optimal timeframe:** Bi-weekly data (FINRA reporting cycle); predicts 2–4 weeks ahead
**Signal direction:** HIGH short interest = bearish signal normally; potential squeeze catalyst if news is positive. SHORT SQUEEZE: rapid price rise forces short covering, amplifying gains.
**Evidence:** Strong. Asquith, Pathak & Ritter (2005): high short interest strongly predicts negative returns over next 12 months. Squeeze episodes are shorter-horizon positive.
**Data availability:** FINRA short interest reports (bi-weekly, free)
**Survival note:** Strong for the short-side signal (short high-SI stocks). Long-squeeze signal is speculative and timing-dependent.

---

### F084 — Short Interest Change Rate
**Description:** (Current short interest − prior period short interest) / prior period short interest. Rising short interest is more bearish than level alone.
**Optimal timeframe:** Bi-weekly
**Signal direction:** Large increase in short interest = increased bearish conviction = negative forward returns
**Evidence:** Moderate. Desai et al. (2002), Boehmer et al. (2010). Change in short interest has incremental information over level.
**Data availability:** FINRA bi-weekly reports
**Survival note:** Moderate. Incremental signal over level. Useful for ranking stocks within high-short-interest universe.

---

### F085 — Insider Buying Signal (SEC Form 4)
**Description:** Open market purchases by corporate insiders (officers, directors). NOT option exercises. Must be voluntary purchase above market price.
**Optimal timeframe:** 1–12 months post-filing
**Signal direction:** Insider buying = bullish signal (insider has private positive information)
**Evidence:** Strong. Seyhun (1988), Jeng, Metrick & Zeckhauser (2003). Insider buying, particularly by multiple insiders simultaneously, predicts positive returns over 1–12 months. Classic "cluster buy" signal.
**Data availability:** SEC EDGAR Form 4 filings (free, same-day availability)
**Survival note:** Strong. One of the cleanest information signals. Survives transaction costs and is free to obtain. Short-horizon implementation is best.

---

### F086 — Insider Selling Signal (SEC Form 4)
**Description:** Open market sales by insiders. More ambiguous than buying (insiders sell for many reasons: diversification, estate planning, option exercise schedules).
**Optimal timeframe:** 1–6 months
**Signal direction:** Large sales by multiple insiders = mildly bearish; not as strong as buy signal
**Evidence:** Moderate. Weaker than insider buying signal. Seyhun (1992): insider selling has predictive value but much weaker than buying. Pre-announced sales plans (10b5-1) reduce information content.
**Data availability:** SEC EDGAR Form 4 (free)
**Survival note:** Moderate. 10b5-1 plans weaken the signal significantly. Use with caution.

---

### F087 — Day-of-Week Effect
**Description:** Systematic return differences by day of week. Monday effect (historically negative), Friday effect (positive), pre-holiday effect (positive).
**Optimal timeframe:** Single-day prediction
**Signal direction:** Historically: Monday returns negative; Friday returns positive; day-before-holiday positive
**Evidence:** Moderate. French (1980), Lakonishok & Smidt (1988). Well-documented historically but partially arbitraged. Monday effect has weakened post-discovery.
**Data availability:** Calendar-derived (no additional data needed)
**Survival note:** Weak post-discovery. Useful as small adjustment factor in multi-factor models, not standalone.

---

### F088 — Month-of-Year Seasonality
**Description:** January effect (small-cap outperformance), "Sell in May and Go Away" (May–October underperformance vs. November–April), September as worst performing month historically.
**Optimal timeframe:** Monthly
**Signal direction:** January: bullish small-cap. May–October: reduce equity exposure. November–April: increase equity exposure.
**Evidence:** Moderate-Strong. January effect: Rozeff & Kinney (1976). Halloween effect (Sell in May): Bouman & Jacobsen (2002), replicated in 37 countries. September effect: statistically significant historically.
**Data availability:** Calendar-derived
**Survival note:** Moderate. January effect has declined since publication. Halloween effect remains in international data. Not sufficient alone but useful overlay.

---

### F089 — Options Expiration Week Effect (OPEX)
**Description:** The week of monthly options expiration (third Friday) has distinct return patterns. Market makers' hedging activity creates predictable flows.
**Optimal timeframe:** Weekly (expiration week and week after)
**Signal direction:** Expiration week: pin to max pain. Week after expiration: directional move resumes (GEX resets).
**Evidence:** Moderate. Ni, Pearson & Poteshman (2005): stock prices cluster at option strike prices near expiration. Post-expiration drift is documented.
**Data availability:** Calendar (expiration dates) + OHLCV
**Survival note:** Moderate. PIN effect at strike prices is real but small. Post-expiration drift is exploitable.

---

### F090 — Turn-of-Month Effect
**Description:** Stocks tend to outperform in the last 1–2 trading days of a month and first 3–4 trading days of the next month. Driven by pension fund contributions and rebalancing flows.
**Optimal timeframe:** ±3 days around month-end
**Signal direction:** Positive bias at month-end/start
**Evidence:** Strong. Ogden (1990), Lakonishok & Smidt (1988). Remarkably persistent across markets. Likely driven by systematic institutional fund flows (401k contributions, pension rebalancing).
**Data availability:** Calendar-derived
**Survival note:** Strong and persistent. One of the most reliable seasonal effects. Low turnover, low transaction cost implementation.

---

### F091 — Relative Strength vs. Index (RS Rating)
**Description:** Stock's return relative to index return over 63 or 252 days. William O'Neil's RS Rating (1–99 scale vs. all stocks). High RS = outperforming the market.
**Optimal timeframe:** 3–12 months formation; 1–6 months prediction
**Signal direction:** High RS = momentum/leadership = continue to buy. Low RS = avoid or short.
**Evidence:** Strong. Core component of CANSLIM system (O'Neil 1988). Independent academic evidence supports relative momentum over absolute return momentum (same as F010 cross-sectional momentum).
**Data availability:** OHLCV for stock and index
**Survival note:** Strong. Cross-sectional relative strength is one of the most robust momentum implementations. Used by most professional momentum managers.

---

### F092 — Relative Strength vs. Sector
**Description:** Stock return minus sector ETF return over 63 or 252 days. Identifies within-sector leaders.
**Optimal timeframe:** 3–12 months
**Signal direction:** Outperforming sector peers = continued leadership. Underperforming sector = laggard likely to continue underperforming.
**Evidence:** Strong. Industry-level momentum is well-documented (Moskowitz & Grinblatt 1999): much of stock momentum is explained by industry momentum. Relative strength within industry adds incremental value.
**Data availability:** OHLCV for stock + sector ETF (SPY sector ETFs are free from Yahoo Finance)
**Survival note:** Strong. Industry momentum survives costs. Within-sector selection adds value over pure index momentum.

---

### F093 — Inter-Market Momentum (Cross-Asset Signals)
**Description:** Return signal derived from related asset classes. Examples: bond yield changes → equity sector rotation; oil price momentum → energy stocks; USD momentum → multinational earnings.
**Optimal timeframe:** 1–4 weeks
**Signal direction:** Bond yield rising = value/financial outperform; growth underperforms. USD rising = domestic consumer outperforms; exporters underperform. Oil rising = energy/materials lead.
**Evidence:** Moderate. Martin Pring (2002) inter-market analysis. Ferson & Harvey (1991): business cycle factors from bond/commodity markets predict equity returns.
**Data availability:** Free ETF prices for bonds (TLT, IEF), commodities (GLD, USO), USD (UUP)
**Survival note:** Moderate. Cross-asset signals add useful regime context but require correct mapping to sector exposures.

---

### F094 — Earnings Announcement Momentum (Post-Earnings Drift / PEAD)
**Description:** Stocks that gap up/down significantly on earnings continue to drift in the same direction for 60–90 days after the announcement.
**Optimal timeframe:** 1–60 days post-earnings
**Signal direction:** Large positive earnings gap = buy and hold 60 days; large negative earnings gap = short or avoid 60 days
**Evidence:** Strong. Ball & Brown (1968), Bernard & Thomas (1989, 1990). One of the most replicated anomalies. PEAD survives transaction costs for patient investors.
**Data availability:** Earnings dates + OHLCV (earnings dates from SEC EDGAR, yfinance)
**Survival note:** Strong. Survives transaction costs at monthly rebalancing. Weaker for very large-cap stocks (faster arbitrage). Best in small/mid-cap.

---

### F095 — Price Trend Linearity (R-squared of Price Trend)
**Description:** R-squared of a linear regression of log-price on time over a lookback window (typically 90 days). High R-squared = clean, linear trend. Low R-squared = choppy, non-trending.
**Optimal timeframe:** 90-day lookback; predicts 1–4 weeks
**Signal direction:** High R-squared + positive slope = strong trend continuation. High R-squared + negative slope = strong downtrend. Low R-squared = mean reversion more likely.
**Evidence:** Moderate. Used in algorithmic trend-following. Marks (2009). Academic reference: trend quality measures in time-series momentum literature.
**Data availability:** OHLCV (daily) — regression computed from price series
**Survival note:** Moderate. Useful for regime-conditional strategy switching (momentum vs. mean reversion). Not standalone.

---

## Summary Reference Table

| ID | Factor Name | Category | Timeframe | Direction | Evidence |
|----|-------------|----------|-----------|-----------|----------|
| F001 | 1-Day Return (O/N + Intraday) | Momentum | 1–5d | Reversal (lqd) | Moderate |
| F002 | 1-Week Momentum | Momentum | 5–10d | Continuation | Moderate |
| F003 | 1-Month Momentum | Momentum | 5–21d | Continuation | Moderate-Strong |
| F004 | 3-Month Momentum | Momentum | 1–3m | Continuation | Strong |
| F005 | 6-Month Momentum | Momentum | 1–6m | Continuation | Strong |
| F006 | 12-Month Momentum | Momentum | 1–12m | Continuation | Strong |
| F007 | 24-Month Momentum | Momentum | 3–12m | Continuation/Reversal | Moderate |
| F008 | 52-Week High Ratio | Momentum | 1–6m | Continuation | Strong |
| F009 | ATH Ratio | Momentum | 1–3m | Mixed | Moderate |
| F010 | Cross-Sectional Momentum Rank | Momentum | 3–12m | Continuation | Strong |
| F011 | Residual Momentum | Momentum | 6–12m | Continuation | Strong |
| F012 | 3–5 Year Reversal | Mean Rev | 12–36m | Reversal | Strong |
| F013 | Short-Term 1-Month Reversal | Mean Rev | 5–21d | Reversal | Strong |
| F014 | Overnight Gap Reversal | Mean Rev | Intraday | Reversal | Moderate |
| F015 | Intraday Mean Reversion | Mean Rev | Minutes | VWAP revert | Moderate |
| F016 | SMA 10-Day | Moving Avg | 1–5d | Trend | Moderate |
| F017 | SMA 20-Day | Moving Avg | 5–20d | Trend | Moderate |
| F018 | SMA 50-Day | Moving Avg | 1–2m | Trend | Moderate |
| F019 | SMA 200-Day (Faber) | Moving Avg | 1–12m | Drawdown reduction | Strong |
| F020 | EMA 9-Day | Moving Avg | 1–5d | Trend (component) | Weak |
| F021 | EMA 12/26 Crossover | Moving Avg | 2–6w | Trend signal | Moderate |
| F022 | VWAP | Moving Avg | Intraday | Support/Resistance | Moderate |
| F023 | Anchored VWAP | Moving Avg | Days–weeks | Dynamic S/R | Moderate |
| F024 | Hull Moving Average | Moving Avg | 10–30d | Trend | Weak |
| F025 | KAMA | Moving Avg | 10–30d | Trend (adaptive) | Moderate |
| F026 | MACD | Oscillator | 2–8w | Trend confirmation | Moderate |
| F027 | MA Envelope | Oscillator | 10–30d | Reversion | Weak |
| F028 | RSI 14-Day | Oscillator | 5–21d | Reversal | Moderate |
| F029 | RSI 2-Day (Connors) | Oscillator | 1–5d | Reversal | Moderate |
| F030 | Stochastic %K/%D | Oscillator | 5–15d | Reversal | Moderate |
| F031 | CCI | Oscillator | 14–20d | Reversal/Momentum | Moderate |
| F032 | Williams %R | Oscillator | 10–14d | Reversal | Moderate |
| F033 | Ultimate Oscillator | Oscillator | 14–28d | Reversal | Weak |
| F034 | Rate of Change (ROC) | Oscillator | 5–63d | Momentum | Moderate |
| F035 | Chande Momentum Osc | Oscillator | 14–20d | Mixed | Weak |
| F036 | Aroon Oscillator | Oscillator | 25d | Trend class | Weak-Mod |
| F037 | On-Balance Volume | Volume | 5–30d | Divergence | Moderate |
| F038 | Volume Price Trend | Volume | 10–30d | Divergence | Moderate |
| F039 | A/D Line | Volume | 10–30d | Divergence | Moderate |
| F040 | Chaikin Money Flow | Volume | 20d | Buying pressure | Moderate |
| F041 | Volume Profile (POC) | Volume | Days–weeks | S/R dynamic | Moderate |
| F042 | Relative Volume (RVOL) | Volume | Intraday–daily | Breakout confirm | Moderate |
| F043 | Dollar Volume Turnover | Volume | 5–21d | Attention | Moderate |
| F044 | Volume-Weighted Momentum | Volume | 21–63d | Continuation | Moderate |
| F045 | ATR 14-Day | Volatility | 10–20d | Regime | Strong |
| F046 | Bollinger Bands (%B, BW) | Volatility | 10–30d | Reversion/Breakout | Moderate |
| F047 | Keltner Channels | Volatility | 10–20d | Breakout | Moderate |
| F048 | Historical Volatility (HV) | Volatility | 20–60d | Low-vol anomaly | Strong |
| F049 | Realized Vol (Parkinson/GK) | Volatility | 10–20d | Vol estimation | Strong |
| F050 | Volatility of Volatility | Volatility | 60d rolling | Regime | Moderate |
| F051 | Implied Volatility (IV) | Volatility | 30d fwd | Fear premium | Strong |
| F052 | IV/HV Ratio | Volatility | 20–30d | Vol premium | Strong |
| F053 | Volatility Ratio (ST/LT) | Volatility | 10–60d | Regime | Moderate |
| F054 | A/D Line (Breadth) | Breadth | Weeks–months | Market health | Strong |
| F055 | A/D Ratio | Breadth | 1–5d | Panic/Euphoria | Moderate |
| F056 | New 52W Highs/Lows | Breadth | Weekly | Market quality | Strong |
| F057 | McClellan Oscillator | Breadth | 5–20d | Breadth momentum | Moderate-Strong |
| F058 | TRIN (Arms Index) | Breadth | Intraday–daily | Panic detect | Moderate |
| F059 | % Stocks > 50/200 MA | Breadth | Weeks–months | Regime | Strong |
| F060 | Zweig Breadth Thrust | Breadth | 10d → months | Bull confirmation | Moderate-Strong |
| F061 | Bid-Ask Spread | Microstructure | Real-time | Liquidity cost | Strong |
| F062 | Amihud Illiquidity | Microstructure | Monthly | Illiquidity premium | Strong |
| F063 | Order Book Depth | Microstructure | Real-time | Short-term press | Strong |
| F064 | Trade Size Distribution | Microstructure | Intraday | Informed trading | Moderate-Strong |
| F065 | Kyle's Lambda (price impact) | Microstructure | Daily | Illiquidity | Strong |
| F066 | Order Flow Delta | Order Flow | Intraday | Buying pressure | Strong |
| F067 | Cumulative Delta Divergence | Order Flow | Intraday–daily | Reversal warning | Moderate |
| F068 | Footprint Imbalances | Order Flow | Intraday | Institutional pos | Moderate |
| F069 | VPIN | Order Flow | Intraday | Informed trading | Strong |
| F070 | Opening Gap | Price Pattern | Intraday–5d | Reversal/Cont | Moderate |
| F071 | Inside Bar | Price Pattern | 1–3d | Breakout signal | Moderate |
| F072 | Key Reversal Day | Price Pattern | 1–5d | Exhaustion | Moderate |
| F073 | Pivot Points | Price Pattern | Intraday–week | S/R dynamic | Moderate |
| F074 | Horizontal S/R Levels | Price Pattern | Variable | S/R | Moderate |
| F075 | Fibonacci Retracements | Price Pattern | Variable | S/R (weak) | Weak-Mod |
| F076 | Round Number Clustering | Price Pattern | Days–weeks | Psychological S/R | Moderate |
| F077 | Put/Call Ratio | Options | 5–21d | Sentiment | Strong |
| F078 | Max Pain Level | Options | 1–2w pre-exp | Price gravitation | Moderate |
| F079 | Gamma Exposure (GEX) | Options | Days–2w | Vol regime | Strong |
| F080 | IV Skew (Put Skew) | Options | 1–4w | Fear premium | Strong |
| F081 | Options OI Changes | Options | Days–month | Institutional pos | Moderate |
| F082 | VIX Level + Term Structure | Options | 1–30d | Fear/Complacency | Strong |
| F083 | Short Interest Ratio | Alt Signal | 2–4w | Bearish/Squeeze | Strong |
| F084 | Short Interest Change | Alt Signal | 2–4w | Bearish increment | Moderate |
| F085 | Insider Buying (Form 4) | Alt Signal | 1–12m | Bullish | Strong |
| F086 | Insider Selling (Form 4) | Alt Signal | 1–6m | Mildly bearish | Moderate |
| F087 | Day-of-Week Effect | Seasonal | Single day | Calendar bias | Weak (modern) |
| F088 | Month-of-Year Seasonality | Seasonal | Monthly | Seasonal bias | Moderate |
| F089 | OPEX Effect | Seasonal | Weekly | Options flow | Moderate |
| F090 | Turn-of-Month Effect | Seasonal | ±3 days | Fund flow | Strong |
| F091 | Relative Strength vs. Index | Rel Strength | 3–12m | Continuation | Strong |
| F092 | Relative Strength vs. Sector | Rel Strength | 3–12m | Continuation | Strong |
| F093 | Inter-Market Momentum | Cross-Asset | 1–4w | Sector rotation | Moderate |
| F094 | Post-Earnings Drift (PEAD) | Earnings | 1–60d | Continuation | Strong |
| F095 | Price Trend Linearity (R²) | Regime | 90d lookback | Trend quality | Moderate |

---

## Implementation Priority for This Project

### Tier 1: Implement First (High evidence, free data, daily OHLCV sufficient)

These 25 factors are computable from standard daily OHLCV + free auxiliary data and have strong academic evidence:

| Priority | Factor ID | Reason |
|----------|-----------|--------|
| 1 | F005, F006 | Core 6/12-month momentum — strongest evidence |
| 2 | F010 | Cross-sectional momentum rank — best momentum implementation |
| 3 | F019 | SMA 200-day — best drawdown protection |
| 4 | F048 | Historical volatility (low-vol anomaly) |
| 5 | F062 | Amihud illiquidity — computable from OHLCV |
| 6 | F008 | 52-week high ratio — strong momentum variant |
| 7 | F013 | Short-term 1-month reversal — important to avoid |
| 8 | F085 | Insider buying — free from SEC EDGAR |
| 9 | F077 | Put/call ratio — free from CBOE |
| 10 | F082 | VIX level and term structure — free from CBOE/Yahoo |
| 11 | F094 | PEAD — high evidence, needs earnings dates only |
| 12 | F083 | Short interest — free bi-weekly from FINRA |
| 13 | F054 | A/D Line — free breadth data |
| 14 | F059 | % Stocks above MA — computable from universe OHLCV |
| 15 | F090 | Turn-of-month — calendar signal, zero data cost |
| 16 | F028 | RSI 14-day — oscillator baseline |
| 17 | F011 | Residual momentum — best momentum variant |
| 18 | F091 | RS vs. Index — direct relative strength |
| 19 | F092 | RS vs. Sector — within-sector ranking |
| 20 | F046 | Bollinger Band squeeze — volatility compression signal |
| 21 | F037 | OBV divergence — volume confirmation |
| 22 | F040 | Chaikin Money Flow — normalized volume pressure |
| 23 | F088 | Seasonal factors — November–April overlay |
| 24 | F076 | Round number clustering — pattern signal |
| 25 | F042 | RVOL — breakout confirmation |

### Tier 2: Add After Tier 1 Validation (Requires options data or enhanced data)

F051 (IV), F052 (IV/HV ratio), F079 (GEX), F080 (IV skew), F081 (OI changes), F078 (max pain)

### Tier 3: Requires Premium Data Infrastructure (Tick-level, L2 data)

F063 (order book depth), F064 (trade size), F066 (delta), F067 (cumulative delta), F068 (footprint), F069 (VPIN)

---

## Data Dependencies Summary

| Data Source | Factors Enabled | Cost | Access |
|-------------|----------------|------|--------|
| yfinance OHLCV (daily) | F001–F020, F022, F024–F046, F048–F050, F053, F056, F070–F076, F087–F090, F095 | Free | yfinance Python library |
| Universe daily OHLCV | F010, F054, F055, F059, F091, F092 | Free | yfinance batch |
| CBOE VIX data | F082 | Free | CBOE website, Yahoo (^VIX, ^VIX3M) |
| CBOE PCR daily | F077 | Free | CBOE website download |
| CBOE options chain | F078, F079, F080, F081, F051, F052 | Free (delayed) | yfinance options; real-time requires subscription |
| FINRA short interest | F083, F084 | Free (bi-weekly) | FINRA website |
| SEC EDGAR Form 4 | F085, F086 | Free | EDGAR full-text search, sec-edgar-api |
| Market breadth data | F054, F055, F057, F058, F060 | Free | Barchart, StockCharts (some), DIY from universe |
| Earnings calendar | F094 | Free | yfinance, Alpha Vantage |
| Tick/L2 data | F063–F069, F041 | Premium | IEX Cloud, Polygon.io, Interactive Brokers |
| Intraday OHLCV | F015, F022, F023, F041 | Free limited | yfinance 1m (60d), Polygon.io |

---

## Critical Implementation Warnings

1. **Survivorship bias:** All backtests must use point-in-time universe membership. Using today's S&P 500 to backtest 2010 data = guaranteed overfitting. Maintain historical constituent lists.

2. **Look-ahead bias in earnings dates:** Many data providers report the earnings date after the fact with different dates than what was known in advance. Always use confirmed, advance-reported earnings dates.

3. **Short interest timing:** FINRA reports bi-weekly with a 1-week lag. The settlement date matters — use settlement date, not report date.

4. **Form 4 filings:** Insiders have 2 business days to file. Use the transaction date (Form 4 field), not the filing date.

5. **Options data:** Daily end-of-day options snapshots are sufficient for PCR, GEX, max pain. Intraday needed for precise IV skew surface.

6. **Factor interaction:** Many factors are correlated (momentum × volume-weighted momentum × relative strength). Use correlation analysis before combining. Orthogonal factor construction (residual momentum) reduces redundancy.

7. **Regime conditioning:** Many factors have opposite signs in different market regimes. Oscillators (RSI oversold) are contrarian in trending markets but predictive in range-bound markets. Always test regime-conditional factor behavior.

8. **Transaction costs:** Small-cap factors (illiquidity, short-term reversal) show large gross returns that are largely consumed by bid-ask spread and market impact. Use realistic transaction cost models: 0.1% for large-cap ETFs, 0.3–0.5% for small-cap.

9. **Multiple testing:** 95 factors tested = expect ~4–5 to appear significant at 5% level by chance alone. Use Bonferroni correction or FDR control (Benjamini-Hochberg). Report factor-by-factor information coefficients (ICs) not just regression t-stats.

10. **Alpha decay:** Document when each factor was first published. Test pre- vs. post-publication performance. Factors discovered pre-internet (pre-1990) have mostly been arbitraged; factors requiring complex data processing retain more edge.
