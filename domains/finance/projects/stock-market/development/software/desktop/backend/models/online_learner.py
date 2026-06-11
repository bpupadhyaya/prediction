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


def resolve_interactive_outcomes() -> int:
    """
    For each interactive_predictions row older than its implied horizon
    (estimate: session_date + 7 days for weekly, use 7 days default),
    look up actual price return from DuckDB prices table, determine
    if direction was correct, and insert into prediction_outcomes.
    Returns number of outcomes resolved.
    """
    conn = get_conn()
    # Find unresolved interactive predictions older than 7 days
    unresolved = conn.execute("""
        SELECT ip.id, ip.ticker, ip.session_date, ip.direction, ip.prob_up,
               ip.confidence, ip.created_at
        FROM interactive_predictions ip
        WHERE ip.session_date <= CURRENT_DATE - INTERVAL 7 DAY
          AND ip.id NOT IN (
              SELECT source_id FROM prediction_outcomes WHERE source_type = 'interactive'
                  AND source_id IS NOT NULL
          )
        LIMIT 100
    """).fetchdf()

    resolved = 0
    for _, row in unresolved.iterrows():
        try:
            session_date = pd.to_datetime(row['session_date']).date()
            end_date = session_date + timedelta(days=14)
            # Get price at prediction date and ~7 trading days later
            prices = conn.execute("""
                SELECT date, close FROM prices
                WHERE ticker = ? AND date BETWEEN ? AND ?
                ORDER BY date
            """, [row['ticker'], str(session_date), str(end_date)]).fetchdf()

            if len(prices) < 2:
                continue

            entry_price = float(prices.iloc[0]['close'])
            exit_price  = float(prices.iloc[-1]['close'])
            if entry_price == 0:
                continue
            actual_return = (exit_price - entry_price) / entry_price

            actual_direction = 'up' if actual_return > 0.002 else ('down' if actual_return < -0.002 else 'neutral')
            was_correct = (row['direction'] == actual_direction)

            conn.execute("""
                INSERT OR IGNORE INTO prediction_outcomes
                    (ticker, horizon, predicted_at, direction, probability,
                     regime_label, actual_return, was_correct, resolved_at,
                     source_type, source_id)
                VALUES (?, '1w', ?, ?, ?, 'interactive', ?, ?, now(), 'interactive', ?)
            """, [row['ticker'], row['created_at'], row['direction'],
                  float(row['prob_up']), float(actual_return), bool(was_correct), str(row['id'])])
            conn.commit()
            resolved += 1
        except Exception as e:
            logger.debug(f"Could not resolve interactive outcome {row['id']}: {e}")

    if resolved:
        logger.info(f"Resolved {resolved} interactive prediction outcomes")
    return resolved


def update_interactive_accuracy_weights() -> dict:
    """
    Analyze interactive prediction accuracy by domain over last 90 days.
    Update signal_weights table based on interactive prediction performance.
    Returns accuracy stats dict keyed by domain.
    """
    import json as _json

    conn = get_conn()

    try:
        results = conn.execute("""
            SELECT po.was_correct, ip.user_signals
            FROM prediction_outcomes po
            JOIN interactive_predictions ip ON po.source_id = ip.id
            WHERE po.source_type = 'interactive'
              AND po.resolved_at >= (now() - INTERVAL 90 DAY)
        """).fetchdf()

        if results.empty:
            return {}

        domain_stats: dict[str, dict] = {}
        for _, row in results.iterrows():
            try:
                raw = row['user_signals']
                signals = _json.loads(raw) if isinstance(raw, str) else raw
                if not isinstance(signals, list):
                    continue
                for signal in signals:
                    domain = signal.get('domain', 'unknown')
                    if domain not in domain_stats:
                        domain_stats[domain] = {'correct': 0, 'total': 0}
                    domain_stats[domain]['total'] += 1
                    if row['was_correct']:
                        domain_stats[domain]['correct'] += 1
            except Exception:
                continue

        # Update weights for domains with enough data
        for domain, stats in domain_stats.items():
            if stats['total'] < _MIN_OUTCOMES_FOR_UPDATE:
                continue
            accuracy = stats['correct'] / stats['total']
            try:
                current = conn.execute(
                    "SELECT weight_multiplier FROM signal_weights WHERE domain = ?", [domain]
                ).fetchone()
                current_weight = float(current[0]) if current else 1.0

                if accuracy > 0.55:
                    new_weight = min(_MAX_WEIGHT, current_weight * (1 + _LR * (accuracy - 0.5)))
                elif accuracy < 0.45:
                    new_weight = max(_MIN_WEIGHT, current_weight * (1 - _LR * (0.5 - accuracy)))
                else:
                    new_weight = current_weight

                conn.execute("""
                    INSERT INTO signal_weights (domain, weight_multiplier, correct_count, total_count, last_updated)
                    VALUES (?, ?, ?, ?, now())
                    ON CONFLICT (domain) DO UPDATE SET
                        weight_multiplier = excluded.weight_multiplier,
                        correct_count     = excluded.correct_count,
                        total_count       = excluded.total_count,
                        last_updated      = excluded.last_updated
                """, [domain, round(new_weight, 4), stats['correct'], stats['total']])
                conn.commit()
            except Exception as e:
                logger.debug(f"Could not update weight for domain {domain}: {e}")

        return {
            d: {'accuracy': round(s['correct'] / s['total'], 4), 'n': s['total']}
            for d, s in domain_stats.items()
            if s['total'] > 0
        }
    except Exception as e:
        logger.warning(f"update_interactive_accuracy_weights failed: {e}")
        return {}


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


