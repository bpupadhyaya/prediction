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

# Per-horizon model files
HORIZON_DAYS = {"1d": 1, "1w": 5, "1m": 21}
HORIZON_MODEL_PATHS = {h: MODELS_DIR / f"model_{h}.pkl" for h in HORIZON_DAYS}
HORIZON_SCALER_PATHS = {h: MODELS_DIR / f"scaler_{h}.pkl" for h in HORIZON_DAYS}
ACCURACY_LOG_PATH = MODELS_DIR / "accuracy_history.json"

# Legacy paths — kept so exporter can reference them (points to 1w model)
MODEL_PATH = HORIZON_MODEL_PATHS["1w"]
SCALER_PATH = HORIZON_SCALER_PATHS["1w"]

# Base technical features computed per ticker
BASE_FEATURE_COLS = [
    "return_1d", "return_5d", "return_20d",
    "ma_5", "ma_20", "ma_50",
    "volatility_20", "volume_ratio", "rsi",
]
# Cross-sectional rank features: percentile rank within peer universe on the same date
CROSS_COLS = ["rsi", "return_5d", "return_20d", "volatility_20", "volume_ratio"]
FEATURE_COLS = BASE_FEATURE_COLS + [f"{c}_rank" for c in CROSS_COLS]


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

    delta = c.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))

    return df.dropna()


def prepare_training_data(horizon_days: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    conn = get_conn()
    df = conn.execute("""
        SELECT ticker, date, open, high, low, close, volume
        FROM prices
        ORDER BY ticker, date
    """).df()
    df["date"] = pd.to_datetime(df["date"])

    all_feat = []
    for ticker, group in df.groupby("ticker"):
        feat = build_features(group)
        if len(feat) < horizon_days + 50:
            continue
        feat = feat.copy()
        feat["date"] = pd.to_datetime(feat["date"])
        feat["future_return"] = feat["close"].pct_change(horizon_days).shift(-horizon_days)
        feat["target"] = (feat["future_return"] > 0).astype(int)
        feat = feat.dropna(subset=BASE_FEATURE_COLS + ["target"])
        if feat.empty:
            continue
        all_feat.append(feat[["date"] + BASE_FEATURE_COLS + ["target"]])

    if not all_feat:
        return np.array([]), np.array([]), np.array([]), np.array([])

    combined = pd.concat(all_feat, ignore_index=True)
    combined = combined.sort_values("date")

    # Cross-sectional percentile ranks: on each date, rank each feature vs all peers
    for col in CROSS_COLS:
        combined[f"{col}_rank"] = combined.groupby("date")[col].rank(pct=True)

    combined = combined.dropna(subset=FEATURE_COLS)

    # Time-based split — last 20% of dates are test (never train on future)
    all_dates = sorted(combined["date"].unique())
    if len(all_dates) < 10:
        return np.array([]), np.array([]), np.array([]), np.array([])
    split_date = all_dates[int(len(all_dates) * 0.8)]

    train = combined[combined["date"] < split_date]
    test = combined[combined["date"] >= split_date]

    return (
        train[FEATURE_COLS].values, train["target"].values,
        test[FEATURE_COLS].values, test["target"].values,
    )


def train_model(horizon: str = "1w") -> float:
    horizon_days = HORIZON_DAYS.get(horizon, 5)
    logger.info(f"Training {horizon} model (target={horizon_days}d)...")
    X_train, y_train, X_test, y_test = prepare_training_data(horizon_days)

    if len(X_train) == 0:
        logger.warning(f"No training data for {horizon}")
        return 0.0

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    model = GradientBoostingClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42
    )
    model.fit(X_train_s, y_train)

    accuracy = accuracy_score(y_test, model.predict(X_test_s))
    logger.info(f"[{horizon}] Validation accuracy: {accuracy:.3f}")

    with open(HORIZON_MODEL_PATHS[horizon], "wb") as f:
        pickle.dump(model, f)
    with open(HORIZON_SCALER_PATHS[horizon], "wb") as f:
        pickle.dump(scaler, f)

    return accuracy


def train_all_models() -> float:
    """Train one model per prediction horizon. Returns average accuracy."""
    accuracies = {}
    for horizon in HORIZON_DAYS:
        acc = train_model(horizon)
        accuracies[horizon] = acc

    avg_acc = sum(accuracies.values()) / max(1, len(accuracies))
    history = {}
    if ACCURACY_LOG_PATH.exists():
        with open(ACCURACY_LOG_PATH) as f:
            history = json.load(f)
    history[datetime.now().isoformat()] = avg_acc
    with open(ACCURACY_LOG_PATH, "w") as f:
        json.dump(history, f)

    logger.info(f"All models trained — accuracies: {accuracies} | avg: {avg_acc:.3f}")
    return avg_acc


def retrain_if_needed() -> None:
    models_missing = any(not p.exists() for p in HORIZON_MODEL_PATHS.values())

    if models_missing:
        train_all_models()
        _try_onnx_export()
        return

    if ACCURACY_LOG_PATH.exists():
        with open(ACCURACY_LOG_PATH) as f:
            history = json.load(f)
        if history:
            latest_accuracy = list(history.values())[-1]
            if latest_accuracy < ACCURACY_THRESHOLD:
                logger.info(f"Accuracy {latest_accuracy:.3f} below threshold — retraining")
                train_all_models()
                _try_onnx_export()


def _try_onnx_export() -> None:
    try:
        from backend.models.exporter import export as export_onnx
        export_onnx(verify=False)
        logger.info("ONNX model re-exported after retraining")
    except Exception as e:
        logger.warning(f"ONNX export failed after retrain (non-fatal): {e}")
