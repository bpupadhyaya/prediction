import argparse
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def run_daily_refresh() -> None:
    from backend.data.price_feed import fetch_sp500_tickers, refresh_ticker
    from backend.data.macro_feed import refresh_all_macro
    from backend.models.trainer import retrain_if_needed

    logger.info(f"Daily refresh started at {datetime.now()}")

    tickers = fetch_sp500_tickers()
    for ticker in tickers:
        refresh_ticker(ticker, full=False)

    refresh_all_macro()
    retrain_if_needed()

    logger.info(f"Daily refresh complete at {datetime.now()}")


def start_scheduler() -> None:
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    # Run daily at 5pm ET (22:00 UTC) — after market close
    scheduler.add_job(run_daily_refresh, "cron", hour=22, minute=0)
    scheduler.start()
    logger.info("Scheduler started — daily refresh at 22:00 UTC")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run one refresh and exit")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.once:
        try:
            run_daily_refresh()
        except Exception as e:
            logger.warning(f"Background refresh failed (offline?): {e}")
    else:
        import time
        start_scheduler()
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            pass