# ─────────────────────────────────────────────────────────────────────────────
# YVIS feedback loop — Layer 5 ← Layer 6
#
# Applied video signals are stored in user_signals (source_tag='VIDEO_INTELLIGENCE')
# with speaker/video/parameter provenance. These functions resolve their outcomes
# against realised price moves, attribute accuracy to the speaker, and feed that
# back so proven speakers gain influence and unreliable ones are damped.
# ─────────────────────────────────────────────────────────────────────────────

# Trading-day horizon → minimum calendar age before an outcome can be resolved.
_HORIZON_TRADING_DAYS = {"1d": 1, "1w": 5, "1m": 21}
_HORIZON_MIN_CALENDAR_DAYS = {"1d": 2, "1w": 9, "1m": 35}
_CORR_MIN_SAMPLES = 5          # speaker needs this many resolved signals before it sways weighting


def resolve_video_signal_outcomes() -> int:
    """
    Resolve outcomes for applied video signals (user_signals with a video source).

    For each active video signal whose horizon has elapsed and whose ticker has
    enough forward price data, determine whether its direction was correct, mark
    the user_signal (which also nudges its domain weight via
    update_user_signal_outcome), and log a row into prediction_outcomes
    (source_type='video') for accuracy reporting.

    Returns the number of video signal outcomes resolved.
    """
    conn = get_conn()
    try:
        candidates = conn.execute("""
            SELECT id, ticker, extracted_signal, created_at,
                   COALESCE(horizon, '1w')          AS horizon,
                   COALESCE(speaker_name, '')        AS speaker_name,
                   COALESCE(parameter_name, '')      AS parameter_name,
                   COALESCE(domain, 'macro')         AS domain
            FROM user_signals
            WHERE source_tag = 'VIDEO_INTELLIGENCE'
              AND outcome_known = FALSE
              AND ticker IS NOT NULL AND ticker <> ''
              AND created_at < (now() - INTERVAL 2 DAY)
            LIMIT 500
        """).df()
    except Exception as e:
        logger.debug(f"resolve_video_signal_outcomes query failed: {e}")
        return 0

    resolved = 0
    for _, row in candidates.iterrows():
        sig_id   = row["id"]
        ticker   = row["ticker"]
        horizon  = str(row["horizon"]) if str(row["horizon"]) in _HORIZON_TRADING_DAYS else "1w"
        created  = pd.to_datetime(row["created_at"])
        min_age  = _HORIZON_MIN_CALENDAR_DAYS[horizon]

        # Skip signals not yet old enough for this horizon to have played out.
        if created > (datetime.now() - timedelta(days=min_age)):
            continue

        n_days = _HORIZON_TRADING_DAYS[horizon]
        actual_return = _get_actual_return(conn, ticker, created, n_days)
        if actual_return is None:
            continue

        es = float(row["extracted_signal"] or 0.0)
        if es == 0.0:
            continue
        predicted_up = es > 0
        was_correct = (predicted_up and actual_return > 0) or (not predicted_up and actual_return < 0)

        # Mark the user_signal + nudge its domain weight (existing reinforcement path).
        update_user_signal_outcome(sig_id, bool(was_correct))

        # Record an outcome row for accuracy reporting / dashboards.
        try:
            conn.execute("""
                INSERT OR IGNORE INTO prediction_outcomes
                    (ticker, horizon, predicted_at, direction, probability,
                     regime_label, actual_return, was_correct, resolved_at,
                     source_type, source_id)
                VALUES (?, ?, ?, ?, ?, 'video', ?, ?, now(), 'video', ?)
            """, [ticker, horizon, row["created_at"],
                  "up" if predicted_up else "down", 0.5 + 0.5 * min(1.0, abs(es)),
                  float(actual_return), bool(was_correct), str(sig_id)])
            resolved += 1
        except Exception as e:
            logger.debug(f"Could not log video outcome for {sig_id}: {e}")

    if resolved:
        conn.commit()
        logger.info(f"Resolved {resolved} video signal outcomes")
        update_speaker_correlations()

    return resolved


