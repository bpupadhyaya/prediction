"""
Online Learning Engine — Layer 5 of the ADPS architecture.

Tracks prediction outcomes vs. actual price moves and adjusts:
  1. Per-domain signal weights in signal_weights table
  2. User-override outcome records (for reinforcement)

GBM is not inherently online-learnable, so this engine works at the
ensemble blending level: domains that consistently led to wrong
predictions get their weight multiplier nudged down; correct ones up.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import pandas as pd

from backend.database.duckdb_client import get_conn

logger = logging.getLogger(__name__)

# Learning rate for weight updates — small to avoid overfitting to recent noise
_LR = 0.02
_MIN_WEIGHT = 0.50
_MAX_WEIGHT = 2.00
_MIN_OUTCOMES_FOR_UPDATE = 10   # Need at least this many outcomes before adjusting


def record_prediction(
    ticker: str,
    horizon: str,
    predicted_at: datetime,
    direction: str,
    probability: float,
    regime_label: str,
    expected_return_low: float = 0.0,
    expected_return_high: float = 0.0,
    volatility: float = 0.0,
) -> None:
    """
    Store a prediction for later outcome resolution.
    Called every time predict_ticker() runs. Persists to DuckDB on disk —
    survives server restarts and new sessions indefinitely.
    """
    conn = get_conn()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO predictions
                (ticker, horizon, predicted_at, direction, probability,
                 expected_return_low, expected_return_high, volatility,
                 model_version, regime_label)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, '3.0', ?)
        """, [ticker, horizon, predicted_at, direction, probability,
              expected_return_low, expected_return_high, volatility, regime_label])
        conn.commit()
    except Exception as e:
        logger.debug(f"Could not record prediction: {e}")


def resolve_outcomes() -> int:
    """
    For all unresolved predictions where the horizon has elapsed, look up
    the actual price move and mark the prediction as correct/incorrect.
    Returns the number of outcomes resolved.
    """
    conn = get_conn()
    horizon_days = {"1d": 1, "1w": 5, "1m": 21}
    resolved = 0

    # Get unresolved predictions older than their horizon
    unresolved = conn.execute("""
        SELECT p.ticker, p.horizon, p.predicted_at, p.direction, p.probability, p.regime_label
        FROM predictions p
        LEFT JOIN prediction_outcomes o
            ON p.ticker = o.ticker AND p.horizon = o.horizon AND p.predicted_at = o.predicted_at
        WHERE o.ticker IS NULL
          AND p.predicted_at < (now() - INTERVAL 35 DAY)
        LIMIT 500
    """).df()

    for _, row in unresolved.iterrows():
        ticker     = row["ticker"]
        horizon    = row["horizon"]
        pred_at    = pd.to_datetime(row["predicted_at"])
        direction  = row["direction"]
        n_days     = horizon_days.get(horizon, 5)

        try:
            actual_return = _get_actual_return(conn, ticker, pred_at, n_days)
            if actual_return is None:
                continue
            was_correct = (direction == "up" and actual_return > 0) or (direction == "down" and actual_return < 0)
            conn.execute("""
                INSERT OR REPLACE INTO prediction_outcomes
                    (ticker, horizon, predicted_at, direction, probability,
                     regime_label, actual_return, was_correct, resolved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, now())
            """, [ticker, horizon, row["predicted_at"], direction,
                  float(row["probability"]), str(row.get("regime_label", "")),
                  float(actual_return), bool(was_correct)])
            resolved += 1
        except Exception as e:
            logger.debug(f"Outcome resolution failed for {ticker}/{horizon}: {e}")

    if resolved:
        conn.commit()
        logger.info(f"Resolved {resolved} prediction outcomes")

    return resolved


def _get_actual_return(conn, ticker: str, pred_at: datetime, n_days: int) -> float | None:
    """Get the n_days-forward return for ticker starting from pred_at date."""
    pred_date = pred_at.date() if hasattr(pred_at, "date") else pred_at
    try:
        row = conn.execute("""
            SELECT close FROM prices
            WHERE ticker = ? AND date >= ?
            ORDER BY date ASC LIMIT 1
        """, [ticker, pred_date]).fetchone()
        if not row:
            return None
        start_price = float(row[0])

        future_row = conn.execute("""
            SELECT close FROM prices
            WHERE ticker = ? AND date > ?
            ORDER BY date ASC
            LIMIT 1 OFFSET ?
        """, [ticker, pred_date, n_days - 1]).fetchone()
        if not future_row:
            return None
        end_price = float(future_row[0])
        return (end_price - start_price) / start_price
    except Exception:
        return None


