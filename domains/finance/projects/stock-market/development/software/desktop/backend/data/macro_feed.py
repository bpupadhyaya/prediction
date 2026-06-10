"""
Tier 1 macro + cross-asset data feeds.

Sources (all free, no API key required for basic access):
  FRED CSV downloads  — yields, spreads, money supply, conditions indices
  Yahoo Finance       — VIX, cross-asset (DXY, gold, copper, oil, USDJPY, BTC)
"""

import io
import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests
import yfinance as yf

from backend.database.duckdb_client import get_conn

logger = logging.getLogger(__name__)

# ── FRED series (direct CSV download — no API key needed) ─────────────────────
# Format: series_id → FRED series ID (same string used as primary key in DB)
_FRED_SERIES: dict[str, str] = {
    "DGS10":        "DGS10",         # 10-Year Treasury Yield
    "DGS2":         "DGS2",          # 2-Year Treasury Yield
    "DGS3M":        "DTB3",          # 3-Month T-Bill (DTB3 on FRED)
    "BAMLH0A0HYM2": "BAMLH0A0HYM2", # HY OAS credit spread (basis points)
    "BAMLC0A0CM":   "BAMLC0A0CM",   # IG OAS credit spread (basis points)
    "DFII10":       "DFII10",        # 10-Year TIPS real yield
    "M2SL":         "M2SL",          # M2 money supply (billions)
    "ICSA":         "ICSA",          # Initial jobless claims
    "NFCI":         "NFCI",          # Chicago Fed National Financial Conditions Index
    "PCEPILFE":     "PCEPILFE",      # PCE Core Price Index (level — compute YoY)
    "WALCL":        "WALCL",         # Fed balance sheet (millions)
    # ── Additional macro series ────────────────────────────────────────────
    # Consumer / Sentiment
    "UMCSENT":      "UMCSENT",       # UMich Consumer Sentiment
    "NAPM":         "NAPM",          # ISM Manufacturing PMI
    # Housing
    "HOUST":        "HOUST",         # Housing Starts
    "CSUSHPINSA":   "CSUSHPINSA",    # Case-Shiller Home Price Index
    # Activity
    "INDPRO":       "INDPRO",        # Industrial Production Index
    "RSXFS":        "RSXFS",         # Retail Sales excl. Food Services
    # Inflation
    "CPILFESL":     "CPILFESL",      # Core CPI (level — compute YoY)
    "PPIACO":       "PPIACO",        # PPI All Commodities
    "T10YIE":       "T10YIE",        # 10-Year Breakeven Inflation
    # Money / Credit
    "M2V":          "M2V",           # M2 Velocity of Money
    "TOTCI":        "TOTCI",         # Total Consumer Credit Outstanding
    "DRSDCILM":     "DRSDCILM",      # C&I Loan Standards (net % tightening)
    # Labor
    "CCSA":         "CCSA",          # Continuing Jobless Claims
    "JTSJOL":       "JTSJOL",        # JOLTS Job Openings
    # International / Credit risk
    "DTWEXBGS":     "DTWEXBGS",      # Broad Dollar Index (goods)
}

# ── Yahoo Finance series ──────────────────────────────────────────────────────
_YF_SERIES: dict[str, str] = {
    "VIXCLS":  "^VIX",      # CBOE VIX
    "VVIX":    "^VVIX",     # Volatility of VIX
    "DXY":     "DX-Y.NYB",  # US Dollar Index
    "GOLD":    "GC=F",      # Gold futures
    "COPPER":  "HG=F",      # Copper futures
    "OIL":     "CL=F",      # Crude oil futures
    "USDJPY":  "USDJPY=X",  # USD/JPY exchange rate
    "BTC":     "BTC-USD",   # Bitcoin
    "SPX":     "^GSPC",     # S&P 500 (for BTC correlation)
    "SPY":     "SPY",       # S&P 500 ETF (for gold/equity ratio)
}

_FRED_BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv"


# ── FRED fetcher ──────────────────────────────────────────────────────────────

