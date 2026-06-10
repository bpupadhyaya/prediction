"""
Interactive Predictions — Phase 4.

Endpoints for saving, retrieving, and managing user-driven interactive
prediction sessions (built from manually entered signals in the UI).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, date
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database.duckdb_client import get_conn

router = APIRouter(prefix="/api/interactive", tags=["interactive"])


# ── Request / response schemas ────────────────────────────────────────────────

class UserSignal(BaseModel):
    name: str
    domain: str
    direction: str          # 'up', 'down', 'neutral'
    weight: int             # 0–100
    value: Optional[float] = None


class InteractivePredictionRequest(BaseModel):
    ticker: str
    prob_up: float
    confidence: float
    direction: str          # 'up', 'down', 'neutral'
    user_signals: List[UserSignal]
    notes: str = ''
    source: str = 'web'


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/predictions")
def save_interactive_prediction(payload: InteractivePredictionRequest) -> dict:
    """Save an interactive prediction session built from user-entered signals."""
    pred_id    = str(uuid.uuid4())
    created_at = datetime.utcnow()
    session_date = created_at.date()
    signals_json = json.dumps([s.model_dump() for s in payload.user_signals])

    conn = get_conn()
    conn.execute("""
        INSERT INTO interactive_predictions
            (id, ticker, session_date, created_at,
             user_signals, signals_count,
             prob_up, confidence, direction,
             notes, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        pred_id,
        payload.ticker.upper(),
        session_date,
        created_at,
        signals_json,
        len(payload.user_signals),
        payload.prob_up,
        payload.confidence,
        payload.direction,
        payload.notes,
        payload.source,
    ])
    conn.commit()

    return {
        "id":           pred_id,
        "ticker":       payload.ticker.upper(),
        "session_date": str(session_date),
        "created_at":   created_at.isoformat(),
        "direction":    payload.direction,
        "prob_up":      payload.prob_up,
        "confidence":   payload.confidence,
        "signals_count": len(payload.user_signals),
        "message":      "Interactive prediction saved",
    }


