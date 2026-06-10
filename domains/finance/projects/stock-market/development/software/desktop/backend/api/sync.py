from fastapi import APIRouter, BackgroundTasks
from backend.data.price_feed import refresh_ticker
from backend.data.macro_feed import refresh_all_macro, initial_macro_load
from backend.models.trainer import retrain_if_needed
from backend.database.duckdb_client import get_conn
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

_refresh_status = {"running": False, "last_completed": None, "message": ""}
_macro_init_status: dict = {"running": False, "last_result": None}


@router.post("/macro-init")
def trigger_macro_init(background_tasks: BackgroundTasks):
    """Fetch 7 years of history for all 85+ FRED and 65+ YF series (one-time bootstrap)."""
    if _macro_init_status["running"]:
        return {"status": "already_running", "message": "Initial macro load already in progress"}
    _macro_init_status["running"] = True
    background_tasks.add_task(_run_macro_init)
    return {"status": "started", "message": "Initial macro load started in background (fetches ~150 series × 7 years)"}


@router.get("/macro-init/status")
def macro_init_status():
    return _macro_init_status


def _run_macro_init():
    try:
        initial_macro_load()
        _macro_init_status["last_result"] = {"status": "ok"}
        logger.info("Initial macro load complete via API")
    except Exception as e:
        logger.error(f"Initial macro load failed: {e}", exc_info=True)
        _macro_init_status["last_result"] = {"status": "error", "error": str(e)}
    finally:
        _macro_init_status["running"] = False


@router.post("/refresh")
def trigger_refresh(background_tasks: BackgroundTasks):
    if _refresh_status["running"]:
        return {"status": "already_running", "message": "Refresh already in progress"}
    _refresh_status["running"] = True   # set before adding task to close the race window
    _refresh_status["message"] = "Starting..."
    background_tasks.add_task(_run_refresh)
    return {"status": "started", "message": "Data refresh started in background"}


@router.get("/status")
def refresh_status():
    try:
        if _refresh_status["last_completed"] is None:
            conn = get_conn()
            count = int(conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0])
            if count > 0:
                max_date = conn.execute("SELECT MAX(date) FROM prices").fetchone()[0]
                return {**_refresh_status, "last_completed": str(max_date),
                        "message": f"Setup data loaded ({count:,} price bars through {max_date})"}
        return _refresh_status
    except Exception as e:
        logger.error(f"refresh_status failed: {e}")
        return {**_refresh_status, "message": f"Status check error: {e}"}


def _run_refresh():
    global _refresh_status
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
