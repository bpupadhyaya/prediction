import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import pickle
import json
import re
from datetime import datetime, timedelta
from backend.config import MODELS_DIR, ACCURACY_THRESHOLD
from backend.database.duckdb_client import get_conn
import logging

logger = logging.getLogger(__name__)

HORIZON_DAYS = {"1d": 1, "1w": 5, "1m": 21}
HORIZON_MODEL_PATHS  = {h: MODELS_DIR / f"model_{h}.pkl"  for h in HORIZON_DAYS}
HORIZON_SCALER_PATHS = {h: MODELS_DIR / f"scaler_{h}.pkl" for h in HORIZON_DAYS}
HORIZON_FEATURES_PATHS = {h: MODELS_DIR / f"features_{h}.json" for h in HORIZON_DAYS}
ACCURACY_LOG_PATH = MODELS_DIR / "accuracy_history.json"

SECTORS_DIR = MODELS_DIR / "sectors"
SECTORS_DIR.mkdir(parents=True, exist_ok=True)

# Legacy aliases so exporter can reference them
MODEL_PATH  = HORIZON_MODEL_PATHS["1w"]
SCALER_PATH = HORIZON_SCALER_PATHS["1w"]

# ── Feature columns ───────────────────────────────────────────────────────────

BASE_TECHNICAL_COLS = [
    "return_1d", "return_5d", "return_20d",
    "ma_5", "ma_20", "ma_50",
    "volatility_20", "volume_ratio", "rsi",
]

FUNDAMENTAL_COLS = [
    "earnings_surprise",   # QoQ earnings growth or actual surprise from earnings_history
    "short_ratio",         # Days to cover (shares short / avg daily volume)
]

MACRO_COLS = [
    "vix", "vix_regime",
    "yield_curve", "yield_curve_inverted",
    "fed_rate",
]

BASE_FEATURE_COLS = BASE_TECHNICAL_COLS + FUNDAMENTAL_COLS + MACRO_COLS

CROSS_COLS = ["rsi", "return_5d", "return_20d", "volatility_20", "volume_ratio", "short_ratio"]

FEATURE_COLS = BASE_FEATURE_COLS + [f"{c}_rank" for c in CROSS_COLS]

MODEL_VERSION = "2.0"  # Bump this when FEATURE_COLS change to force retrain


# ── Technical feature engineering ────────────────────────────────────────────

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_values("date")
    c   = df["close"]
    vol = df["volume"].fillna(0).astype(float)

    df["return_1d"]     = c.pct_change(1)
    df["return_5d"]     = c.pct_change(5)
    df["return_20d"]    = c.pct_change(20)
    df["ma_5"]          = c.rolling(5).mean() / c - 1
    df["ma_20"]         = c.rolling(20).mean() / c - 1
    df["ma_50"]         = c.rolling(50).mean() / c - 1
    df["volatility_20"] = c.pct_change().rolling(20).std()
    roll_mean = vol.rolling(20).mean().replace(0, np.nan)
    df["volume_ratio"]  = vol / roll_mean

    delta = c.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))

    return df.dropna(subset=BASE_TECHNICAL_COLS)


# ── Macro feature loading ─────────────────────────────────────────────────────

def _load_macro_timeseries() -> pd.DataFrame:
    """Load macro timeseries for as-of join during training."""
    try:
        from backend.data.macro_feed import load_macro_timeseries
        return load_macro_timeseries()
    except Exception as e:
        logger.warning(f"Could not load macro timeseries: {e}")
        return pd.DataFrame()


# ── Fundamentals feature loading ──────────────────────────────────────────────

def _load_fundamentals() -> pd.DataFrame:
    """
    Load fundamentals keyed by (ticker, report_date) for as-of join.
    Merges today's snapshot from `fundamentals` table with historical
    earnings surprises from `earnings_history` table.
    """
    conn = get_conn()

    # Current snapshot (most recent per ticker — from daily refresh)
    fund = conn.execute("""
        SELECT DISTINCT ON (ticker)
            ticker, report_date, earnings_surprise, short_ratio, short_pct_float
        FROM fundamentals
        ORDER BY ticker, report_date DESC
    """).df()

    # Historical earnings surprises (point-in-time)
    hist = conn.execute("""
        SELECT ticker, earnings_date AS report_date,
               earnings_surprise AS hist_surprise
        FROM earnings_history
        ORDER BY ticker, earnings_date
    """).df()

    return fund, hist


# ── Training data preparation ─────────────────────────────────────────────────

