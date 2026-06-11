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

    # ── Core market data ──────────────────────────────────────────────────────
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
            ticker            VARCHAR,
            report_date       DATE,
            pe_ratio          DOUBLE,
            pb_ratio          DOUBLE,
            eps               DOUBLE,
            revenue           DOUBLE,
            earnings_surprise DOUBLE,
            short_ratio       DOUBLE,
            short_pct_float   DOUBLE,
            PRIMARY KEY (ticker, report_date)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS earnings_history (
            ticker            VARCHAR,
            earnings_date     DATE,
            earnings_surprise DOUBLE,
            PRIMARY KEY (ticker, earnings_date)
        )
    """)

    # ── Macro / cross-asset data ──────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS macro_indicators (
            series_id   VARCHAR,
            date        DATE,
            value       DOUBLE,
            PRIMARY KEY (series_id, date)
        )
    """)

    # ── Predictions ───────────────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            ticker               VARCHAR,
            horizon              VARCHAR,
            predicted_at         TIMESTAMP,
            direction            VARCHAR,
            probability          DOUBLE,
            expected_return_low  DOUBLE,
            expected_return_high DOUBLE,
            volatility           DOUBLE,
            model_version        VARCHAR,
            regime_label         VARCHAR,
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

    # ── Regime history ────────────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS regime_history (
            as_of_date  DATE PRIMARY KEY,
            monetary    INTEGER,
            credit      INTEGER,
            volatility  INTEGER,
            yield_curve INTEGER,
            label       VARCHAR,
            recorded_at TIMESTAMP DEFAULT now()
        )
    """)

    # ── User guidance signals ─────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_signals (
            id                VARCHAR PRIMARY KEY,
            ticker            VARCHAR,
            signal_type       VARCHAR,
            domain            VARCHAR,
            content           TEXT,
            extracted_signal  DOUBLE,
            weight_multiplier DOUBLE DEFAULT 1.0,
            confidence        DOUBLE DEFAULT 0.9,
            source_tag        VARCHAR DEFAULT 'USER_OVERRIDE',
            created_at        TIMESTAMP DEFAULT now(),
            expires_at        TIMESTAMP,
            is_active         BOOLEAN DEFAULT TRUE,
            outcome_known     BOOLEAN DEFAULT FALSE,
            was_correct       BOOLEAN,
            reinforcement_count INTEGER DEFAULT 0
        )
    """)

    # ── Prediction outcomes (for online learning) ─────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prediction_outcomes (
            ticker       VARCHAR,
            horizon      VARCHAR,
            predicted_at TIMESTAMP,
            direction    VARCHAR,
            probability  DOUBLE,
            regime_label VARCHAR,
            actual_return DOUBLE,
            was_correct  BOOLEAN,
            resolved_at  TIMESTAMP DEFAULT now(),
            source_type  VARCHAR DEFAULT 'model',
            source_id    VARCHAR,
            PRIMARY KEY (ticker, horizon, predicted_at)
        )
    """)

    # ── Online learning: domain weights ──────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS signal_weights (
            domain          VARCHAR PRIMARY KEY,
            weight_multiplier DOUBLE DEFAULT 1.0,
            correct_count   INTEGER DEFAULT 0,
            total_count     INTEGER DEFAULT 0,
            last_updated    TIMESTAMP DEFAULT now()
        )
    """)

    # ── Interactive predictions (user-driven session saves) ───────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS interactive_predictions (
            id            VARCHAR PRIMARY KEY,
            ticker        VARCHAR NOT NULL,
            session_date  DATE NOT NULL,
            created_at    TIMESTAMP NOT NULL,
            user_signals  JSON NOT NULL,
            signals_count INTEGER NOT NULL,
            prob_up       DOUBLE NOT NULL,
            confidence    DOUBLE NOT NULL,
            direction     VARCHAR NOT NULL,
            notes         TEXT DEFAULT '',
            source        VARCHAR DEFAULT 'web'
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ip_ticker ON interactive_predictions(ticker)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ip_date   ON interactive_predictions(session_date)")

    # ── YouTube Video Intelligence System (YVIS) ─────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS video_sources (
            id              VARCHAR PRIMARY KEY,
            url             VARCHAR UNIQUE,
            video_id        VARCHAR,
            title           VARCHAR,
            channel_name    VARCHAR,
            channel_id      VARCHAR,
            speaker_name    VARCHAR,
            published_at    TIMESTAMP,
            duration_sec    INTEGER,
            view_count      BIGINT,
            language        VARCHAR DEFAULT 'en',
            processed_at    TIMESTAMP,
            transcript_model VARCHAR,
            status          VARCHAR DEFAULT 'pending',
            error_msg       TEXT,
            created_at      TIMESTAMP DEFAULT now()
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transcripts (
            video_id        VARCHAR PRIMARY KEY,
            full_text       TEXT,
            chunks_json     TEXT,
            word_count      INTEGER,
            language        VARCHAR,
            model_used      VARCHAR,
            transcribed_at  TIMESTAMP DEFAULT now()
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS video_signals (
            id              VARCHAR PRIMARY KEY,
            video_id        VARCHAR,
            ticker          VARCHAR,
            parameter_name  VARCHAR,
            domain          VARCHAR,
            direction       VARCHAR,
            weight          DOUBLE,
            confidence      DOUBLE,
            key_quote       TEXT,
            quote_ts_sec    INTEGER,
            extracted_at    TIMESTAMP DEFAULT now()
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS channel_tracks (
            channel_id      VARCHAR PRIMARY KEY,
            channel_name    VARCHAR,
            speaker_name    VARCHAR,
            auto_process    BOOLEAN DEFAULT TRUE,
            time_range_years INTEGER DEFAULT 5,
            last_checked_at TIMESTAMP,
            created_at      TIMESTAMP DEFAULT now()
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS signal_correlations (
            id              VARCHAR PRIMARY KEY,
            speaker_name    VARCHAR,
            ticker          VARCHAR,
            parameter_name  VARCHAR,
            hist_accuracy   DOUBLE,
            sample_size     INTEGER,
            updated_at      TIMESTAMP DEFAULT now()
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vs_ticker   ON video_signals(ticker)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vs_video    ON video_signals(video_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vsrc_channel ON video_sources(channel_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vsrc_published ON video_sources(published_at)")

    # ── Migrations: add new columns to existing tables ────────────────────────
    _safe_alter(conn, "ALTER TABLE fundamentals ADD COLUMN short_ratio DOUBLE DEFAULT 0")
    _safe_alter(conn, "ALTER TABLE fundamentals ADD COLUMN short_pct_float DOUBLE DEFAULT 0")
    _safe_alter(conn, "ALTER TABLE predictions ADD COLUMN regime_label VARCHAR")
    _safe_alter(conn, "ALTER TABLE prediction_outcomes ADD COLUMN source_type VARCHAR DEFAULT 'model'")
    _safe_alter(conn, "ALTER TABLE prediction_outcomes ADD COLUMN source_id VARCHAR")

    # ── Seed signal_weights with default domains ──────────────────────────────
    _seed_signal_weights(conn)

    conn.commit()
    # Checkpoint so ALTER TABLE migrations are written to the main db file
    # (avoids WAL replay failures with DEFAULT now() / function expressions)
    try:
        conn.execute("CHECKPOINT")
    except Exception:
        pass


def _safe_alter(conn, sql: str) -> None:
    try:
        conn.execute(sql)
    except Exception:
        pass


def _seed_signal_weights(conn) -> None:
    domains = ["macro", "technical", "momentum", "fundamental", "cross_asset", "sentiment", "geopolitical"]
    for domain in domains:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO signal_weights (domain, weight_multiplier)
                VALUES (?, 1.0)
            """, [domain])
        except Exception:
            pass
