"""
Prediction Engine — Layer 4 of the ADPS architecture.

Assembles regime-aware ensemble prediction, SHAP explanation, user signal
nudges, and online-learning outcome recording into a single predict_ticker()
call. Returns a Prediction dataclass that the API layer serialises directly.
"""

from __future__ import annotations

import json
import logging
import pickle
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd

from backend.config import MODELS_DIR
from backend.database.duckdb_client import get_conn
from backend.models.trainer import (
    BASE_TECHNICAL_COLS,
    CROSS_RANK_SOURCE_COLS,
    FEATURE_COLS,
    HORIZON_DAYS,
    HORIZON_FEATURES_PATHS,
    HORIZON_MODEL_PATHS,
    HORIZON_SCALER_PATHS,
    SECTORS_DIR,
    _load_regime_model,
    _sector_slug,
    build_features,
    latest_accuracy,
)

logger = logging.getLogger(__name__)

# Blend weights: 65% regime-specific model + 35% global model at inference
_REGIME_BLEND   = 0.65
_GLOBAL_BLEND   = 0.35

# Maximum probability nudge from all user signals combined (prevents runaway overrides)
_MAX_NUDGE = 0.15


# ── Expanded Prediction dataclass ────────────────────────────────────────────

@dataclass
class Prediction:
    ticker:               str
    horizon:              str
    direction:            str
    probability:          float
    expected_return_low:  float
    expected_return_high: float
    volatility:           float
    model_accuracy:       float
    model_ready:          bool
    sector:               str = "Unknown"
    model_type:           str = "global"
    # ADPS v3 additions
    regime_label:         str = ""
    regime:               dict = field(default_factory=dict)
    explanation:          dict = field(default_factory=dict)
    calc_chain:           dict = field(default_factory=dict)
    user_signals_active:  list = field(default_factory=list)
    recent_accuracy:      dict = field(default_factory=dict)


# ── Per-day inference cache ───────────────────────────────────────────────────

_cache: dict = {"date": None, "cs": None, "macro": None, "fund": None, "sectors": None}


def invalidate_cache() -> None:
    """Force a cross-sectional cache rebuild (e.g. after an on-demand data load
    adds a ticker the daily cache has never seen)."""
    _cache["date"] = None


def _refresh_cache() -> None:
    today = date.today()
    if _cache["date"] == today:
        return

    conn = get_conn()

    df = conn.execute("""
        SELECT ticker, CAST(date AS VARCHAR) as date, open, high, low, close, volume
        FROM prices
        WHERE date >= CURRENT_DATE - INTERVAL 150 DAY
        ORDER BY ticker, date
    """).df()
    df["date"] = pd.to_datetime(df["date"])

    rows = []
    for ticker, group in df.groupby("ticker"):
        feat = build_features(group)
        if feat.empty:
            continue
        last = feat.iloc[-1]
        row = {col: float(last[col]) for col in BASE_TECHNICAL_COLS if col in feat.columns}
        row["ticker"]   = ticker
        row["_vol_ref"] = float(last["volatility_20"])
        rows.append(row)

    cs = pd.DataFrame(rows) if rows else pd.DataFrame()

    if not cs.empty:
        for col in CROSS_RANK_SOURCE_COLS:
            if col in cs.columns:
                cs[f"{col}_rank"] = cs[col].rank(pct=True)

    try:
        from backend.data.macro_feed import get_macro_context
        macro = get_macro_context()
    except Exception:
        macro = {}

    fund_snap = conn.execute("""
        SELECT DISTINCT ON (ticker) ticker, earnings_surprise, short_ratio
        FROM fundamentals
        ORDER BY ticker, report_date DESC
    """).df()
    fund_map = {
        r["ticker"]: {
            "earnings_surprise": float(r["earnings_surprise"] or 0.0),
            "short_ratio":       float(r["short_ratio"] or 0.0),
        }
        for _, r in fund_snap.iterrows()
    }

    sectors = conn.execute("SELECT ticker, COALESCE(sector, 'Unknown') as sector FROM stocks").df()
    sector_map = dict(zip(sectors["ticker"], sectors["sector"]))

    _cache.update({
        "date":    today,
        "cs":      cs,
        "macro":   macro,
        "fund":    fund_map,
        "sectors": sector_map,
    })


