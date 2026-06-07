import duckdb
from backend.config import DB_PATH

_conn: duckdb.DuckDBPyConnection | None = None


def get_conn() -> duckdb.DuckDBPyConnection:
    global _conn
    if _conn is None:
        _conn = duckdb.connect(str(DB_PATH))
    return _conn


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
            ticker  VARCHAR,
            date    DATE,
            open    DOUBLE,
            high    DOUBLE,
            low     DOUBLE,
            close   DOUBLE,
            volume  BIGINT,
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
            PRIMARY KEY (ticker, report_date)
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
            ticker      VARCHAR,
            horizon     VARCHAR,
            predicted_at TIMESTAMP,
            direction   VARCHAR,
            probability DOUBLE,
            expected_return_low  DOUBLE,
            expected_return_high DOUBLE,
            volatility  DOUBLE,
            model_version VARCHAR,
            PRIMARY KEY (ticker, horizon, predicted_at)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS accuracy_log (
            ticker      VARCHAR,
            horizon     VARCHAR,
            period_end  DATE,
            directional_accuracy DOUBLE,
            sample_size INTEGER,
            PRIMARY KEY (ticker, horizon, period_end)
        )
    """)
    conn.commit()