def _sector_slug(sector: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", sector.lower()).strip("_")


def prepare_all_training_data(horizon_days: int) -> pd.DataFrame:
    """
    Build full feature matrix for all tickers, all dates.
    Joins macro (by date) and fundamentals (by ticker+date as-of).
    Returns a DataFrame ready for training with 'target' and 'sector' columns.
    """
    conn = get_conn()

    # ── Price data ────────────────────────────────────────────────────────────
    price_df = conn.execute("""
        SELECT ticker, CAST(date AS VARCHAR) as date, open, high, low, close, volume
        FROM prices
        ORDER BY ticker, date
    """).df()
    price_df["date"] = pd.to_datetime(price_df["date"]).dt.as_unit("ns")

    # ── Stock sector map ──────────────────────────────────────────────────────
    sectors = conn.execute("""
        SELECT ticker, COALESCE(sector, 'Unknown') as sector
        FROM stocks
    """).df()
    sector_map = dict(zip(sectors["ticker"], sectors["sector"]))

    # ── Macro timeseries ──────────────────────────────────────────────────────
    macro_ts = _load_macro_timeseries()
    has_macro = not macro_ts.empty

    # ── Latest fundamentals per ticker ────────────────────────────────────────
    fund_snap = conn.execute("""
        SELECT DISTINCT ON (ticker) ticker, earnings_surprise, short_ratio
        FROM fundamentals
        WHERE earnings_surprise IS NOT NULL
        ORDER BY ticker, report_date DESC
    """).df()
    fund_map = {
        row["ticker"]: {"earnings_surprise": row["earnings_surprise"], "short_ratio": row["short_ratio"]}
        for _, row in fund_snap.iterrows()
    }

    # ── Historical earnings surprises per ticker ──────────────────────────────
    hist_surp = conn.execute("""
        SELECT ticker, earnings_date, earnings_surprise
        FROM earnings_history
        ORDER BY ticker, earnings_date
    """).df()
    hist_surp["earnings_date"] = pd.to_datetime(hist_surp["earnings_date"]).dt.as_unit("ns")

    # ── Build features per ticker ─────────────────────────────────────────────
    all_feat = []
    for ticker, group in price_df.groupby("ticker"):
        feat = build_features(group)
        if len(feat) < horizon_days + 60:
            continue

        feat = feat.copy()
        feat["future_return"] = feat["close"].pct_change(horizon_days).shift(-horizon_days)
        feat["target"]        = (feat["future_return"] > 0).astype(int)
        feat = feat.dropna(subset=BASE_TECHNICAL_COLS + ["target"])
        if feat.empty:
            continue

        # Fundamentals: point-in-time from earnings_history where available, else latest snapshot
        ticker_hist = hist_surp[hist_surp["ticker"] == ticker].sort_values("earnings_date")
        if not ticker_hist.empty:
            feat = pd.merge_asof(
                feat.sort_values("date"),
                ticker_hist[["earnings_date", "earnings_surprise"]].rename(columns={"earnings_date": "date"}),
                on="date", direction="backward",
                suffixes=("", "_hist"),
            )
            if "earnings_surprise_hist" in feat.columns:
                feat["earnings_surprise"] = feat["earnings_surprise_hist"].fillna(
                    fund_map.get(ticker, {}).get("earnings_surprise", 0.0)
                )
                feat = feat.drop(columns=["earnings_surprise_hist"])
            else:
                feat["earnings_surprise"] = fund_map.get(ticker, {}).get("earnings_surprise", 0.0)
        else:
            feat["earnings_surprise"] = fund_map.get(ticker, {}).get("earnings_surprise", 0.0)

        feat["short_ratio"] = fund_map.get(ticker, {}).get("short_ratio", 0.0)

        # Macro: as-of join by date
        if has_macro:
            feat = pd.merge_asof(
                feat.sort_values("date"),
                macro_ts.sort_values("date"),
                on="date", direction="backward",
            )
            for col in MACRO_COLS:
                if col not in feat.columns:
                    feat[col] = 0.0
        else:
            for col in MACRO_COLS:
                feat[col] = 0.0

        feat["sector"] = sector_map.get(ticker, "Unknown")
        feat["ticker"] = ticker

        all_feat.append(feat[["date", "ticker", "sector"] + BASE_FEATURE_COLS + ["target"]])

    if not all_feat:
        return pd.DataFrame()

    combined = pd.concat(all_feat, ignore_index=True).sort_values("date")

    # ── Cross-sectional percentile ranks ──────────────────────────────────────
    for col in CROSS_COLS:
        if col in combined.columns:
            combined[f"{col}_rank"] = combined.groupby("date")[col].rank(pct=True)
        else:
            combined[f"{col}_rank"] = 0.5

    combined = combined.dropna(subset=[c for c in FEATURE_COLS if c in combined.columns])

    # Fill any remaining NaNs in new features with 0 (no data = neutral signal)
    for col in FEATURE_COLS:
        if col in combined.columns:
            combined[col] = combined[col].fillna(0.0)

    return combined


# ── Walk-forward training ─────────────────────────────────────────────────────

def _fit_eval(train_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple:
    """Fit GBM on train, evaluate on test. Returns (model, scaler, accuracy)."""
    X_tr = train_df[FEATURE_COLS].values.astype(float)
    y_tr = train_df["target"].values
    X_te = test_df[FEATURE_COLS].values.astype(float)
    y_te = test_df["target"].values

    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_te_s = scaler.transform(X_te)

    model = GradientBoostingClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.8, random_state=42,
    )
    model.fit(X_tr_s, y_tr)
    acc = accuracy_score(y_te, model.predict(X_te_s))
    return model, scaler, float(acc)


def _walk_forward_train(combined: pd.DataFrame) -> tuple[object, object, float]:
    """
    Expanding-window walk-forward cross-validation.
    Folds: 126-day (≈6-month) step, 252×2-day minimum training window.
    Final model is trained on ALL data (for production use).
    Returns (final_model, final_scaler, avg_cv_accuracy).
    """
    all_dates = sorted(combined["date"].unique())
    n = len(all_dates)

    MIN_TRAIN = 252 * 2   # 2 years of dates
    STEP      = 126        # 6-month folds

    fold_accuracies = []

    if n > MIN_TRAIN + STEP:
        for fold_end_idx in range(MIN_TRAIN, n - STEP, STEP):
            train_end = all_dates[fold_end_idx]
            test_end  = all_dates[min(fold_end_idx + STEP, n - 1)]

            train = combined[combined["date"] < train_end]
            test  = combined[(combined["date"] >= train_end) & (combined["date"] < test_end)]

            if len(train) < 500 or len(test) < 100:
                continue

            _, _, acc = _fit_eval(train, test)
            fold_accuracies.append(acc)
            logger.debug(f"  Walk-forward fold: train<{train_end.date()} test [{train_end.date()},{test_end.date()}] acc={acc:.4f}")

    avg_acc = float(np.mean(fold_accuracies)) if fold_accuracies else 0.5
    logger.info(f"  Walk-forward: {len(fold_accuracies)} folds, avg accuracy={avg_acc:.4f}")

    # Final model: train on everything (maximises data for production predictions)
    X_all = combined[FEATURE_COLS].values.astype(float)
    y_all = combined["target"].values
    final_scaler = StandardScaler()
    X_all_s = final_scaler.fit_transform(X_all)
    final_model = GradientBoostingClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.8, random_state=42,
    )
    final_model.fit(X_all_s, y_all)

    return final_model, final_scaler, avg_acc