# ── Model loading helpers ─────────────────────────────────────────────────────

def _load_global_model(horizon: str) -> tuple:
    """Returns (model, scaler, feature_cols) or (None, None, None)."""
    mp = HORIZON_MODEL_PATHS.get(horizon)
    sp = HORIZON_SCALER_PATHS.get(horizon)
    fp = HORIZON_FEATURES_PATHS.get(horizon)
    if not mp or not mp.exists() or not sp or not sp.exists():
        return None, None, None
    with open(mp, "rb") as f:
        model = pickle.load(f)
    with open(sp, "rb") as f:
        scaler = pickle.load(f)
    feat_cols = FEATURE_COLS
    if fp and fp.exists():
        with open(fp) as f:
            feat_cols = json.load(f).get("feature_cols", FEATURE_COLS)
    return model, scaler, feat_cols


def _load_sector_model(sector: str, horizon: str) -> tuple:
    """Returns (model, scaler, feature_cols, accuracy) or (None, None, None, None)."""
    if not sector or sector == "Unknown":
        return None, None, None, None
    slug = _sector_slug(sector)
    mp = SECTORS_DIR / f"model_{slug}_{horizon}.pkl"
    sp = SECTORS_DIR / f"scaler_{slug}_{horizon}.pkl"
    fp = SECTORS_DIR / f"features_{slug}_{horizon}.json"
    if not mp.exists() or not sp.exists():
        return None, None, None, None
    with open(mp, "rb") as f:
        model = pickle.load(f)
    with open(sp, "rb") as f:
        scaler = pickle.load(f)
    feat_cols = FEATURE_COLS
    sector_acc = None
    if fp.exists():
        with open(fp) as f:
            meta = json.load(f)
            feat_cols  = meta.get("feature_cols", FEATURE_COLS)
            sector_acc = meta.get("accuracy")
    return model, scaler, feat_cols, sector_acc


# ── Feature vector assembly ───────────────────────────────────────────────────

def _build_feature_vector(
    ticker: str,
    feature_cols: list[str],
    regime_codes: dict | None = None,
) -> tuple[np.ndarray | None, dict]:
    """
    Assemble scaled feature vector for ticker.
    Returns (X_raw_unscaled_as_1xN, feature_values_raw_dict).
    """
    _refresh_cache()
    cs    = _cache.get("cs")
    macro = _cache.get("macro", {})
    fund  = _cache.get("fund", {})

    if cs is None or cs.empty:
        return None, {}

    row = cs[cs["ticker"] == ticker]
    if row.empty:
        return None, {}

    values: dict[str, float] = {}

    for col in feature_cols:
        if col in row.columns:
            values[col] = float(row[col].iloc[0])

    for k, v in macro.items():
        values[k] = float(v)

    fund_data = fund.get(ticker, {})
    values["earnings_surprise"] = float(fund_data.get("earnings_surprise", 0.0))
    values["short_ratio"]       = float(fund_data.get("short_ratio", 0.0))

    # Cross-sectional ranks
    for col in CROSS_RANK_SOURCE_COLS:
        rank_col = f"{col}_rank"
        if rank_col not in values:
            values[rank_col] = float(row[rank_col].iloc[0]) if rank_col in row.columns else 0.5

    # Inject regime codes if provided (from classify_current)
    if regime_codes:
        for k, v in regime_codes.items():
            values[k] = float(v)

    # Sanitize all values — NaN/Inf in the dict would break JSON serialization of explanations
    values = {k: (v if np.isfinite(v) else 0.0) for k, v in values.items()}

    vec = np.array([values.get(col, 0.0) for col in feature_cols], dtype=float)
    vec = np.nan_to_num(vec, nan=0.0)
    return vec.reshape(1, -1), values


# ── User signal helpers ───────────────────────────────────────────────────────