def _fetch_fred(series_id: str, fred_id: str, days: int) -> pd.DataFrame:
    """Fetch a FRED series via direct CSV download (no API key required)."""
    try:
        start = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        url = f"{_FRED_BASE}?id={fred_id}&vintage_date=&observation_start={start}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        df.columns = ["date", "value"]
        df["date"]  = pd.to_datetime(df["date"]).dt.tz_localize(None)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
        df["series_id"] = series_id
        return df[["series_id", "date", "value"]]
    except Exception as e:
        logger.warning(f"FRED fetch failed for {series_id} ({fred_id}): {e}")
        return pd.DataFrame()


# ── Yahoo Finance fetcher ─────────────────────────────────────────────────────

def _fetch_yf(series_id: str, ticker: str, days: int) -> pd.DataFrame:
    try:
        start = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        raw = yf.download(ticker, start=start, auto_adjust=True, progress=False)
        if raw.empty:
            return pd.DataFrame()
        raw = raw.reset_index()
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = ["_".join(str(c) for c in col).strip("_") for col in raw.columns]
        date_col  = next((c for c in raw.columns if c.lower() in ("date", "datetime")), None)
        close_col = next((c for c in raw.columns if "close" in c.lower()), None)
        if not date_col or not close_col:
            return pd.DataFrame()
        df = raw[[date_col, close_col]].copy()
        df.columns = ["date", "value"]
        df["date"]  = pd.to_datetime(df["date"]).dt.tz_localize(None)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
        df["series_id"] = series_id
        return df[["series_id", "date", "value"]]
    except Exception as e:
        logger.warning(f"YF fetch failed for {series_id} ({ticker}): {e}")
        return pd.DataFrame()


# ── DB upsert ─────────────────────────────────────────────────────────────────

def upsert_macro(df: pd.DataFrame) -> None:
    if df.empty:
        return
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO macro_indicators SELECT * FROM df")
    conn.commit()


# ── Derived series ────────────────────────────────────────────────────────────