def _save_model(model, scaler, horizon: str) -> None:
    with open(HORIZON_MODEL_PATHS[horizon], "wb") as f:
        pickle.dump(model, f)
    with open(HORIZON_SCALER_PATHS[horizon], "wb") as f:
        pickle.dump(scaler, f)
    with open(HORIZON_FEATURES_PATHS[horizon], "w") as f:
        json.dump({"feature_cols": FEATURE_COLS, "version": MODEL_VERSION}, f)


def _save_sector_model(model, scaler, sector: str, horizon: str, accuracy: float | None = None) -> None:
    slug = _sector_slug(sector)
    path_m = SECTORS_DIR / f"model_{slug}_{horizon}.pkl"
    path_s = SECTORS_DIR / f"scaler_{slug}_{horizon}.pkl"
    path_f = SECTORS_DIR / f"features_{slug}_{horizon}.json"
    with open(path_m, "wb") as f:
        pickle.dump(model, f)
    with open(path_s, "wb") as f:
        pickle.dump(scaler, f)
    meta = {"feature_cols": FEATURE_COLS, "version": MODEL_VERSION, "sector": sector}
    if accuracy is not None:
        meta["accuracy"] = accuracy
    with open(path_f, "w") as f:
        json.dump(meta, f)


def _update_accuracy_log(horizon: str, accuracy: float) -> None:
    history = {}
    if ACCURACY_LOG_PATH.exists():
        with open(ACCURACY_LOG_PATH) as f:
            history = json.load(f)
    if horizon not in history:
        history[horizon] = {}
    history[horizon][datetime.now().isoformat()] = accuracy
    with open(ACCURACY_LOG_PATH, "w") as f:
        json.dump(history, f)


