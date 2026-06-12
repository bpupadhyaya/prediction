import yfinance as yf
import pandas as pd
import requests
import io
import time
from datetime import datetime, timedelta, date
from backend.database.duckdb_client import get_conn
import logging

logger = logging.getLogger(__name__)

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
        logger.warning(f"Wikipedia ticker fetch failed ({e}) — using fallback list")
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


def fetch_fundamentals(ticker: str) -> dict | None:
    """
    Fetch earnings quality + short interest signals from yfinance.
    These are point-in-time proxies for recent fundamental data.
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info

        earnings_qoq_growth = float(info.get("earningsQuarterlyGrowth") or 0.0)
        trailing_eps = float(info.get("trailingEps") or 0.0)
        forward_eps = float(info.get("forwardEps") or 0.0)
        short_ratio = float(info.get("shortRatio") or 0.0)
        short_pct_float = float(info.get("shortPercentOfFloat") or 0.0)
        pe_ratio = float(info.get("trailingPE") or 0.0)
        pb_ratio = float(info.get("priceToBook") or 0.0)
        revenue = float(info.get("totalRevenue") or 0.0)

        # Clamp outliers that indicate bad data
        if pe_ratio > 1000:
            pe_ratio = 0.0
        if short_ratio > 100:
            short_ratio = 0.0

        return {
            "ticker": ticker,
            "report_date": date.today().isoformat(),
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "eps": trailing_eps,
            "revenue": revenue,
            "earnings_surprise": earnings_qoq_growth,
            "short_ratio": short_ratio,
            "short_pct_float": short_pct_float,
        }
    except Exception as e:
        logger.warning(f"Could not fetch fundamentals for {ticker}: {e}")
        return None


def fetch_earnings_history(ticker: str) -> pd.DataFrame:
    """
    Fetch historical earnings dates with surprise data from yfinance.
    Returns point-in-time earnings surprise for up to ~8 quarters.
    """
    try:
        t = yf.Ticker(ticker)
        df = t.earnings_dates
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.reset_index()
        df.columns = [str(c).lower().replace(" ", "_").replace("(", "").replace(")", "") for c in df.columns]

        # Standardize column names across yfinance versions
        date_col = next((c for c in df.columns if "date" in c or "earnings" in c), None)
        est_col = next((c for c in df.columns if "estimate" in c), None)
        act_col = next((c for c in df.columns if "reported" in c or "actual" in c), None)

        if not date_col or not est_col or not act_col:
            return pd.DataFrame()

        df = df.rename(columns={date_col: "earnings_date", est_col: "eps_estimate", act_col: "reported_eps"})
        df["ticker"] = ticker
        df = df[["ticker", "earnings_date", "eps_estimate", "reported_eps"]].dropna()
        df = df[df["eps_estimate"] != 0]  # Avoid division by zero
        df["earnings_surprise"] = (df["reported_eps"] - df["eps_estimate"]) / df["eps_estimate"].abs()
        df["earnings_surprise"] = df["earnings_surprise"].clip(-2.0, 2.0)
        df["earnings_date"] = pd.to_datetime(df["earnings_date"]).dt.tz_localize(None).dt.date

        return df[["ticker", "earnings_date", "earnings_surprise"]]
    except Exception as e:
        logger.warning(f"Could not fetch earnings history for {ticker}: {e}")
        return pd.DataFrame()


def upsert_prices(df: pd.DataFrame) -> None:
    if df.empty:
        return
    df = df.drop_duplicates(subset=["ticker", "date"], keep="last")
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


def upsert_fundamentals(data: dict) -> None:
    conn = get_conn()
    conn.execute("""
        INSERT OR REPLACE INTO fundamentals
            (ticker, report_date, pe_ratio, pb_ratio, eps, revenue,
             earnings_surprise, short_ratio, short_pct_float)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        data["ticker"], data["report_date"], data["pe_ratio"], data["pb_ratio"],
        data["eps"], data["revenue"], data["earnings_surprise"],
        data["short_ratio"], data["short_pct_float"],
    ])
    conn.commit()


def upsert_earnings_history(df: pd.DataFrame) -> None:
    if df.empty:
        return
    conn = get_conn()
    conn.execute("""
        INSERT OR REPLACE INTO earnings_history
            (ticker, earnings_date, earnings_surprise)
        SELECT ticker, earnings_date, earnings_surprise FROM df
    """)
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


def refresh_ticker_fundamentals(ticker: str) -> None:
    """Refresh fundamentals + earnings history + insider activity for one ticker."""
    fund = fetch_fundamentals(ticker)
    if fund:
        upsert_fundamentals(fund)
    hist = fetch_earnings_history(ticker)
    upsert_earnings_history(hist)
    # SEC EDGAR Form 4 insider activity (best-effort — never blocks the refresh).
    try:
        from backend.data.insider_feed import refresh_insider_signal
        refresh_insider_signal(ticker)
    except Exception:
        pass


def _fetch_prices_single(ticker: str, start: datetime) -> pd.DataFrame:
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


def ensure_ticker_data(ticker: str, min_bars: int = 260) -> bool:
    """
    Make ANY symbol predictable on demand — local or global stock, crypto pair,
    ETF, index. If the ticker has too little price history in the DB, fetch ~5y
    from Yahoo and upsert it (plus best-effort fundamentals). Returns True when
    enough history exists for the prediction pipeline afterwards.
    """
    ticker = ticker.upper()
    conn = get_conn()
    try:
        n = conn.execute(
            "SELECT COUNT(*) FROM prices WHERE ticker = ?", [ticker]
        ).fetchone()[0]
    except Exception:
        n = 0
    if n >= min_bars:
        return True

    start = datetime.today() - timedelta(days=365 * 5)
    df = _fetch_prices_single(ticker, start)
    if df.empty:
        return n >= min_bars
    upsert_prices(df)
    try:
        refresh_ticker_fundamentals(ticker)
    except Exception:
        pass
    # The predictor's cross-sectional cache is built once per day — it has never
    # seen this ticker, so force a rebuild or the prediction falls back to neutral.
    try:
        from backend.models.predictor import invalidate_cache
        invalidate_cache()
    except Exception:
        pass
    logger.info(f"On-demand data load for {ticker}: {len(df)} bars")
    return len(df) >= min_bars or n + len(df) >= min_bars


def initial_load(tickers: list[str]) -> None:
    conn = get_conn()
    existing = {r[0] for r in conn.execute("SELECT DISTINCT ticker FROM prices").fetchall()}
    pending = [t for t in tickers if t not in existing]
    logger.info(f"Loading price data: {len(pending)} new tickers ({len(existing)} already in DB)...")

    start = datetime.today() - timedelta(days=365 * 5)
    total_ok = 0

    for i, ticker in enumerate(pending):
        if i % 25 == 0:
            logger.info(f"  Progress: {i}/{len(pending)} ({total_ok} loaded)...")
        df = _fetch_prices_single(ticker, start)
        if not df.empty:
            upsert_prices(df)
            total_ok += 1
        else:
            time.sleep(2)
            df = _fetch_prices_single(ticker, start)
            if not df.empty:
                upsert_prices(df)
                total_ok += 1
        time.sleep(0.4)

    logger.info(f"Price download complete: {total_ok}/{len(pending)} tickers loaded.")
