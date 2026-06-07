import pickle
import numpy as np
import json
from dataclasses import dataclass
from backend.config import MODELS_DIR
from backend.models.trainer import build_features, MODEL_PATH, SCALER_PATH, ACCURACY_LOG_PATH
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
    model_accuracy: float   # recent model accuracy — always shown to user
    model_ready: bool


FEATURE_COLS = ["return_1d", "return_5d", "return_20d", "ma_5", "ma_20",
                "ma_50", "volatility_20", "volume_ratio", "rsi"]


def _load_model():
    if not MODEL_PATH.exists() or not SCALER_PATH.exists():
        return None, None
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)
    return model, scaler


def _latest_accuracy() -> float:
    if not ACCURACY_LOG_PATH.exists():
        return 0.0
    with open(ACCURACY_LOG_PATH) as f:
        history = json.load(f)
    return list(history.values())[-1] if history else 0.0


def predict_ticker(ticker: str, horizon: str = "1w") -> Prediction:
    model, scaler = _load_model()
    if model is None:
        return Prediction(ticker, horizon, "unknown", 0.5, 0.0, 0.0, 0.0, 0.0, False)

    conn = get_conn()
    df = conn.execute("""
        SELECT date, open, high, low, close, volume
        FROM prices
        WHERE ticker = ?
        ORDER BY date DESC
        LIMIT 120
    """, [ticker]).df().sort_values("date")

    if len(df) < 60:
        return Prediction(ticker, horizon, "unknown", 0.5, 0.0, 0.0, 0.0, _latest_accuracy(), False)

    feat = build_features(df)
    if feat.empty:
        return Prediction(ticker, horizon, "unknown", 0.5, 0.0, 0.0, 0.0, _latest_accuracy(), False)

    X = feat[FEATURE_COLS].iloc[-1:].values
    X_s = scaler.transform(X)

    prob_up = model.predict_proba(X_s)[0][1]
    direction = "up" if prob_up >= 0.5 else "down"

    # Estimate return range from recent volatility
    vol = feat["volatility_20"].iloc[-1]
    horizon_days = {"1d": 1, "1w": 5, "1m": 21}.get(horizon, 5)
    vol_horizon = vol * np.sqrt(horizon_days)
    expected = (prob_up - 0.5) * 2 * vol_horizon

    return Prediction(
        ticker=ticker,
        horizon=horizon,
        direction=direction,
        probability=round(float(prob_up), 4),
        expected_return_low=round(float(expected - vol_horizon), 4),
        expected_return_high=round(float(expected + vol_horizon), 4),
        volatility=round(float(vol_horizon * np.sqrt(252 / horizon_days)), 4),
        model_accuracy=_latest_accuracy(),
        model_ready=True,
    )