def _get_active_user_signals(ticker: str) -> list[dict]:
    """Return unexpired, active user signals for ticker (or ticker-agnostic)."""
    conn = get_conn()
    try:
        df = conn.execute("""
            SELECT id, ticker, signal_type, domain, content,
                   extracted_signal, weight_multiplier, confidence, source_tag
            FROM user_signals
            WHERE is_active = TRUE
              AND (expires_at IS NULL OR expires_at > now())
              AND (ticker = ? OR ticker IS NULL OR ticker = '')
            ORDER BY created_at DESC
            LIMIT 20
        """, [ticker]).df()
        return df.to_dict("records")
    except Exception:
        return []


def _apply_user_signals(prob_up: float, signals: list[dict]) -> float:
    """
    Nudge probability based on user signals.
    Each signal's extracted_signal is in [-1, +1]; positive → bullish nudge.
    Total nudge capped at ±_MAX_NUDGE.
    """
    if not signals:
        return prob_up

    total_nudge = 0.0
    for sig in signals:
        es   = float(sig.get("extracted_signal") or 0.0)
        wt   = float(sig.get("weight_multiplier") or 1.0)
        conf = float(sig.get("confidence") or 0.9)
        # Nudge = signal * weight * confidence * base_scale
        total_nudge += es * wt * conf * 0.10

    total_nudge = max(-_MAX_NUDGE, min(_MAX_NUDGE, total_nudge))
    return max(0.01, min(0.99, prob_up + total_nudge))


# ── Main predict function ─────────────────────────────────────────────────────

