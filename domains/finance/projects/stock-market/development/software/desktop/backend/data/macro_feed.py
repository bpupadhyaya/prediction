import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from backend.database.duckdb_client import get_conn
import logging

logger = logging.getLogger(__name__)

# All macro series fetched from Yahoo Finance — no API key required.
# ^TNX = 10-Year Treasury Yield
# ^IRX = 13-Week Treasury Bill Yield (proxy for short rates / fed funds)
# ^VIX = CBOE VIX
# Yield curve slope = ^TNX - ^IRX  (≈ 10Y-2Y spread)
_YF_SERIES = {
    "DGS10":  "^TNX",   # 10-Year Treasury Yield
    "DGS3M":  "^IRX",   # 3-Month T-Bill (short-rate proxy)
    "VIXCLS": "^VIX",   # VIX
}


def _fetch_yf_series(series_id: str, yf_ticker: str, days: int) -> pd.DataFrame:
    """Fetch a single series from Yahoo Finance and store it under series_id."""
    try:
        start = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        raw = yf.download(yf_ticker, start=start, auto_adjust=True, progress=False)
        if raw.empty:
            return pd.DataFrame()
        raw = raw.reset_index()
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = ["_".join(c).strip("_") for c in raw.columns]
        date_col  = next((c for c in raw.columns if c.lower() in ("date", "datetime")), None)
        close_col = next((c for c in raw.columns if "close" in c.lower()), None)
        if not date_col or not close_col:
            return pd.DataFrame()
        df = raw[[date_col, close_col]].copy()
        df.columns = ["date", "value"]
        df["series_id"] = series_id
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
        df = df.dropna(subset=["value"])
        return df[["series_id", "date", "value"]]
    except Exception as e:
        logger.warning(f"YF fetch failed for {series_id} ({yf_ticker}): {e}")
        return pd.DataFrame()


def upsert_macro(df: pd.DataFrame) -> None:
    if df.empty:
        return
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO macro_indicators SELECT * FROM df")
    conn.commit()


def _compute_yield_curve_and_store(days: int) -> None:
    """
    Compute T10Y2Y proxy = DGS10 - DGS3M and store as series 'T10Y2Y'.
    Also store FEDFUNDS approximation = DGS3M.
    """
    conn = get_conn()
    ten = conn.execute("""
        SELECT CAST(date AS DATE) as date, value FROM macro_indicators
        WHERE series_id = 'DGS10' ORDER BY date
    """).df()
    three = conn.execute("""
        SELECT CAST(date AS DATE) as date, value as v3m FROM macro_indicators
        WHERE series_id = 'DGS3M' ORDER BY date
    """).df()

    if ten.empty or three.empty:
        return

    ten["date"] = pd.to_datetime(ten["date"])
    three["date"] = pd.to_datetime(three["date"])

    merged = pd.merge_asof(ten.sort_values("date"), three.sort_values("date"), on="date", direction="nearest")
    merged = merged.dropna(subset=["value", "v3m"])
    merged["spread"] = merged["value"] - merged["v3m"]

    spread_df = pd.DataFrame({
        "series_id": "T10Y2Y",
        "date": merged["date"],
        "value": merged["spread"],
    })
    fed_df = pd.DataFrame({
        "series_id": "FEDFUNDS",
        "date": merged["date"],
        "value": merged["v3m"],
    })
    upsert_macro(spread_df)
    upsert_macro(fed_df)
    logger.info(f"Computed T10Y2Y ({len(spread_df)} rows) and FEDFUNDS ({len(fed_df)} rows)")


def refresh_all_macro() -> None:
    for series_id, yf_ticker in _YF_SERIES.items():
        df = _fetch_yf_series(series_id, yf_ticker, days=90)
        upsert_macro(df)
        logger.info(f"Refreshed macro: {series_id} ({len(df)} rows)")
    _compute_yield_curve_and_store(days=90)


def initial_macro_load() -> None:
    for series_id, yf_ticker in _YF_SERIES.items():
        df = _fetch_yf_series(series_id, yf_ticker, days=365 * 7)
        upsert_macro(df)
        logger.info(f"Loaded macro: {series_id} ({len(df)} rows)")
    _compute_yield_curve_and_store(days=365 * 7)


def load_macro_timeseries() -> pd.DataFrame:
    """
    Load all macro indicators from DB as a daily-forward-filled wide DataFrame.
    Used by the trainer to join macro features to training data by date.
    Returns columns: date, vix, vix_regime, yield_curve, yield_curve_inverted, fed_rate
    """
    conn = get_conn()
    raw = conn.execute("""
        SELECT series_id, CAST(date AS DATE) as date, value
        FROM macro_indicators
        WHERE series_id IN ('VIXCLS', 'T10Y2Y', 'FEDFUNDS')
        ORDER BY date
    """).df()

    if raw.empty:
        return pd.DataFrame()

    raw["date"] = pd.to_datetime(raw["date"]).dt.as_unit("ns")
    wide = raw.pivot_table(index="date", columns="series_id", values="value", aggfunc="last")
    wide = wide.reset_index().sort_values("date")

    # Forward-fill to daily (FEDFUNDS is monthly, FRED data has gaps on weekends)
    date_range = pd.date_range(wide["date"].min(), wide["date"].max(), freq="D")
    wide = wide.set_index("date").reindex(date_range).ffill().reset_index()
    wide = wide.rename(columns={"index": "date"})

    vix = wide.get("VIXCLS", pd.Series(dtype=float))
    yc = wide.get("T10Y2Y", pd.Series(dtype=float))
    fed = wide.get("FEDFUNDS", pd.Series(dtype=float))

    result = pd.DataFrame({
        "date": wide["date"],
        "vix": vix.values if hasattr(vix, "values") else vix,
        "yield_curve": yc.values if hasattr(yc, "values") else yc,
        "fed_rate": fed.values if hasattr(fed, "values") else fed,
    })
    result["vix"] = result["vix"].fillna(0.0)
    result["yield_curve"] = result["yield_curve"].fillna(0.0)
    result["fed_rate"] = result["fed_rate"].fillna(0.0)
    result["vix_regime"] = result["vix"].apply(lambda v: 0.0 if v < 15 else (1.0 if v < 25 else 2.0))
    result["yield_curve_inverted"] = (result["yield_curve"] < 0).astype(float)

    return result[["date", "vix", "vix_regime", "yield_curve", "yield_curve_inverted", "fed_rate"]]


def get_macro_context() -> dict:
    """Most recent macro values for use at inference time."""
    conn = get_conn()

    def latest(sid: str) -> float:
        row = conn.execute("""
            SELECT value FROM macro_indicators
            WHERE series_id = ? AND value IS NOT NULL
            ORDER BY date DESC LIMIT 1
        """, [sid]).fetchone()
        return float(row[0]) if row else 0.0

    vix = latest("VIXCLS")
    yc = latest("T10Y2Y")
    fed = latest("FEDFUNDS")

    return {
        "vix": vix,
        "vix_regime": 0.0 if vix < 15 else (1.0 if vix < 25 else 2.0),
        "yield_curve": yc,
        "yield_curve_inverted": 1.0 if yc < 0 else 0.0,
        "fed_rate": fed,
    }