def update_speaker_correlations() -> dict:
    """
    Aggregate resolved video signals into the signal_correlations table:
    per (speaker, ticker, parameter) historical accuracy + sample size, plus a
    per-speaker 'ALL' rollup. This is the memory the prediction path reads to
    weight a speaker's future signals.

    Returns {speaker_name: {accuracy, n}} for speakers with a populated rollup.
    """
    import uuid as _uuid

    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT COALESCE(speaker_name, '')   AS speaker_name,
                   COALESCE(ticker, '')         AS ticker,
                   COALESCE(parameter_name, '') AS parameter_name,
                   was_correct
            FROM user_signals
            WHERE source_tag = 'VIDEO_INTELLIGENCE'
              AND outcome_known = TRUE
              AND speaker_name IS NOT NULL AND speaker_name <> ''
        """).df()
    except Exception as e:
        logger.debug(f"update_speaker_correlations query failed: {e}")
        return {}

    if rows.empty:
        return {}

    # Build (speaker, ticker, parameter) buckets AND a per-speaker ALL/ALL rollup.
    buckets: dict[tuple, dict] = {}
    for _, r in rows.iterrows():
        speaker = r["speaker_name"]
        correct = bool(r["was_correct"])
        for key in [
            (speaker, r["ticker"] or "ALL", r["parameter_name"] or "ALL"),
            (speaker, "ALL", "ALL"),
        ]:
            b = buckets.setdefault(key, {"correct": 0, "total": 0})
            b["total"] += 1
            b["correct"] += 1 if correct else 0

    summary: dict[str, dict] = {}
    for (speaker, ticker, param), b in buckets.items():
        acc = b["correct"] / b["total"] if b["total"] else 0.0
        try:
            existing = conn.execute(
                "SELECT id FROM signal_correlations WHERE speaker_name = ? AND ticker = ? AND parameter_name = ?",
                [speaker, ticker, param],
            ).fetchone()
            if existing:
                conn.execute("""
                    UPDATE signal_correlations
                    SET hist_accuracy = ?, sample_size = ?, updated_at = now()
                    WHERE id = ?
                """, [round(acc, 4), int(b["total"]), existing[0]])
            else:
                conn.execute("""
                    INSERT INTO signal_correlations
                        (id, speaker_name, ticker, parameter_name, hist_accuracy, sample_size, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, now())
                """, [str(_uuid.uuid4()), speaker, ticker, param, round(acc, 4), int(b["total"])])
        except Exception as e:
            logger.debug(f"Could not upsert correlation {speaker}/{ticker}/{param}: {e}")

        if ticker == "ALL" and param == "ALL":
            summary[speaker] = {"accuracy": round(acc, 4), "n": int(b["total"])}

    conn.commit()
    if summary:
        logger.info(f"Updated speaker correlations: {summary}")
    return summary


def get_speaker_signal_multiplier(
    speaker_name: str,
    ticker: str | None = None,
    parameter_name: str | None = None,
    min_samples: int = _CORR_MIN_SAMPLES,
) -> float:
    """
    Weight multiplier in [0.5, 2.0] for a speaker's video signal, derived from
    historical accuracy. Falls back through (speaker,ticker,param) →
    (speaker,ticker) → (speaker,ALL,ALL); returns 1.0 (neutral) until a speaker
    has at least `min_samples` resolved signals.
    """
    if not speaker_name:
        return 1.0
    conn = get_conn()
    lookups = [
        (speaker_name, ticker or "ALL", parameter_name or "ALL"),
        (speaker_name, ticker or "ALL", "ALL"),
        (speaker_name, "ALL", "ALL"),
    ]
    for sp, tk, pm in lookups:
        try:
            row = conn.execute("""
                SELECT hist_accuracy, sample_size FROM signal_correlations
                WHERE speaker_name = ? AND ticker = ? AND parameter_name = ?
            """, [sp, tk, pm]).fetchone()
        except Exception:
            row = None
        if row and row[1] and int(row[1]) >= min_samples:
            acc = float(row[0])
            # acc 0.5 → 1.0 ; 0.75 → 1.5 ; 1.0 → 2.0 ; 0.25 → 0.5 ; clamp [0.5, 2.0]
            mult = 1.0 + (acc - 0.5) * 2.0
            return float(max(0.5, min(2.0, mult)))
    return 1.0


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