def _compute_derived(conn) -> None:
    """Compute T10Y2Y, FEDFUNDS, M2_YOY, PCE_CORE_YOY, GOLD_EQUITY_RATIO, BTC_SPX_CORR."""

    def load_series(sid: str) -> pd.DataFrame:
        df = conn.execute("""
            SELECT CAST(date AS DATE) as date, value
            FROM macro_indicators WHERE series_id = ? ORDER BY date
        """, [sid]).df()
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df

    # T10Y2Y = 10-Year minus 2-Year (better than 3M proxy)
    ten = load_series("DGS10")
    two = load_series("DGS2")
    if not ten.empty and not two.empty:
        merged = pd.merge_asof(ten.sort_values("date"),
                               two.rename(columns={"value": "v2"}).sort_values("date"),
                               on="date", direction="nearest")
        merged = merged.dropna(subset=["value", "v2"])
        merged["spread"] = merged["value"] - merged["v2"]
        upsert_macro(pd.DataFrame({"series_id": "T10Y2Y", "date": merged["date"], "value": merged["spread"]}))
        upsert_macro(pd.DataFrame({"series_id": "FEDFUNDS", "date": merged["date"], "value": merged["v2"]}))
        logger.info(f"Computed T10Y2Y ({len(merged)} rows)")

    # M2 YoY growth (%)
    m2 = load_series("M2SL")
    if not m2.empty and len(m2) > 252:
        m2 = m2.set_index("date").sort_index()
        m2["yoy"] = m2["value"].pct_change(periods=52) * 100   # M2SL is weekly
        m2_yoy = m2["yoy"].dropna().reset_index()
        m2_yoy.columns = ["date", "value"]
        m2_yoy["series_id"] = "M2_GROWTH_YOY"
        upsert_macro(m2_yoy[["series_id", "date", "value"]])
        logger.info(f"Computed M2_GROWTH_YOY ({len(m2_yoy)} rows)")

    # PCE Core YoY (%)
    pce = load_series("PCEPILFE")
    if not pce.empty and len(pce) > 12:
        pce = pce.set_index("date").sort_index()
        pce["yoy"] = pce["value"].pct_change(periods=12) * 100   # monthly
        pce_yoy = pce["yoy"].dropna().reset_index()
        pce_yoy.columns = ["date", "value"]
        pce_yoy["series_id"] = "PCE_CORE_YOY"
        upsert_macro(pce_yoy[["series_id", "date", "value"]])
        logger.info(f"Computed PCE_CORE_YOY ({len(pce_yoy)} rows)")

    # Gold / Equity ratio
    gold = load_series("GOLD")
    spy  = load_series("SPY")
    if not gold.empty and not spy.empty:
        merged = pd.merge_asof(gold.sort_values("date"),
                               spy.rename(columns={"value": "spy"}).sort_values("date"),
                               on="date", direction="nearest")
        merged = merged.dropna(subset=["value", "spy"])
        merged["ratio"] = merged["value"] / merged["spy"].replace(0, np.nan)
        ratio_df = merged[["date", "ratio"]].dropna()
        ratio_df.columns = ["date", "value"]
        ratio_df["series_id"] = "GOLD_EQUITY_RATIO"
        upsert_macro(ratio_df[["series_id", "date", "value"]])
        logger.info(f"Computed GOLD_EQUITY_RATIO ({len(ratio_df)} rows)")

    # BTC / SPX 30-day rolling correlation
    btc = load_series("BTC")
    spx = load_series("SPX")
    if not btc.empty and not spx.empty:
        merged = pd.merge_asof(btc.sort_values("date"),
                               spx.rename(columns={"value": "spx"}).sort_values("date"),
                               on="date", direction="nearest")
        merged = merged.dropna(subset=["value", "spx"])
        btc_ret = merged["value"].pct_change()
        spx_ret = merged["spx"].pct_change()
        corr = btc_ret.rolling(30).corr(spx_ret)
        corr_df = pd.DataFrame({"date": merged["date"], "value": corr}).dropna()
        corr_df["series_id"] = "BTC_SPX_CORR_30D"
        upsert_macro(corr_df[["series_id", "date", "value"]])
        logger.info(f"Computed BTC_SPX_CORR_30D ({len(corr_df)} rows)")

    # Copper 20-day momentum
    copper = load_series("COPPER")
    if not copper.empty:
        copper = copper.set_index("date").sort_index()
        copper["ret20"] = copper["value"].pct_change(20)
        c_df = copper["ret20"].dropna().reset_index()
        c_df.columns = ["date", "value"]
        c_df["series_id"] = "COPPER_RET20"
        upsert_macro(c_df[["series_id", "date", "value"]])

    # Oil 20-day momentum
    oil = load_series("OIL")
    if not oil.empty:
        oil = oil.set_index("date").sort_index()
        oil["ret20"] = oil["value"].pct_change(20)
        o_df = oil["ret20"].dropna().reset_index()
        o_df.columns = ["date", "value"]
        o_df["series_id"] = "OIL_RET20"
        upsert_macro(o_df[["series_id", "date", "value"]])

    # USDJPY 5-day return
    usdjpy = load_series("USDJPY")
    if not usdjpy.empty:
        usdjpy = usdjpy.set_index("date").sort_index()
        usdjpy["ret5"] = usdjpy["value"].pct_change(5)
        u_df = usdjpy["ret5"].dropna().reset_index()
        u_df.columns = ["date", "value"]
        u_df["series_id"] = "USDJPY_RET5"
        upsert_macro(u_df[["series_id", "date", "value"]])

    # DXY 20-day momentum
    dxy = load_series("DXY")
    if not dxy.empty:
        dxy = dxy.set_index("date").sort_index()
        dxy["ret20"] = dxy["value"].pct_change(20)
        d_df = dxy["ret20"].dropna().reset_index()
        d_df.columns = ["date", "value"]
        d_df["series_id"] = "DXY_RET20"
        upsert_macro(d_df[["series_id", "date", "value"]])

    # Core CPI YoY (monthly, 12-period pct change)
    cpi_core = load_series("CPILFESL")
    if not cpi_core.empty and len(cpi_core) > 12:
        cpi_core = cpi_core.set_index("date").sort_index()
        cpi_core["yoy"] = cpi_core["value"].pct_change(12) * 100
        cpi_df = cpi_core["yoy"].dropna().reset_index()
        cpi_df.columns = ["date", "value"]
        cpi_df["series_id"] = "CORE_CPI_YOY"
        upsert_macro(cpi_df[["series_id", "date", "value"]])
        logger.info(f"Computed CORE_CPI_YOY ({len(cpi_df)} rows)")

    # Industrial Production: 12-month YoY change
    indpro = load_series("INDPRO")
    if not indpro.empty and len(indpro) > 12:
        indpro = indpro.set_index("date").sort_index()
        indpro["yoy"] = indpro["value"].pct_change(12) * 100
        ip_df = indpro["yoy"].dropna().reset_index()
        ip_df.columns = ["date", "value"]
        ip_df["series_id"] = "INDPRO_YOY"
        upsert_macro(ip_df[["series_id", "date", "value"]])

    # Retail Sales: 12-month YoY change
    rsxfs = load_series("RSXFS")
    if not rsxfs.empty and len(rsxfs) > 12:
        rsxfs = rsxfs.set_index("date").sort_index()
        rsxfs["yoy"] = rsxfs["value"].pct_change(12) * 100
        rs_df = rsxfs["yoy"].dropna().reset_index()
        rs_df.columns = ["date", "value"]
        rs_df["series_id"] = "RETAIL_SALES_YOY"
        upsert_macro(rs_df[["series_id", "date", "value"]])


