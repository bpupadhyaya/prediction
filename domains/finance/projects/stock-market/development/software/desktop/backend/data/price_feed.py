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
    conn = get_conn()
    existing = {r[0] for r in conn.execute("SELECT DISTINCT ticker FROM prices").fetchall()}
    pending = [t for t in tickers if t not in existing]
    logger.info(f"Loading price data: {len(pending)} new tickers ({len(existing)} already in DB)...")

    batch_size = 50
    start = datetime.today() - timedelta(days=365 * 5)
    total_ok = 0

    for i in range(0, len(pending), batch_size):
        batch = pending[i:i + batch_size]
        logger.info(f"  Batch {i // batch_size + 1}/{(len(pending) + batch_size - 1) // batch_size}: {len(batch)} tickers...")
        try:
            df = yf.download(batch, start=start, progress=False, auto_adjust=True, group_by="ticker")
            if df.empty:
                continue
            # Multi-ticker download returns a MultiIndex DataFrame
            for ticker in batch:
                try:
                    if len(batch) == 1:
                        tdf = df.copy()
                    else:
                        tdf = df[ticker].copy() if ticker in df.columns.get_level_values(0) else pd.DataFrame()
                    if tdf.empty or tdf["Close"].isna().all():
                        continue
                    tdf = tdf.reset_index()
                    tdf.columns = [c.lower() for c in tdf.columns]
                    tdf["ticker"] = ticker
                    tdf["adj_close"] = tdf["close"]
                    tdf = tdf[["ticker", "date", "open", "high", "low", "close", "volume", "adj_close"]].dropna()
                    if not tdf.empty:
                        upsert_prices(tdf)
                        total_ok += 1
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"  Batch failed: {e}")
        time.sleep(1)

    logger.info(f"Price download complete: {total_ok}/{len(pending)} tickers loaded.")

    # Fetch stock info individually (lightweight)
    logger.info("Fetching stock metadata...")
    for i, ticker in enumerate(tickers):
        if i % 100 == 0:
            logger.info(f"  Metadata {i}/{len(tickers)}...")
        info = fetch_stock_info(ticker)
        if info:
            upsert_stock_info(info)
        time.sleep(0.05)
