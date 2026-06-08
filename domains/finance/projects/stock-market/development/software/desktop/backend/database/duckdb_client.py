import duckdb
import threading
from backend.config import DB_PATH

_local = threading.local()


def get_conn() -> duckdb.DuckDBPyConnection:
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = duckdb.connect(str(DB_PATH))
    return _local.conn


def init_db() -> None:
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            ticker      VARCHAR PRIMARY KEY,
            name        VARCHAR,
            sector      VARCHAR,
            industry    VARCHAR,
            market_cap  DOUBLE,
            updated_at  TIMESTAMP DEFAULT now()
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            ticker    VARCHAR,
            date      DATE,
            open      DOUBLE,
            high      DOUBLE,
            low       DOUBLE,
            close     DOUBLE,
            volume    BIGINT,
            adj_close DOUBLE,
            PRIMARY KEY (ticker, date)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fundamentals (
            ticker          VARCHAR,
            report_date     DATE,
            pe_ratio        DOUBLE,
            pb_ratio        DOUBLE,
            eps             DOUBLE,
            revenue         DOUBLE,
            earnings_surprise DOUBLE,
            short_ratio     DOUBLE,
            short_pct_float DOUBLE,
            PRIMARY KEY (ticker, report_date)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS earnings_history (
            ticker           VARCHAR,
            earnings_date    DATE,
            earnings_surprise DOUBLE,
            PRIMARY KEY (ticker, earnings_date)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS macro_indicators (
            series_id   VARCHAR,
            date        DATE,
            value       DOUBLE,
            PRIMARY KEY (series_id, date)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            ticker           VARCHAR,
            horizon          VARCHAR,
            predicted_at     TIMESTAMP,
            direction        VARCHAR,
            probability      DOUBLE,
            expected_return_low  DOUBLE,
            expected_return_high DOUBLE,
            volatility       DOUBLE,
            model_version    VARCHAR,
            PRIMARY KEY (ticker, horizon, predicted_at)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS accuracy_log (
            ticker               VARCHAR,
            horizon              VARCHAR,
            period_end           DATE,
            directional_accuracy DOUBLE,
            sample_size          INTEGER,
            PRIMARY KEY (ticker, horizon, period_end)
        )
    """)

    # Migrate: add new columns to fundamentals if upgrading from older schema
    try:
        conn.execute("ALTER TABLE fundamentals ADD COLUMN short_ratio DOUBLE DEFAULT 0")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE fundamentals ADD COLUMN short_pct_float DOUBLE DEFAULT 0")
    except Exception:
        pass

    conn.commit()
