import pickle
import numpy as np
import json
import pandas as pd
from dataclasses import dataclass
from datetime import date
from backend.config import MODELS_DIR
from backend.models.trainer import (
    build_features,
    BASE_FEATURE_COLS, CROSS_COLS, FEATURE_COLS,
    HORIZON_MODEL_PATHS, HORIZON_SCALER_PATHS,
    ACCURACY_LOG_PATH, HORIZON_DAYS,
)
from backend.database.duckdb_client import get_conn
import logging

logger = logging.getLogger(__name__)


@dataclass
class Prediction:
    ticker: str
    horizon: str
    direction: str          # "up" | "down"
    probability: float      # probability of going up
    expected_return_low: float
    expected_return_high: float
    volatility: float
    model_accuracy: float
    model_ready: bool


# Cross-sectional feature cache — recomputed at most once per calendar day
_cs_cache: dict = {"date": None, "data": None}


def _load_model(horizon: str):
    model_path = HORIZON_MODEL_PATHS.get(horizon)
    scaler_path = HORIZON_SCALER_PATHS.get(horizon)
    if not model_path or not model_path.exists() or not scaler_path or not scaler_path.exists():
        return None, None
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    return model, scaler


def _latest_accuracy() -> float:
    if not ACCURACY_LOG_PATH.exists():
        return 0.0
    with open(ACCURACY_LOG_PATH) as f:
        history = json.load(f)
    return list(history.values())[-1] if history else 0.0


def _get_cross_sectional_features() -> pd.DataFrame | None:
    """
    Load the latest technical features for all tickers and compute cross-sectional
    percentile ranks (matching what was used at training time).
    Results are cached for the current calendar day.
    """
    today = date.today()
    if _cs_cache["date"] == today and _cs_cache["data"] is not None:
        return _cs_cache["data"]

    conn = get_conn()
    df = conn.execute("""
        SELECT ticker, date, open, high, low, close, volume
        FROM prices
        WHERE date >= CURRENT_DATE - INTERVAL 120 DAY
        ORDER BY ticker, date
    """).df()

    rows = []
    for ticker, group in df.groupby("ticker"):
        feat = build_features(group)
        if feat.empty:
            continue
        last = feat.iloc[-1]
        row = {col: last[col] for col in BASE_FEATURE_COLS if col in feat.columns}
        row["ticker"] = ticker
        row["_volatility_ref"] = last["volatility_20"]
        rows.append(row)

    if not rows:
        return None

    cs = pd.DataFrame(rows)
    for col in CROSS_COLS:
        if col in cs.columns:
            cs[f"{col}_rank"] = cs[col].rank(pct=True)

    _cs_cache["date"] = today
    _cs_cache["data"] = cs
    return cs


def predict_ticker(ticker: str, horizon: str = "1w") -> Prediction:
    model, scaler = _load_model(horizon)
    if model is None:
        return Prediction(ticker, horizon, "unknown", 0.5, 0.0, 0.0, 0.0, 0.0, False)

    cs = _get_cross_sectional_features()
    if cs is None:
        return Prediction(ticker, horizon, "unknown", 0.5, 0.0, 0.0, 0.0, _latest_accuracy(), False)

    row = cs[cs["ticker"] == ticker]
    if row.empty:
        return Prediction(ticker, horizon, "unknown", 0.5, 0.0, 0.0, 0.0, _latest_accuracy(), False)

    missing = [c for c in FEATURE_COLS if c not in row.columns]
    if missing:
        logger.warning(f"Missing features for {ticker}: {missing}")
        return Prediction(ticker, horizon, "unknown", 0.5, 0.0, 0.0, 0.0, _latest_accuracy(), False)

    X = row[FEATURE_COLS].values.astype(float)
    if np.any(np.isnan(X)):
        return Prediction(ticker, horizon, "unknown", 0.5, 0.0, 0.0, 0.0, _latest_accuracy(), False)

    X_s = scaler.transform(X)
    prob_up = float(model.predict_proba(X_s)[0][1])
    direction = "up" if prob_up >= 0.5 else "down"

    vol = float(row["_volatility_ref"].iloc[0])
    horizon_days = HORIZON_DAYS.get(horizon, 5)
    vol_horizon = vol * np.sqrt(horizon_days)
    expected = (prob_up - 0.5) * 2 * vol_horizon

    return Prediction(
        ticker=ticker,
        horizon=horizon,
        direction=direction,
        probability=round(prob_up, 4),
        expected_return_low=round(float(expected - vol_horizon), 4),
        expected_return_high=round(float(expected + vol_horizon), 4),
        volatility=round(float(vol_horizon * np.sqrt(252 / max(1, horizon_days))), 4),
        model_accuracy=_latest_accuracy(),
        model_ready=True,
    )
