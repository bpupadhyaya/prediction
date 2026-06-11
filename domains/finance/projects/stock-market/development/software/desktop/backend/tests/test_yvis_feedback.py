"""
End-to-end test for the YVIS feedback loop (Layer 5 ← Layer 6).

Self-contained: redirects the DuckDB connection to an in-memory database,
seeds synthetic prices + applied video signals, then verifies that
  1. resolve_video_signal_outcomes() resolves elapsed signals against prices,
  2. update_speaker_correlations() populates signal_correlations,
  3. get_speaker_signal_multiplier() amplifies a proven speaker and damps a poor one.

Run:  python3 -m backend.tests.test_yvis_feedback
"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta

import duckdb

from backend.database import duckdb_client


def _setup_memory_db():
    duckdb_client._local.conn = duckdb.connect(":memory:")
    duckdb_client.init_db()
    return duckdb_client._local.conn


def _seed_prices(conn, ticker: str, start: datetime, days: int, direction: str):
    """Seed `days` of daily prices rising (up) or falling (down) ~1%/day."""
    price = 100.0
    step = 1.01 if direction == "up" else 0.99
    for i in range(days):
        d = (start + timedelta(days=i)).date()
        conn.execute(
            "INSERT INTO prices (ticker, date, open, high, low, close, volume, adj_close) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [ticker, str(d), price, price, price, price, 1_000_000, price],
        )
        price *= step
    conn.commit()


def _apply_signal(conn, *, ticker, speaker, direction, created_at, parameter="price_momentum"):
    es = 1.0 if direction == "up" else -1.0
    conn.execute(
        """
        INSERT INTO user_signals
            (id, ticker, signal_type, domain, content, extracted_signal,
             weight_multiplier, confidence, source_tag, created_at, expires_at, is_active,
             speaker_name, video_id, parameter_name, horizon)
        VALUES (?, ?, 'video', 'technical', 'test', ?, 1.0, 0.9,
                'VIDEO_INTELLIGENCE', ?, ?, TRUE, ?, ?, ?, '1w')
        """,
        [str(uuid.uuid4()), ticker, es, created_at,
         (created_at + timedelta(days=30)).isoformat(), speaker, str(uuid.uuid4()), parameter],
    )
    conn.commit()


def main() -> int:
    from backend.models import online_learner as ol

    conn = _setup_memory_db()

    # Two speakers, one ticker that actually RISES over the next two weeks.
    pred_day = datetime.now() - timedelta(days=20)   # old enough for a 1w horizon
    _seed_prices(conn, "TESTCO", pred_day, days=20, direction="up")

    # GoodSpeaker calls UP (correct) 8x; BadSpeaker calls DOWN (wrong) 8x.
    for _ in range(8):
        _apply_signal(conn, ticker="TESTCO", speaker="GoodSpeaker", direction="up", created_at=pred_day)
        _apply_signal(conn, ticker="TESTCO", speaker="BadSpeaker", direction="down", created_at=pred_day)

    # 1. Resolve outcomes
    n = ol.resolve_video_signal_outcomes()
    assert n == 16, f"expected 16 resolved, got {n}"

    # 2. Correlations populated
    corr = conn.execute(
        "SELECT speaker_name, hist_accuracy, sample_size FROM signal_correlations "
        "WHERE ticker = 'ALL' AND parameter_name = 'ALL' ORDER BY speaker_name"
    ).fetchall()
    corr_map = {r[0]: (r[1], r[2]) for r in corr}
    assert "GoodSpeaker" in corr_map and "BadSpeaker" in corr_map, f"correlations missing: {corr_map}"
    assert corr_map["GoodSpeaker"][0] == 1.0, f"GoodSpeaker acc should be 1.0, got {corr_map['GoodSpeaker']}"
    assert corr_map["BadSpeaker"][0] == 0.0, f"BadSpeaker acc should be 0.0, got {corr_map['BadSpeaker']}"

    # 3. Multipliers: good speaker amplified to ~2.0, bad damped to ~0.5
    good_mult = ol.get_speaker_signal_multiplier("GoodSpeaker", "TESTCO", "price_momentum")
    bad_mult = ol.get_speaker_signal_multiplier("BadSpeaker", "TESTCO", "price_momentum")
    unknown_mult = ol.get_speaker_signal_multiplier("NeverSeen", "TESTCO", "price_momentum")
    assert good_mult == 2.0, f"good speaker mult should be 2.0, got {good_mult}"
    assert bad_mult == 0.5, f"bad speaker mult should be 0.5, got {bad_mult}"
    assert unknown_mult == 1.0, f"unknown speaker should be neutral 1.0, got {unknown_mult}"

    # 4. Below-threshold speaker stays neutral
    _apply_signal(conn, ticker="TESTCO", speaker="RareSpeaker", direction="up", created_at=pred_day)
    ol.resolve_video_signal_outcomes()
    rare_mult = ol.get_speaker_signal_multiplier("RareSpeaker", "TESTCO", "price_momentum")
    assert rare_mult == 1.0, f"speaker with 1 sample should be neutral, got {rare_mult}"

    print("PASS — YVIS feedback loop:")
    print(f"  resolved outcomes      : {n}")
    print(f"  GoodSpeaker acc/mult   : {corr_map['GoodSpeaker'][0]} / {good_mult}")
    print(f"  BadSpeaker  acc/mult   : {corr_map['BadSpeaker'][0]} / {bad_mult}")
    print(f"  unknown/rare mult      : {unknown_mult} / {rare_mult}  (neutral until {ol._CORR_MIN_SAMPLES} samples)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
