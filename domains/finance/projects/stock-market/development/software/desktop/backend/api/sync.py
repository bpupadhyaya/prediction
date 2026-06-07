from fastapi import APIRouter, BackgroundTasks
from backend.data.price_feed import refresh_ticker
from backend.data.macro_feed import refresh_all_macro
from backend.models.trainer import retrain_if_needed
from backend.database.duckdb_client import get_conn
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

_refresh_status = {"running": False, "last_completed": None, "message": ""}


@router.post("/refresh")
def trigger_refresh(background_tasks: BackgroundTasks):
    if _refresh_status["running"]:
        return {"status": "already_running", "message": "Refresh already in progress"}
    background_tasks.add_task(_run_refresh)
    return {"status": "started", "message": "Data refresh started in background"}


@router.get("/status")
def refresh_status():
    if _refresh_status["last_completed"] is None:
        conn = get_conn()
        count = conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0]
        if count > 0:
            max_date = conn.execute("SELECT MAX(date) FROM prices").fetchone()[0]
            return {**_refresh_status, "last_completed": str(max_date),
                    "message": f"Setup data loaded ({count:,} price bars through {max_date})"}
    return _refresh_status


def _run_refresh():
    global _refresh_status
    _refresh_status["running"] = True
    _refresh_status["message"] = "Fetching latest prices..."
    try:
        conn = get_conn()
        tickers = [r[0] for r in conn.execute("SELECT DISTINCT ticker FROM prices").fetchall()]
        for i, ticker in enumerate(tickers):
            _refresh_status["message"] = f"Refreshing {ticker} ({i+1}/{len(tickers)})"
            refresh_ticker(ticker, full=False)

        _refresh_status["message"] = "Refreshing macro indicators..."
        refresh_all_macro()

        _refresh_status["message"] = "Checking model accuracy..."
        retrain_if_needed()

        from datetime import datetime
        _refresh_status["last_completed"] = datetime.now().isoformat()
        _refresh_status["message"] = "Refresh complete"
    except Exception as e:
        logger.error(f"Refresh failed: {e}")
        _refresh_status["message"] = f"Refresh failed: {e}"
    finally:
        _refresh_status["running"] = False
