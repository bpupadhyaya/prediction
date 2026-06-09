"""
User Guidance Interface — Layer 9 of the ADPS architecture.

Endpoints for injecting user knowledge (URLs, notes, weight overrides, pins)
into the prediction system, reviewing active signals, and recording outcomes.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database.duckdb_client import get_conn

router = APIRouter()


# ── Request / response schemas ────────────────────────────────────────────────

class SignalRequest(BaseModel):
    ticker: Optional[str] = None         # None = applies to all tickers
    signal_type: str                     # "url" | "note" | "weight" | "pin"
    domain: str                          # "macro" | "momentum" | "volatility" | etc.
    content: str                         # URL, text, or description
    extracted_signal: float = 0.0        # [-1, +1]: -1 = strong bearish, +1 = strong bullish
    weight_multiplier: float = 1.0       # domain weight override [0.5, 2.0]
    confidence: float = 0.9
    expires_days: Optional[int] = 7      # None = never expires


class OutcomeRequest(BaseModel):
    signal_id: str
    was_correct: bool


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/signal")
def add_signal(req: SignalRequest):
    """
    Add a user guidance signal to the prediction system.
    The signal will be applied as a nudge on the next predict_ticker() call.
    """
    if req.extracted_signal < -1.0 or req.extracted_signal > 1.0:
        raise HTTPException(status_code=400, detail="extracted_signal must be in [-1, 1]")
    if req.weight_multiplier < 0.1 or req.weight_multiplier > 5.0:
        raise HTTPException(status_code=400, detail="weight_multiplier must be in [0.1, 5.0]")

    signal_id  = str(uuid.uuid4())
    expires_at = (datetime.now() + timedelta(days=req.expires_days)) if req.expires_days else None

    conn = get_conn()
    conn.execute("""
        INSERT INTO user_signals
            (id, ticker, signal_type, domain, content, extracted_signal,
             weight_multiplier, confidence, source_tag, created_at, expires_at, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'USER_OVERRIDE', now(), ?, TRUE)
    """, [
        signal_id,
        req.ticker or None,
        req.signal_type,
        req.domain,
        req.content,
        req.extracted_signal,
        req.weight_multiplier,
        req.confidence,
        expires_at,
    ])
    conn.commit()

    return {
        "id":               signal_id,
        "message":          "Signal added successfully",
        "ticker":           req.ticker,
        "domain":           req.domain,
        "extracted_signal": req.extracted_signal,
        "expires_at":       expires_at.isoformat() if expires_at else None,
    }


@router.get("/signals/{ticker}")
def get_signals(ticker: str):
    """Return active, unexpired signals for this ticker (plus global signals)."""
    conn = get_conn()
    df = conn.execute("""
        SELECT id, ticker, signal_type, domain, content,
               extracted_signal, weight_multiplier, confidence,
               source_tag, created_at, expires_at, outcome_known, was_correct
        FROM user_signals
        WHERE is_active = TRUE
          AND (expires_at IS NULL OR expires_at > now())
          AND (ticker = ? OR ticker IS NULL OR ticker = '')
        ORDER BY created_at DESC
    """, [ticker.upper()]).df()

    return {
        "ticker":  ticker.upper(),
        "signals": df.to_dict("records"),
        "count":   len(df),
    }


@router.get("/signals")
def get_all_signals():
    """Return all active, unexpired signals across all tickers."""
    conn = get_conn()
    df = conn.execute("""
        SELECT id, ticker, signal_type, domain, content,
               extracted_signal, weight_multiplier, confidence,
               source_tag, created_at, expires_at, outcome_known, was_correct
        FROM user_signals
        WHERE is_active = TRUE
          AND (expires_at IS NULL OR expires_at > now())
        ORDER BY created_at DESC
        LIMIT 100
    """).df()

    return {"signals": df.to_dict("records"), "count": len(df)}


@router.delete("/signal/{signal_id}")
def delete_signal(signal_id: str):
    """Deactivate (soft-delete) a signal."""
    conn = get_conn()
    result = conn.execute("""
        UPDATE user_signals SET is_active = FALSE
        WHERE id = ?
    """, [signal_id])
    conn.commit()
    return {"message": "Signal deactivated", "id": signal_id}


@router.post("/outcome")
def record_outcome(req: OutcomeRequest):
    """
    Record whether a user-guided prediction was correct.
    This feeds into online learning to reinforce or weaken domain weights.
    """
    from backend.models.online_learner import update_user_signal_outcome
    try:
        update_user_signal_outcome(req.signal_id, req.was_correct)
        return {"message": "Outcome recorded", "signal_id": req.signal_id, "was_correct": req.was_correct}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regime")
def get_current_regime():
    """Return current 4-dimension market regime classification."""
    try:
        from backend.models.regime import classify_current
        regime = classify_current()
        if regime is None:
            return {"regime": None, "message": "Regime not yet computed — run prediction first"}

        monetary_labels  = {0: "Cutting", 1: "Pausing", 2: "Hiking"}
        credit_labels    = {0: "Expansion", 1: "Stress", 2: "Crisis"}
        vol_labels       = {0: "Low Volatility", 1: "Normal", 2: "Elevated Volatility", 3: "Volatility Crisis"}
        yc_labels        = {0: "Normal (Upward Slope)", 1: "Flat", 2: "Inverted", 3: "Re-steepening"}

        return {
            "regime": {
                "monetary":    {"code": regime.monetary,    "label": monetary_labels.get(regime.monetary, "?")},
                "credit":      {"code": regime.credit,      "label": credit_labels.get(regime.credit, "?")},
                "volatility":  {"code": regime.volatility,  "label": vol_labels.get(regime.volatility, "?")},
                "yield_curve": {"code": regime.yield_curve, "label": yc_labels.get(regime.yield_curve, "?")},
                "as_of": str(regime.as_of) if regime.as_of else None,
            },
            "interpretation": _interpret_regime(regime),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accuracy")
def get_accuracy(horizon: str = "1w", days: int = 90):
    """Return recent model directional accuracy from online learning outcomes."""
    from backend.models.online_learner import get_recent_accuracy
    result = get_recent_accuracy(horizon=horizon, days=days)
    return {
        "horizon":  horizon,
        "days":     days,
        "total":    result.get("total", 0),
        "correct":  result.get("correct", 0),
        "accuracy": result.get("accuracy"),
        "message":  "Insufficient data" if result.get("total", 0) < 10 else None,
    }


@router.get("/domain-weights")
def get_domain_weights():
    """Return current per-domain signal weight multipliers."""
    from backend.models.online_learner import get_domain_weights
    weights = get_domain_weights()
    domain_labels = {
        "macro":      "Macro & Monetary",
        "momentum":   "Momentum & Technical",
        "volatility": "Volatility",
        "fundamental": "Fundamental",
        "cross_asset": "Cross-Asset",
        "sentiment":  "Sentiment",
        "geopolitical": "Geopolitical",
        "technical":  "Technical",
    }
    return {
        "weights": [
            {"domain": d, "label": domain_labels.get(d, d), "multiplier": w}
            for d, w in sorted(weights.items())
        ]
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _interpret_regime(regime) -> str:
    """Plain-English regime summary."""
    parts = []

    if regime.monetary == 0:
        parts.append("Fed is cutting rates — typically bullish for equities")
    elif regime.monetary == 2:
        parts.append("Fed is hiking rates — headwind for equities")

    if regime.credit == 1:
        parts.append("credit spreads elevated — risk-off conditions")
    elif regime.credit == 2:
        parts.append("credit in crisis — severe risk aversion")

    if regime.volatility == 0:
        parts.append("low volatility — risk-on environment")
    elif regime.volatility == 2:
        parts.append("elevated volatility — expect wider swings")
    elif regime.volatility == 3:
        parts.append("volatility crisis — extreme caution warranted")

    if regime.yield_curve == 2:
        parts.append("inverted yield curve — historically precedes recessions")
    elif regime.yield_curve == 3:
        parts.append("yield curve re-steepening — early recovery signal")

    if not parts:
        return "Normal market regime — no extreme signals"
    return "; ".join(p.capitalize() for p in parts) + "."