# ── Public training API ───────────────────────────────────────────────────────

def train_model(horizon: str = "1w") -> float:
    """Train (or retrain) the global model for one horizon. Returns walk-forward CV accuracy."""
    horizon_days = HORIZON_DAYS.get(horizon, 5)
    logger.info(f"Training global {horizon} model (target={horizon_days}d)...")

    combined = prepare_all_training_data(horizon_days)
    if combined.empty:
        logger.warning(f"No training data for {horizon}")
        return 0.0

    model, scaler, avg_acc = _walk_forward_train(combined)
    _save_model(model, scaler, horizon)
    _update_accuracy_log(horizon, avg_acc)
    logger.info(f"[{horizon}] Global model trained, walk-forward accuracy: {avg_acc:.4f}")
    return avg_acc


def train_sector_models(horizon: str = "1w") -> dict[str, float]:
    """
    Train one GBM per GICS sector using walk-forward CV.
    Requires ≥5 tickers AND ≥2000 training rows per sector.
    Returns {sector: accuracy}.
    """
    horizon_days = HORIZON_DAYS.get(horizon, 5)
    combined = prepare_all_training_data(horizon_days)
    if combined.empty:
        return {}

    results = {}
    for sector in combined["sector"].unique():
        if sector in ("Unknown", ""):
            continue
        sector_data = combined[combined["sector"] == sector]
        n_tickers = sector_data["ticker"].nunique()
        if n_tickers < 5 or len(sector_data) < 2000:
            logger.debug(f"Skipping sector {sector!r}: {n_tickers} tickers, {len(sector_data)} rows")
            continue

        model, scaler, avg_acc = _walk_forward_train(sector_data)
        _save_sector_model(model, scaler, sector, horizon, accuracy=avg_acc)
        results[sector] = avg_acc
        logger.info(f"[{horizon}] Sector {sector!r}: walk-forward accuracy={avg_acc:.4f} ({n_tickers} tickers)")

    return results


def train_all_models() -> float:
    """Train global + sector models for all horizons. Returns average CV accuracy."""
    all_accs = []
    for horizon in HORIZON_DAYS:
        global_acc = train_model(horizon)
        all_accs.append(global_acc)
        sector_accs = train_sector_models(horizon)
        if sector_accs:
            all_accs.extend(sector_accs.values())

    avg = float(np.mean(all_accs)) if all_accs else 0.0
    logger.info(f"All models trained — overall average accuracy: {avg:.4f}")
    return avg


def models_need_retrain() -> bool:
    """True if any model file is missing OR was trained with a different feature set."""
    for horizon in HORIZON_DAYS:
        if not HORIZON_MODEL_PATHS[horizon].exists():
            return True
        meta_path = HORIZON_FEATURES_PATHS[horizon]
        if not meta_path.exists():
            return True  # Old model without feature metadata
        with open(meta_path) as f:
            meta = json.load(f)
        if meta.get("version") != MODEL_VERSION:
            return True
    return False


def retrain_if_needed() -> None:
    if models_need_retrain():
        logger.info("Models missing or outdated — retraining all...")
        train_all_models()
        _try_onnx_export()
        return

    # Check accuracy drift
    if ACCURACY_LOG_PATH.exists():
        with open(ACCURACY_LOG_PATH) as f:
            history = json.load(f)
        # Check 1w horizon (most important)
        h1w = history.get("1w", {})
        if h1w:
            latest = list(h1w.values())[-1]
            if latest < ACCURACY_THRESHOLD:
                logger.info(f"Accuracy {latest:.4f} below threshold {ACCURACY_THRESHOLD} — retraining")
                train_all_models()
                _try_onnx_export()


def _try_onnx_export() -> None:
    try:
        from backend.models.exporter import export as export_onnx
        export_onnx(verify=False)
        logger.info("ONNX model re-exported after retraining")
    except Exception as e:
        logger.warning(f"ONNX export failed (non-fatal): {e}")


def latest_accuracy(horizon: str = "1w") -> float:
    if not ACCURACY_LOG_PATH.exists():
        return 0.0
    with open(ACCURACY_LOG_PATH) as f:
        history = json.load(f)
    h = history.get(horizon, {})
    return float(list(h.values())[-1]) if h else 0.0
