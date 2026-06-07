from fastapi import APIRouter, HTTPException
from backend.database.duckdb_client import get_conn
from backend.data.price_feed import fetch_stock_info, upsert_stock_info

router = APIRouter()


@router.get("/search")
def search_stocks(q: str):
    conn = get_conn()
    rows = conn.execute("""
        SELECT ticker, name, sector, market_cap
        FROM stocks
        WHERE ticker ILIKE ? OR name ILIKE ?
        ORDER BY market_cap DESC NULLS LAST
        LIMIT 20
    """, [f"%{q}%", f"%{q}%"]).fetchall()
    return [{"ticker": r[0], "name": r[1], "sector": r[2], "market_cap": r[3]} for r in rows]


@router.get("/{ticker}/prices")
def get_prices(ticker: str, days: int = 365):
    conn = get_conn()
    rows = conn.execute("""
        SELECT date, open, high, low, close, volume, adj_close
        FROM prices
        WHERE ticker = ?
        ORDER BY date DESC
        LIMIT ?
    """, [ticker.upper(), days]).fetchall()
    if not rows:
        return []   # empty list — frontend handles "no data" gracefully
    return [
        {"date": str(r[0]), "open": r[1], "high": r[2],
         "low": r[3], "close": r[4], "volume": r[5], "adj_close": r[6]}
        for r in rows
    ]


@router.post("/{ticker}/fetch")
def fetch_ticker_on_demand(ticker: str):
    """Download 5-year price history for a ticker not yet in the database."""
    from backend.data.price_feed import refresh_ticker
    t = ticker.upper()
    success = refresh_ticker(t, full=True)
    if not success:
        raise HTTPException(status_code=404, detail=f"Could not fetch data for {t} — it may be delisted or invalid")
    return {"ticker": t, "status": "fetched"}


@router.get("/{ticker}/info")
def get_stock_info(ticker: str):
    t = ticker.upper()
    conn = get_conn()
    row = conn.execute("""
        SELECT ticker, name, sector, industry, market_cap, updated_at
        FROM stocks WHERE ticker = ?
    """, [t]).fetchone()
    if not row:
        # Fetch on demand and cache — avoids bulk metadata download during setup
        info = fetch_stock_info(t)
        if not info:
            raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
        upsert_stock_info(info)
        return {"ticker": info["ticker"], "name": info["name"], "sector": info["sector"],
                "industry": info["industry"], "market_cap": info["market_cap"], "updated_at": None}
    return {"ticker": row[0], "name": row[1], "sector": row[2],
            "industry": row[3], "market_cap": row[4], "updated_at": str(row[5])}
