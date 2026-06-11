import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def run_daily_refresh() -> None:
    from backend.data.price_feed import fetch_sp500_tickers, refresh_ticker, refresh_ticker_fundamentals
    from backend.data.macro_feed import refresh_all_macro
    from backend.models.trainer import retrain_if_needed

    logger.info(f"Daily refresh started at {datetime.now()}")

    from backend.database.duckdb_client import get_conn
    conn = get_conn()
    tickers = [r[0] for r in conn.execute("SELECT DISTINCT ticker FROM prices").fetchall()]
    logger.info(f"Refreshing prices for {len(tickers)} tickers...")
    for ticker in tickers:
        refresh_ticker(ticker, full=False)

    logger.info("Refreshing fundamentals (earnings + short interest)...")
    for i, ticker in enumerate(tickers):
        if i % 50 == 0:
            logger.info(f"  Fundamentals progress: {i}/{len(tickers)}")
        refresh_ticker_fundamentals(ticker)

    refresh_all_macro()
    retrain_if_needed()

    logger.info(f"Daily refresh complete at {datetime.now()}")


def run_initial_data_load() -> None:
    """Load macro + fundamentals data on first run (or when DB is sparse)."""
    from backend.data.macro_feed import initial_macro_load
    from backend.data.price_feed import refresh_ticker_fundamentals
    from backend.database.duckdb_client import get_conn

    logger.info("Initial macro load...")
    initial_macro_load()

    conn = get_conn()
    tickers = [r[0] for r in conn.execute("SELECT DISTINCT ticker FROM prices").fetchall()]
    logger.info(f"Initial fundamentals load for {len(tickers)} tickers...")
    for i, ticker in enumerate(tickers):
        if i % 50 == 0:
            logger.info(f"  Fundamentals: {i}/{len(tickers)}")
        refresh_ticker_fundamentals(ticker)

    logger.info("Initial data load complete.")


def run_outcome_resolution() -> None:
    """Resolve elapsed predictions/signals and feed accuracy back into the
    online-learning weights. Runs nightly after fresh prices are in."""
    from backend.models.online_learner import (
        resolve_outcomes,
        resolve_interactive_outcomes,
        resolve_video_signal_outcomes,
        update_domain_weights,
        update_interactive_accuracy_weights,
        update_speaker_correlations,
    )
    logger.info("Outcome resolution started...")
    n_model = resolve_outcomes()
    n_inter = resolve_interactive_outcomes()
    n_video = resolve_video_signal_outcomes()
    # Feed resolved outcomes back into the weighting layers (Layer 5).
    update_domain_weights()
    update_interactive_accuracy_weights()
    update_speaker_correlations()
    logger.info(
        f"Outcome resolution complete — model={n_model}, interactive={n_inter}, video={n_video}"
    )


def start_scheduler() -> None:
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_daily_refresh, "cron", hour=22, minute=0)
    scheduler.add_job(run_outcome_resolution, "cron", hour=2, minute=30, id="resolve_outcomes")
    scheduler.start()
    logger.info(
        "Scheduler started — daily refresh at 22:00 UTC, outcome resolution + "
        "online-learning weight updates at 02:30 UTC"
    )