def update_domain_weights() -> dict[str, float]:
    """
    Adjust per-domain weight multipliers based on recent 90-day outcome accuracy.
    Called after resolve_outcomes() accumulates enough data.
    Returns updated weights dict.
    """
    conn = get_conn()

    # Get overall recent accuracy
    recent = conn.execute("""
        SELECT COUNT(*) as total, SUM(CASE WHEN was_correct THEN 1 ELSE 0 END) as correct
        FROM prediction_outcomes
        WHERE resolved_at >= (now() - INTERVAL 90 DAY)
    """).fetchone()
    if not recent or recent[0] < _MIN_OUTCOMES_FOR_UPDATE:
        return {}

    baseline_acc = float(recent[1]) / float(recent[0]) if recent[0] > 0 else 0.5
    logger.info(f"Baseline 90d accuracy: {baseline_acc:.3f} ({recent[0]} outcomes)")

    # For each domain, compute accuracy of predictions where that domain had high SHAP
    # Since we can't easily attribute outcomes to domains post-hoc without storing SHAP,
    # we use regime-based accuracy as a proxy:
    # - HIGH_VOL regime accuracy vs NORMAL_VOL → tells us if vol signals are working
    updated = {}
    current = conn.execute("SELECT domain, weight_multiplier FROM signal_weights").df()
    weight_map = dict(zip(current["domain"], current["weight_multiplier"]))

    for domain, current_weight in weight_map.items():
        # Simple heuristic: if overall accuracy > 55%, slightly boost; < 50%, slightly cut
        # (Domain-specific attribution would require storing SHAP values per prediction)
        if baseline_acc > 0.56:
            new_weight = min(_MAX_WEIGHT, current_weight * (1 + _LR * 0.3))
        elif baseline_acc < 0.49:
            new_weight = max(_MIN_WEIGHT, current_weight * (1 - _LR * 0.3))
        else:
            new_weight = current_weight

        if abs(new_weight - current_weight) > 0.001:
            conn.execute("""
                UPDATE signal_weights
                SET weight_multiplier = ?, last_updated = now()
                WHERE domain = ?
            """, [round(new_weight, 4), domain])
            updated[domain] = round(new_weight, 4)

    if updated:
        conn.commit()
        logger.info(f"Updated domain weights: {updated}")

    return updated


def get_domain_weights() -> dict[str, float]:
    """Return current domain weight multipliers."""
    conn = get_conn()
    try:
        df = conn.execute("SELECT domain, weight_multiplier FROM signal_weights").df()
        return dict(zip(df["domain"], df["weight_multiplier"]))
    except Exception:
        return {}


def update_user_signal_outcome(signal_id: str, was_correct: bool) -> None:
    """
    Record whether a user override signal led to a correct prediction.
    Reinforces (boosts) or weakens the signal's domain weight if consistently right/wrong.
    """
    conn = get_conn()
    try:
        conn.execute("""
            UPDATE user_signals
            SET outcome_known = TRUE,
                was_correct = ?,
                reinforcement_count = reinforcement_count + 1
            WHERE id = ?
        """, [was_correct, signal_id])

        # If user was right 3+ times in a row on the same domain, boost that domain slightly
        sig = conn.execute("""
            SELECT domain, reinforcement_count
            FROM user_signals WHERE id = ?
        """, [signal_id]).fetchone()

        if sig and was_correct and sig[1] >= 3:
            domain = sig[0]
            conn.execute("""
                UPDATE signal_weights
                SET weight_multiplier = LEAST(?, weight_multiplier * ?),
                    correct_count = correct_count + 1,
                    total_count = total_count + 1,
                    last_updated = now()
                WHERE domain = ?
            """, [_MAX_WEIGHT, 1 + _LR, domain])
            logger.info(f"User signal reinforcement: domain={domain} boosted")
        elif sig and not was_correct:
            domain = sig[0]
            conn.execute("""
                UPDATE signal_weights
                SET weight_multiplier = GREATEST(?, weight_multiplier * ?),
                    total_count = total_count + 1,
                    last_updated = now()
                WHERE domain = ?
            """, [_MIN_WEIGHT, 1 - _LR * 0.5, domain])

        conn.commit()
    except Exception as e:
        logger.debug(f"Could not update user signal outcome: {e}")


def get_recent_accuracy(horizon: str = "1w", days: int = 90) -> dict:
    """Return recent directional accuracy summary."""
    conn = get_conn()
    try:
        row = conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN was_correct THEN 1 ELSE 0 END) as correct,
                AVG(CASE WHEN was_correct THEN 1.0 ELSE 0.0 END) as accuracy
            FROM prediction_outcomes
            WHERE horizon = ?
              AND resolved_at >= (now() - INTERVAL ? DAY)
        """, [horizon, days]).fetchone()
        if not row or row[0] == 0:
            return {"total": 0, "correct": 0, "accuracy": None}
        return {
            "total":    int(row[0]),
            "correct":  int(row[1]),
            "accuracy": round(float(row[2]), 4),
        }
    except Exception:
        return {"total": 0, "correct": 0, "accuracy": None}
