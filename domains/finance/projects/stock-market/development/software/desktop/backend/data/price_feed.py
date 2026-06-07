import yfinance as yf
import pandas as pd
import requests
import io
import time
from datetime import datetime, timedelta
from backend.database.duckdb_client import get_conn
import logging

logger = logging.getLogger(__name__)

# Fallback: 100 large-cap S&P 500 constituents used when Wikipedia is unreachable
_FALLBACK_TICKERS = [
    "AAPL","MSFT","NVDA","AMZN","GOOGL","GOOG","META","TSLA","BRK-B","AVGO",
    "JPM","LLY","UNH","V","XOM","MA","JNJ","PG","HD","COST",
    "MRK","ABBV","CVX","CRM","NFLX","BAC","AMD","PEP","KO","TMO",
    "ACN","MCD","WMT","CSCO","ABT","LIN","TXN","ORCL","DHR","QCOM",
    "PM","INTU","GE","CAT","IBM","GS","MS","SPGI","ISRG","RTX",
    "AMGN","AXP","T","BLK","BKNG","DE","ELV","ADI","VRTX","REGN",
    "SYK","CI","PLD","CB","GILD","ADP","SCHW","MDLZ","MO","ZTS",
    "CVS","ETN","SO","DUK","NOC","MMM","CL","WM","TJX","PGR",
    "BSX","AON","HUM","MCO","EOG","OXY","USB","BDX","ITW","SLB",
    "CME","EW","APD","FCX","EMR","NSC","MMC","ICE","MPC","ROP",
]


def fetch_sp500_tickers() -> list[str]:
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; stock-prediction-app/1.0)"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        tables = pd.read_html(io.StringIO(resp.text))
        tickers = tables[0]["Symbol"].str.replace(".", "-").tolist()
        logger.info(f"Fetched {len(tickers)} tickers from Wikipedia")
        return tickers
    except Exception as e:
        logger.warning(f"Wikipedia ticker fetch failed ({e}) — using fallback list of {len(_FALLBACK_TICKERS)} tickers")
        return _FALLBACK_TICKERS


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
    return _fetch_prices_single(ticker, start)


def upsert_prices(df: pd.DataFrame) -> None:
    if df.empty:
        return
    conn = get_conn()
    conn.execute("""
        INSERT INTO prices SELECT * FROM df
        ON CONFLICT (ticker, date) DO UPDATE SET
            open      = EXCLUDED.open,
            high      = EXCLUDED.high,
            low       = EXCLUDED.low,
            close     = EXCLUDED.close,
            volume    = EXCLUDED.volume,
            adj_close = EXCLUDED.adj_close
    """)
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


def _fetch_prices_single(ticker: str, start: datetime) -> pd.DataFrame:
    """Download price history for one ticker using Ticker.history() — more reliable than yf.download()."""
    try:
        t = yf.Ticker(ticker)
        df = t.history(start=start, auto_adjust=True)
        if df.empty:
            return pd.DataFrame()
        df = df.reset_index()
        df.columns = [c.lower() for c in df.columns]
        df["ticker"] = ticker
        df["adj_close"] = df["close"]
        cols = ["ticker", "date", "open", "high", "low", "close", "volume", "adj_close"]
        return df[[c for c in cols if c in df.columns]].dropna(subset=["close"])
    except Exception:
        return pd.DataFrame()


def initial_load(tickers: list[str]) -> None:
    conn = get_conn()
    existing = {r[0] for r in conn.execute("SELECT DISTINCT ticker FROM prices").fetchall()}
    pending = [t for t in tickers if t not in existing]
    logger.info(f"Loading price data: {len(pending)} new tickers ({len(existing)} already in DB)...")

    start = datetime.today() - timedelta(days=365 * 5)
    total_ok = 0
    total = len(pending)

    for i, ticker in enumerate(pending):
        if i % 25 == 0:
            logger.info(f"  Progress: {i}/{total} ({total_ok} loaded so far)...")
        df = _fetch_prices_single(ticker, start)
        if not df.empty:
            upsert_prices(df)
            total_ok += 1
        else:
            # Retry once with a longer pause
            time.sleep(2)
            df = _fetch_prices_single(ticker, start)
            if not df.empty:
                upsert_prices(df)
                total_ok += 1
        time.sleep(0.4)

    logger.info(f"Price download complete: {total_ok}/{total} tickers loaded.")
    # Stock metadata (name, sector, market cap) is fetched on-demand when users look up
    # individual stocks — not during initial setup to avoid Yahoo Finance rate limits.