def predict_ticker(ticker: str, horizon: str = "1w") -> Prediction:
    _refresh_cache()
    sector     = _cache.get("sectors", {}).get(ticker, "Unknown")
    global_acc = latest_accuracy(horizon)

    # ── 1. Classify current market regime ────────────────────────────────────
    regime_obj  = None
    regime_label = ""
    regime_dict  = {}
    regime_codes: dict[str, float] = {}
    vol_code = 1   # default: NORMAL

    try:
        from backend.models.regime import classify_current
        regime_obj = classify_current()
        if regime_obj:
            vol_code     = int(regime_obj.volatility)
            regime_codes = {
                "monetary_regime": float(regime_obj.monetary),
                "credit_regime":   float(regime_obj.credit),
                "vol_regime_code": float(regime_obj.volatility),
                "yc_regime_code":  float(regime_obj.yield_curve),
            }
            # Human-readable label
            monetary_labels  = {0: "Cutting", 1: "Pausing", 2: "Hiking"}
            credit_labels    = {0: "Expansion", 1: "Stress", 2: "Crisis"}
            vol_labels       = {0: "Low Vol", 1: "Normal", 2: "Elevated Vol", 3: "Crisis Vol"}
            yc_labels        = {0: "Normal YC", 1: "Flat YC", 2: "Inverted YC", 3: "Re-steepening"}
            regime_label = (
                f"{monetary_labels.get(regime_obj.monetary, '?')} | "
                f"{credit_labels.get(regime_obj.credit, '?')} | "
                f"{vol_labels.get(regime_obj.volatility, '?')} | "
                f"{yc_labels.get(regime_obj.yield_curve, '?')}"
            )
            regime_dict = {
                "monetary":   regime_obj.monetary,
                "credit":     regime_obj.credit,
                "volatility": regime_obj.volatility,
                "yield_curve": regime_obj.yield_curve,
                "label":      regime_label,
                "as_of":      str(regime_obj.as_of) if regime_obj.as_of else "",
            }
    except Exception as e:
        logger.debug(f"Regime classification failed: {e}")

    # ── 2. Load models ────────────────────────────────────────────────────────
    # Global (fallback)
    global_model, global_scaler, global_feat_cols = _load_global_model(horizon)

    # Regime-specific model
    reg_model, reg_scaler, reg_feat_cols, reg_acc = _load_regime_model(vol_code, horizon)

    # Determine primary model for feature cols and accuracy
    if reg_model is not None:
        primary_feat_cols = reg_feat_cols
        model_type = f"regime+global blend"
    elif global_model is not None:
        primary_feat_cols = global_feat_cols
        model_type = "global"
    else:
        # Try sector model as last resort
        s_model, s_scaler, s_feat_cols, s_acc = _load_sector_model(sector, horizon)
        if s_model is not None:
            primary_feat_cols = s_feat_cols
            model_type = f"sector:{sector}"
        else:
            return Prediction(
                ticker, horizon, "unknown", 0.5,
                0.0, 0.0, 0.0, global_acc, False, sector, "none",
                regime_label=regime_label, regime=regime_dict,
            )

    # ── 3. Build feature vector ───────────────────────────────────────────────
    X_raw, feature_values_raw = _build_feature_vector(ticker, primary_feat_cols, regime_codes)
    if X_raw is None:
        return Prediction(
            ticker, horizon, "unknown", 0.5,
            0.0, 0.0, 0.0, global_acc, False, sector, "none",
            regime_label=regime_label, regime=regime_dict,
        )

    # ── 4. Regime-aware probability blending ─────────────────────────────────
    prob_regime: float | None = None
    try:
        prob_global = 0.5
        if global_model is not None:
            X_global_raw, _ = _build_feature_vector(ticker, global_feat_cols, regime_codes)
            if X_global_raw is not None:
                X_global_s = global_scaler.transform(X_global_raw)
                prob_global = float(global_model.predict_proba(X_global_s)[0][1])

        if reg_model is not None:
            X_reg_raw, _ = _build_feature_vector(ticker, reg_feat_cols, regime_codes)
            if X_reg_raw is not None:
                X_reg_s = reg_scaler.transform(X_reg_raw)
                prob_regime = float(reg_model.predict_proba(X_reg_s)[0][1])
                prob_up = _REGIME_BLEND * prob_regime + _GLOBAL_BLEND * prob_global
            else:
                prob_up = prob_global
        else:
            prob_up = prob_global

    except Exception as e:
        logger.warning(f"Prediction error for {ticker}/{horizon}: {e}")
        return Prediction(
            ticker, horizon, "unknown", 0.5,
            0.0, 0.0, 0.0, global_acc, False, sector, "none",
            regime_label=regime_label, regime=regime_dict,
        )

    # ── 5. User signal nudges ─────────────────────────────────────────────────
    user_signals = _get_active_user_signals(ticker)
    prob_up_nudged = _apply_user_signals(prob_up, user_signals)

    # ── 5b. Calculation chain (for transparency UI) ───────────────────────────
    _nudge_delta = round(prob_up_nudged - prob_up, 4)
    calc_chain: dict = {
        "steps": [
            {
                "step": 1,
                "label": "Global Model",
                "description": f"GradientBoosting trained on all tickers (200 estimators, max_depth=4, lr=0.05)",
                "value": round(prob_global, 4),
                "value_pct": round(prob_global * 100, 1),
            },
            {
                "step": 2,
                "label": "Regime Model Blend",
                "description": (
                    f"Regime-specific model (vol_regime={vol_code}) blended: "
                    f"{int(_REGIME_BLEND*100)}% regime + {int(_GLOBAL_BLEND*100)}% global"
                    if prob_regime is not None else
                    "No regime model available — using global only"
                ),
                "value": round(prob_up, 4),
                "value_pct": round(prob_up * 100, 1),
                "regime_model_prob": round(prob_regime, 4) if prob_regime is not None else None,
                "global_model_prob": round(prob_global, 4),
                "blend_formula": (
                    f"{int(_REGIME_BLEND*100)}% × {round(prob_regime,4)} + {int(_GLOBAL_BLEND*100)}% × {round(prob_global,4)} = {round(prob_up,4)}"
                    if prob_regime is not None else
                    f"global only = {round(prob_global,4)}"
                ),
            },
            {
                "step": 3,
                "label": "User Signal Nudge",
                "description": (
                    f"{len(user_signals)} active user signal(s) applied, total nudge = {_nudge_delta:+.4f}"
                    if user_signals else
                    "No active user signals"
                ),
                "value": round(prob_up_nudged, 4),
                "value_pct": round(prob_up_nudged * 100, 1),
                "nudge_delta": _nudge_delta,
                "signals_count": len(user_signals),
            },
        ],
        "final_prob_up": round(prob_up_nudged, 4),
        "final_direction": "up" if prob_up_nudged >= 0.5 else "down",
        "final_confidence_pct": round(
            (prob_up_nudged if prob_up_nudged >= 0.5 else 1 - prob_up_nudged) * 100, 1
        ),
        "regime_label": regime_label,
        "model_type": model_type if prob_regime is not None else "global",
    }

    # ── 6. SHAP explanation ───────────────────────────────────────────────────
    explanation: dict = {}
    try:
        from backend.models.explainer import explain
        from backend.models.trainer import FEATURE_COLS as ALL_FEATURE_COLS
        # Use global model for explanation (more stable than regime-specific)
        if global_model is not None and global_scaler is not None:
            X_explain_raw, _ = _build_feature_vector(ticker, global_feat_cols, regime_codes)
            if X_explain_raw is not None:
                X_explain_s = global_scaler.transform(X_explain_raw)
                # Build comprehensive raw values for ALL defined features (not just model subset)
                _, all_feature_values_raw = _build_feature_vector(ticker, ALL_FEATURE_COLS, regime_codes)
                # Merge: all_feature_values_raw base + original values for any extras not in FEATURE_COLS
                merged_raw = {**all_feature_values_raw, **feature_values_raw}
                explanation = explain(
                    global_model, global_scaler,
                    X_explain_s, global_feat_cols,
                    merged_raw, prob_up_nudged,
                    all_feature_cols=ALL_FEATURE_COLS,
                )
    except Exception as e:
        logger.debug(f"Explanation failed for {ticker}: {e}")

    # ── 7. Compute return range (needed before recording) ────────────────────
    direction = "up" if prob_up_nudged >= 0.5 else "down"

    cs = _cache.get("cs")
    row = cs[cs["ticker"] == ticker] if cs is not None else pd.DataFrame()
    vol_ref = float(row["_vol_ref"].iloc[0]) if not row.empty and "_vol_ref" in row.columns else 0.02

    horizon_days = HORIZON_DAYS.get(horizon, 5)
    vol_horizon  = vol_ref * np.sqrt(horizon_days)
    expected     = (prob_up_nudged - 0.5) * 2 * vol_horizon
    ret_low      = round(float(expected - vol_horizon), 4)
    ret_high     = round(float(expected + vol_horizon), 4)
    ann_vol      = round(float(vol_ref * np.sqrt(252 / max(1, horizon_days))), 4)

    # ── 8. Record prediction for online learning (persistent to DuckDB) ───────
    try:
        from backend.models.online_learner import record_prediction
        record_prediction(
            ticker               = ticker,
            horizon              = horizon,
            predicted_at         = datetime.now(),
            direction            = direction,
            probability          = round(prob_up_nudged, 4),
            regime_label         = regime_label,
            expected_return_low  = ret_low,
            expected_return_high = ret_high,
            volatility           = ann_vol,
        )
    except Exception as e:
        logger.debug(f"Could not record prediction for online learning: {e}")

    # ── 9. Recent accuracy from online learner ────────────────────────────────
    recent_accuracy_dict: dict = {}
    try:
        from backend.models.online_learner import get_recent_accuracy
        recent_accuracy_dict = get_recent_accuracy(horizon=horizon, days=90)
    except Exception:
        pass

    # ── 10. Build final result ────────────────────────────────────────────────

    acc = reg_acc if (reg_model is not None and reg_acc is not None) else global_acc

    # Simplify user signals for the dataclass (strip heavy content field)
    signals_summary = [
        {
            "id":          s.get("id", ""),
            "domain":      s.get("domain", ""),
            "signal_type": s.get("signal_type", ""),
            "source_tag":  s.get("source_tag", ""),
            "extracted_signal": s.get("extracted_signal", 0.0),
        }
        for s in user_signals
    ]

    return Prediction(
        ticker               = ticker,
        horizon              = horizon,
        direction            = direction,
        probability          = round(prob_up_nudged, 4),
        expected_return_low  = ret_low,
        expected_return_high = ret_high,
        volatility           = ann_vol,
        model_accuracy       = round(acc, 4),
        model_ready          = True,
        sector               = sector,
        model_type           = model_type,
        regime_label         = regime_label,
        regime               = regime_dict,
        explanation          = explanation,
        calc_chain           = calc_chain,
        user_signals_active  = signals_summary,
        recent_accuracy      = recent_accuracy_dict,
    )