@router.get("/predictions")
def list_interactive_predictions(
    ticker: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """List interactive predictions, optionally filtered by ticker."""
    conn = get_conn()

    if ticker:
        df = conn.execute("""
            SELECT id, ticker, session_date, created_at,
                   user_signals, signals_count,
                   prob_up, confidence, direction, notes, source
            FROM interactive_predictions
            WHERE ticker = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, [ticker.upper(), limit, offset]).df()
        total = conn.execute(
            "SELECT COUNT(*) FROM interactive_predictions WHERE ticker = ?",
            [ticker.upper()],
        ).fetchone()[0]
    else:
        df = conn.execute("""
            SELECT id, ticker, session_date, created_at,
                   user_signals, signals_count,
                   prob_up, confidence, direction, notes, source
            FROM interactive_predictions
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, [limit, offset]).df()
        total = conn.execute(
            "SELECT COUNT(*) FROM interactive_predictions"
        ).fetchone()[0]

    records = df.to_dict("records")
    # Parse the stored JSON string back to a list for each row
    for r in records:
        if isinstance(r.get("user_signals"), str):
            try:
                r["user_signals"] = json.loads(r["user_signals"])
            except (json.JSONDecodeError, TypeError):
                r["user_signals"] = []
        # Normalise date/timestamp to strings
        for key in ("session_date", "created_at"):
            if key in r and r[key] is not None:
                r[key] = str(r[key])

    return {
        "predictions": records,
        "count":       len(records),
        "total":       total,
        "limit":       limit,
        "offset":      offset,
    }


@router.get("/predictions/{id}")
def get_interactive_prediction(id: str) -> dict:
    """Return a single interactive prediction by ID."""
    conn = get_conn()
    row = conn.execute("""
        SELECT id, ticker, session_date, created_at,
               user_signals, signals_count,
               prob_up, confidence, direction, notes, source
        FROM interactive_predictions
        WHERE id = ?
    """, [id]).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Interactive prediction '{id}' not found")

    cols = ["id", "ticker", "session_date", "created_at",
            "user_signals", "signals_count",
            "prob_up", "confidence", "direction", "notes", "source"]
    record = dict(zip(cols, row))

    if isinstance(record.get("user_signals"), str):
        try:
            record["user_signals"] = json.loads(record["user_signals"])
        except (json.JSONDecodeError, TypeError):
            record["user_signals"] = []

    for key in ("session_date", "created_at"):
        if key in record and record[key] is not None:
            record[key] = str(record[key])

    return record


@router.delete("/predictions/{id}")
def delete_interactive_prediction(id: str) -> dict:
    """Delete an interactive prediction by ID."""
    conn = get_conn()
    # Verify existence first
    exists = conn.execute(
        "SELECT COUNT(*) FROM interactive_predictions WHERE id = ?", [id]
    ).fetchone()[0]
    if not exists:
        raise HTTPException(status_code=404, detail=f"Interactive prediction '{id}' not found")

    conn.execute("DELETE FROM interactive_predictions WHERE id = ?", [id])
    conn.commit()
    return {"message": "Interactive prediction deleted", "id": id}


@router.post("/resolve-outcomes")
async def resolve_outcomes_endpoint() -> dict:
    """
    Resolve any outstanding interactive predictions whose horizon has elapsed,
    determine correctness vs. actual prices, and update domain signal weights.
    """
    from backend.models.online_learner import resolve_interactive_outcomes, update_interactive_accuracy_weights
    resolved = resolve_interactive_outcomes()
    accuracy = update_interactive_accuracy_weights()
    return {"resolved": resolved, "domain_accuracy": accuracy}


@router.get("/stats")
def get_interactive_stats(ticker: Optional[str] = None) -> dict:
    """
    Aggregate accuracy stats for saved interactive predictions.
    Counts directional distribution and returns per-ticker breakdown.
    """
    conn = get_conn()

    where = "WHERE ticker = ?" if ticker else ""
    params = [ticker.upper()] if ticker else []

    summary = conn.execute(f"""
        SELECT
            COUNT(*)                                            AS total,
            SUM(CASE WHEN direction = 'up'      THEN 1 ELSE 0 END) AS up_count,
            SUM(CASE WHEN direction = 'down'    THEN 1 ELSE 0 END) AS down_count,
            SUM(CASE WHEN direction = 'neutral' THEN 1 ELSE 0 END) AS neutral_count,
            AVG(prob_up)                                        AS avg_prob_up,
            AVG(confidence)                                     AS avg_confidence,
            AVG(signals_count)                                  AS avg_signals
        FROM interactive_predictions
        {where}
    """, params).fetchone()

    total, up_count, down_count, neutral_count, avg_prob_up, avg_confidence, avg_signals = summary

    by_ticker_df = conn.execute(f"""
        SELECT ticker,
               COUNT(*)                                            AS total,
               SUM(CASE WHEN direction = 'up'   THEN 1 ELSE 0 END) AS up_count,
               SUM(CASE WHEN direction = 'down' THEN 1 ELSE 0 END) AS down_count,
               AVG(prob_up)                                        AS avg_prob_up,
               AVG(confidence)                                     AS avg_confidence
        FROM interactive_predictions
        {where}
        GROUP BY ticker
        ORDER BY total DESC
    """, params).df()

    return {
        "ticker":          ticker.upper() if ticker else None,
        "total":           int(total or 0),
        "up_count":        int(up_count or 0),
        "down_count":      int(down_count or 0),
        "neutral_count":   int(neutral_count or 0),
        "avg_prob_up":     round(float(avg_prob_up), 4) if avg_prob_up is not None else None,
        "avg_confidence":  round(float(avg_confidence), 4) if avg_confidence is not None else None,
        "avg_signals":     round(float(avg_signals), 1) if avg_signals is not None else None,
        "by_ticker":       by_ticker_df.to_dict("records"),
    }
