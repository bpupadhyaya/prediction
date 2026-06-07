import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import pickle
import json
from datetime import datetime, timedelta
from backend.config import MODELS_DIR, ACCURACY_THRESHOLD
from backend.database.duckdb_client import get_conn
import logging

logger = logging.getLogger(__name__)

MODEL_PATH = MODELS_DIR / "direction_model.pkl"
SCALER_PATH = MODELS_DIR / "scaler.pkl"
ACCURACY_LOG_PATH = MODELS_DIR / "accuracy_history.json"


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_values("date")
    c = df["close"]
    vol = df["volume"].fillna(0).astype(float)

    df["return_1d"] = c.pct_change(1)
    df["return_5d"] = c.pct_change(5)
    df["return_20d"] = c.pct_change(20)
    df["ma_5"] = c.rolling(5).mean() / c - 1
    df["ma_20"] = c.rolling(20).mean() / c - 1
    df["ma_50"] = c.rolling(50).mean() / c - 1
    df["volatility_20"] = c.pct_change().rolling(20).std()
    roll_mean = vol.rolling(20).mean().replace(0, np.nan)
    df["volume_ratio"] = vol / roll_mean

    # RSI
    delta = c.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))

    return df.dropna()


def prepare_training_data(horizon_days: int = 5) -> tuple[np.ndarray, np.ndarray]:
    conn = get_conn()
    df = conn.execute("""
        SELECT ticker, date, open, high, low, close, volume
        FROM prices
        ORDER BY ticker, date
    """).df()

    all_X, all_y = [], []
    feature_cols = ["return_1d", "return_5d", "return_20d", "ma_5", "ma_20",
                    "ma_50", "volatility_20", "volume_ratio", "rsi"]

    for ticker, group in df.groupby("ticker"):
        feat = build_features(group)
        if len(feat) < horizon_days + 50:
            continue
        feat["future_return"] = feat["close"].pct_change(horizon_days).shift(-horizon_days)
        feat["target"] = (feat["future_return"] > 0).astype(int)
        feat = feat.dropna()

        all_X.append(feat[feature_cols].values)
        all_y.append(feat["target"].values)

    if not all_X:
        return np.array([]), np.array([])

    X = np.vstack(all_X)
    y = np.concatenate(all_y)
    return X, y


def train_model(horizon_days: int = 5) -> float:
    logger.info("Training direction model...")
    X, y = prepare_training_data(horizon_days)
    if len(X) == 0:
        logger.warning("No training data available")
        return 0.0

    # Walk-forward split — last 20% is test (never train on future)
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    model = GradientBoostingClassifier(n_estimators=200, max_depth=4, learning_rate=0.05)
    model.fit(X_train_s, y_train)

    accuracy = accuracy_score(y_test, model.predict(X_test_s))
    logger.info(f"Validation directional accuracy: {accuracy:.3f}")

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)

    # Log accuracy
    history = {}
    if ACCURACY_LOG_PATH.exists():
        with open(ACCURACY_LOG_PATH) as f:
            history = json.load(f)
    history[datetime.now().isoformat()] = accuracy
    with open(ACCURACY_LOG_PATH, "w") as f:
        json.dump(history, f)

    return accuracy


def retrain_if_needed() -> None:
    retrained = False
    if not MODEL_PATH.exists():
        train_model()
        retrained = True
    elif ACCURACY_LOG_PATH.exists():
        with open(ACCURACY_LOG_PATH) as f:
            history = json.load(f)
        if history:
            latest_accuracy = list(history.values())[-1]
            if latest_accuracy < ACCURACY_THRESHOLD:
                logger.info(f"Accuracy {latest_accuracy:.3f} below threshold — retraining")
                train_model()
                retrained = True

    if retrained:
        try:
            from backend.models.exporter import export as export_onnx
            export_onnx(verify=False)
            logger.info("ONNX model re-exported after retraining")
        except Exception as e:
            logger.warning(f"ONNX export failed after retrain (non-fatal): {e}")
