import pandas as pd
from datetime import datetime, timedelta
from backend.database.duckdb_client import get_conn
from backend.config import FRED_API_KEY
import logging

logger = logging.getLogger(__name__)

# Key FRED series for macro context
FRED_SERIES = {
    "DGS10":   "10-Year Treasury Yield",
    "DGS2":    "2-Year Treasury Yield",
    "FEDFUNDS": "Fed Funds Rate",
    "CPIAUCSL": "CPI (Inflation)",
    "UNRATE":  "Unemployment Rate",
    "VIXCLS":  "VIX Volatility Index",
    "T10Y2Y":  "10Y-2Y Yield Spread",
    "GDP":     "GDP Growth",
}


def fetch_fred_series(series_id: str, days: int = 365 * 5) -> pd.DataFrame:
    try:
        from fredapi import Fred
        if not FRED_API_KEY:
            logger.warning("No FRED_API_KEY set — skipping macro data")
            return pd.DataFrame()
        fred = Fred(api_key=FRED_API_KEY)
        start = datetime.today() - timedelta(days=days)
        data = fred.get_series(series_id, observation_start=start)
        df = data.reset_index()
        df.columns = ["date", "value"]
        df["series_id"] = series_id
        df = df.dropna()
        return df[["series_id", "date", "value"]]
    except Exception as e:
        logger.warning(f"Could not fetch FRED series {series_id}: {e}")
        return pd.DataFrame()


def upsert_macro(df: pd.DataFrame) -> None:
    if df.empty:
        return
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO macro_indicators SELECT * FROM df")
    conn.commit()


def refresh_all_macro() -> None:
    for series_id in FRED_SERIES:
        df = fetch_fred_series(series_id, days=30)
        upsert_macro(df)
        logger.info(f"Refreshed macro: {series_id}")


def initial_macro_load() -> None:
    for series_id in FRED_SERIES:
        df = fetch_fred_series(series_id, days=365 * 5)
        upsert_macro(df)
        logger.info(f"Loaded macro: {series_id}")