# ── Public load functions ─────────────────────────────────────────────────────

def initial_macro_load() -> None:
    days = 365 * 7
    logger.info("Starting initial macro load (Tier 1 factors)...")
    for series_id, fred_id in _FRED_SERIES.items():
        df = _fetch_fred(series_id, fred_id, days)
        upsert_macro(df)
        logger.info(f"  FRED {series_id}: {len(df)} rows")
    for series_id, yf_ticker in _YF_SERIES.items():
        df = _fetch_yf(series_id, yf_ticker, days)
        upsert_macro(df)
        logger.info(f"  YF {series_id}: {len(df)} rows")
    _compute_derived(get_conn())


def refresh_all_macro() -> None:
    days = 120
    for series_id, fred_id in _FRED_SERIES.items():
        df = _fetch_fred(series_id, fred_id, days)
        upsert_macro(df)
    for series_id, yf_ticker in _YF_SERIES.items():
        df = _fetch_yf(series_id, yf_ticker, days)
        upsert_macro(df)
    _compute_derived(get_conn())
    logger.info("Macro refresh complete")


# ── Training data loader ──────────────────────────────────────────────────────

def load_macro_timeseries() -> pd.DataFrame:
    """
    Wide daily-forward-filled DataFrame of all macro series.
    Used by trainer for as-of date joins.
    Returns columns: date + all macro factor columns.
    """
    conn = get_conn()
    wanted = [
        "VIXCLS", "T10Y2Y", "FEDFUNDS",
        "BAMLH0A0HYM2", "BAMLC0A0CM", "DFII10",
        "M2_GROWTH_YOY", "ICSA", "NFCI", "PCE_CORE_YOY", "WALCL",
        "DXY", "DXY_RET20", "GOLD_EQUITY_RATIO",
        "COPPER_RET20", "USDJPY_RET5", "OIL_RET20",
        "BTC_SPX_CORR_30D", "VVIX",
        # Additional macro series
        "UMCSENT", "NAPM",
        "HOUST", "CSUSHPINSA",
        "INDPRO_YOY", "RETAIL_SALES_YOY",
        "CORE_CPI_YOY", "PPIACO", "T10YIE",
        "M2V", "TOTCI", "DRSDCILM",
        "CCSA", "JTSJOL",
        "DTWEXBGS",
    ]
    placeholders = ",".join("?" * len(wanted))
    raw = conn.execute(f"""
        SELECT series_id, CAST(date AS DATE) as date, value
        FROM macro_indicators
        WHERE series_id IN ({placeholders})
        ORDER BY date
    """, wanted).df()

    if raw.empty:
        return pd.DataFrame()

    raw["date"] = pd.to_datetime(raw["date"])
    wide = raw.pivot_table(index="date", columns="series_id", values="value", aggfunc="last")
    wide = wide.reset_index().sort_values("date")

    date_range = pd.date_range(wide["date"].min(), wide["date"].max(), freq="D")
    wide = wide.set_index("date").reindex(date_range).ffill().reset_index()
    wide = wide.rename(columns={"index": "date"})

    def col(name):
        return wide[name] if name in wide.columns else pd.Series(np.nan, index=wide.index)

    vix  = col("VIXCLS").fillna(20.0)
    yc   = col("T10Y2Y").fillna(0.0)
    fed  = col("FEDFUNDS").fillna(3.0)
    hy   = col("BAMLH0A0HYM2").fillna(300.0)
    ig   = col("BAMLC0A0CM").fillna(100.0)
    tips = col("DFII10").fillna(0.0)
    m2   = col("M2_GROWTH_YOY").fillna(0.0)
    icsa = col("ICSA").fillna(220.0)
    nfci = col("NFCI").fillna(0.0)
    pce  = col("PCE_CORE_YOY").fillna(2.0)
    walcl = col("WALCL").fillna(8e6)
    dxy  = col("DXY").fillna(100.0)
    dxy_ret = col("DXY_RET20").fillna(0.0)
    gold_eq = col("GOLD_EQUITY_RATIO").fillna(5.0)
    cu_ret  = col("COPPER_RET20").fillna(0.0)
    jpy_ret = col("USDJPY_RET5").fillna(0.0)
    oil_ret = col("OIL_RET20").fillna(0.0)
    btc_corr = col("BTC_SPX_CORR_30D").fillna(0.0)
    vvix = col("VVIX").fillna(90.0)

    # Additional macro series
    umcsent      = col("UMCSENT").fillna(80.0)
    ism_mfg      = col("NAPM").fillna(50.0)
    housing_st   = col("HOUST").fillna(1400.0)
    cs_hpi       = col("CSUSHPINSA").fillna(200.0)
    indpro_yoy   = col("INDPRO_YOY").fillna(0.0)
    retail_yoy   = col("RETAIL_SALES_YOY").fillna(0.0)
    core_cpi_yoy = col("CORE_CPI_YOY").fillna(2.0)
    ppi          = col("PPIACO").fillna(200.0)
    breakeven_10y = col("T10YIE").fillna(2.3)
    m2_velocity  = col("M2V").fillna(1.2)
    cons_credit  = col("TOTCI").fillna(4000.0)
    loan_stds    = col("DRSDCILM").fillna(0.0)
    cont_claims  = col("CCSA").fillna(1700.0)
    job_openings = col("JTSJOL").fillna(7000.0)
    broad_dollar = col("DTWEXBGS").fillna(110.0)

    result = pd.DataFrame({
        "date": wide["date"],
        # Core macro
        "vix":             vix.values,
        "vix_regime":      vix.apply(lambda v: 0. if v < 15 else (1. if v < 25 else (2. if v < 35 else 3.))).values,
        "yield_curve":     yc.values,
        "yield_curve_inverted": (yc < 0).astype(float).values,
        "fed_rate":        fed.values,
        "hy_spread":       hy.values,
        "ig_spread":       ig.values,
        "tips_real_yield": tips.values,
        "m2_growth_yoy":   m2.values,
        "initial_claims":  icsa.values,
        "nfci":            nfci.values,
        "pce_core_yoy":    pce.values,
        "fed_balance_sheet": walcl.values,
        # Cross-asset
        "dxy":             dxy.values,
        "dxy_ret20":       dxy_ret.values,
        "gold_equity_ratio": gold_eq.values,
        "copper_ret20":    cu_ret.values,
        "usdjpy_ret5":     jpy_ret.values,
        "oil_ret20":       oil_ret.values,
        "btc_spx_corr":    btc_corr.values,
        "vvix":            vvix.values,
        # Additional macro factors
        "consumer_sentiment":    umcsent.values,
        "ism_manufacturing":     ism_mfg.values,
        "housing_starts":        housing_st.values,
        "case_shiller_hpi":      cs_hpi.values,
        "industrial_production": indpro_yoy.values,
        "retail_sales":          retail_yoy.values,
        "core_cpi_yoy":          core_cpi_yoy.values,
        "ppi":                   ppi.values,
        "breakeven_10y":         breakeven_10y.values,
        "money_velocity":        m2_velocity.values,
        "total_consumer_credit": cons_credit.values,
        "loan_standards":        loan_stds.values,
        "continuing_claims":     cont_claims.values,
        "job_openings":          job_openings.values,
        "broad_dollar_index":    broad_dollar.values,
        "hy_spread_oas":         hy.values,  # BAMLH0A0HYM2 already fetched above
    })

    return result


