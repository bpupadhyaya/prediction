import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from backend.database.duckdb_client import get_conn
import logging

logger = logging.getLogger(__name__)


def fetch_sp500_tickers() -> list[str]:
    try:
        tables = pd.read_html(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        )
        return tables[0]["Symbol"].str.replace(".", "-").tolist()
    except Exception as e:
        logger.error(f"Failed to fetch S&P 500 tickers: {e}")
        return []


def fetch_stock_info(ticker: str) -> dict | None:
    try:
        info = yf.Ticker(ticker).info
        return {
            "ticker": ticker,
            "name": info.get("longName", ""),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "market_cap": info.get("marketCap", 0),
        }
    except Exception as e:
        logger.warning(f"Could not fetch info for {ticker}: {e}")
        return None


def fetch_prices(ticker: str, days: int = 365 * 5) -> pd.DataFrame:
    start = datetime.today() - timedelta(days=days)
    try:
        df = yf.download(ticker, start=start, progress=False, auto_adjust=True)
        if df.empty:
            return pd.DataFrame()
        df = df.reset_index()
        df.columns = [c.lower() for c in df.columns]
        df["ticker"] = ticker
        df["adj_close"] = df["close"]
        return df[["ticker", "date", "open", "high", "low", "close", "volume", "adj_close"]]
    except Exception as e:
        logger.warning(f"Could not fetch prices for {ticker}: {e}")
        return pd.DataFrame()


def upsert_prices(df: pd.DataFrame) -> None:
    if df.empty:
        return
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO prices SELECT * FROM df")
    conn.commit()


def upsert_stock_info(info: dict) -> None:
    conn = get_conn()
    conn.execute("""
        INSERT OR REPLACE INTO stocks (ticker, name, sector, industry, market_cap, updated_at)
        VALUES (?, ?, ?, ?, ?, now())
    """, [info["ticker"], info["name"], info["sector"], info["industry"], info["market_cap"]])
    conn.commit()


def refresh_ticker(ticker: str, full: bool = False) -> bool:
    days = 365 * 5 if full else 30
    df = fetch_prices(ticker, days=days)
    if df.empty:
        return False
    upsert_prices(df)
    info = fetch_stock_info(ticker)
    if info:
        upsert_stock_info(info)
    return True


def initial_load(tickers: list[str]) -> None:
    logger.info(f"Loading initial price data for {len(tickers)} tickers...")
    for i, ticker in enumerate(tickers):
        if i % 50 == 0:
            logger.info(f"  Progress: {i}/{len(tickers)}")
        refresh_ticker(ticker, full=True)