def get_macro_context() -> dict:
    """Most recent macro values for inference."""
    conn = get_conn()

    def latest(sid: str, default: float = 0.0) -> float:
        row = conn.execute("""
            SELECT value FROM macro_indicators
            WHERE series_id = ? AND value IS NOT NULL
            ORDER BY date DESC LIMIT 1
        """, [sid]).fetchone()
        return float(row[0]) if row else default

    vix  = latest("VIXCLS", 20.0)
    yc   = latest("T10Y2Y", 0.5)
    fed  = latest("FEDFUNDS", 3.0)
    hy   = latest("BAMLH0A0HYM2", 300.0)
    ig   = latest("BAMLC0A0CM", 100.0)
    tips = latest("DFII10", 0.0)
    m2   = latest("M2_GROWTH_YOY", 0.0)
    icsa = latest("ICSA", 220.0)
    nfci = latest("NFCI", 0.0)
    pce  = latest("PCE_CORE_YOY", 2.0)
    walcl = latest("WALCL", 8e6)
    dxy   = latest("DXY", 100.0)
    dxy_ret = latest("DXY_RET20", 0.0)
    gold_eq = latest("GOLD_EQUITY_RATIO", 5.0)
    cu_ret  = latest("COPPER_RET20", 0.0)
    jpy_ret = latest("USDJPY_RET5", 0.0)
    oil_ret = latest("OIL_RET20", 0.0)
    btc_corr = latest("BTC_SPX_CORR_30D", 0.0)
    vvix = latest("VVIX", 90.0)

    return {
        "vix":             vix,
        "vix_regime":      0. if vix < 15 else (1. if vix < 25 else (2. if vix < 35 else 3.)),
        "yield_curve":     yc,
        "yield_curve_inverted": 1. if yc < 0 else 0.,
        "fed_rate":        fed,
        "hy_spread":       hy,
        "ig_spread":       ig,
        "tips_real_yield": tips,
        "m2_growth_yoy":   m2,
        "initial_claims":  icsa,
        "nfci":            nfci,
        "pce_core_yoy":    pce,
        "fed_balance_sheet": walcl,
        "dxy":             dxy,
        "dxy_ret20":       dxy_ret,
        "gold_equity_ratio": gold_eq,
        "copper_ret20":    cu_ret,
        "usdjpy_ret5":     jpy_ret,
        "oil_ret20":       oil_ret,
        "btc_spx_corr":    btc_corr,
        "vvix":            vvix,
        # Additional macro context
        "consumer_sentiment":    latest("UMCSENT", 80.0),
        "ism_manufacturing":     latest("NAPM", 50.0),
        "housing_starts":        latest("HOUST", 1400.0),
        "case_shiller_hpi":      latest("CSUSHPINSA", 200.0),
        "industrial_production": latest("INDPRO_YOY", 0.0),
        "retail_sales":          latest("RETAIL_SALES_YOY", 0.0),
        "core_cpi_yoy":          latest("CORE_CPI_YOY", 2.0),
        "ppi":                   latest("PPIACO", 200.0),
        "breakeven_10y":         latest("T10YIE", 2.3),
        "money_velocity":        latest("M2V", 1.2),
        "total_consumer_credit": latest("TOTCI", 4000.0),
        "loan_standards":        latest("DRSDCILM", 0.0),
        "continuing_claims":     latest("CCSA", 1700.0),
        "job_openings":          latest("JTSJOL", 7000.0),
        "broad_dollar_index":    latest("DTWEXBGS", 110.0),
        "hy_spread_oas":         hy,
    }
