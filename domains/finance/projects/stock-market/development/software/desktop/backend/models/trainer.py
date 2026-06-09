"""
Prediction Engine — Layer 4 of the ADPS architecture.

Trains a regime-aware GBM ensemble:
  - One GLOBAL model (all data)
  - One model per VIX volatility regime (LOW/NORMAL/ELEVATED/CRISIS)
  - Sector models where data allows

Feature set: 38 Tier 1 factors across macro, technical, fundamental, cross-asset.
"""

import json
import logging
import pickle
import re
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler

from backend.config import MODELS_DIR, ACCURACY_THRESHOLD
from backend.database.duckdb_client import get_conn

logger = logging.getLogger(__name__)

HORIZON_DAYS = {"1d": 1, "1w": 5, "1m": 21}
HORIZON_MODEL_PATHS   = {h: MODELS_DIR / f"model_{h}.pkl"    for h in HORIZON_DAYS}
HORIZON_SCALER_PATHS  = {h: MODELS_DIR / f"scaler_{h}.pkl"   for h in HORIZON_DAYS}
HORIZON_FEATURES_PATHS = {h: MODELS_DIR / f"features_{h}.json" for h in HORIZON_DAYS}
ACCURACY_LOG_PATH     = MODELS_DIR / "accuracy_history.json"

SECTORS_DIR = MODELS_DIR / "sectors"
SECTORS_DIR.mkdir(parents=True, exist_ok=True)

REGIMES_DIR = MODELS_DIR / "regimes"
REGIMES_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH  = HORIZON_MODEL_PATHS["1w"]
SCALER_PATH = HORIZON_SCALER_PATHS["1w"]

MODEL_VERSION = "3.0"   # Bump triggers full retrain

# ── Feature columns ───────────────────────────────────────────────────────────

BASE_TECHNICAL_COLS = [
    "return_1d", "return_5d", "return_20d", "return_60d", "return_252d",
    "ma_5", "ma_20", "ma_50",
    "volatility_20", "volume_ratio", "rsi",
    "high_52w_ratio", "amihud_illiquidity",
]

FUNDAMENTAL_COLS = [
    "earnings_surprise",
    "short_ratio",
]

MACRO_COLS = [
    "vix", "vix_regime",
    "yield_curve", "yield_curve_inverted",
    "fed_rate",
    "hy_spread", "ig_spread", "tips_real_yield",
    "m2_growth_yoy", "initial_claims", "nfci", "pce_core_yoy",
    "fed_balance_sheet",
]

CROSS_ASSET_COLS = [
    "dxy_ret20", "gold_equity_ratio",
    "copper_ret20", "usdjpy_ret5", "oil_ret20",
    "btc_spx_corr", "vvix",
]

REGIME_COLS = [
    "monetary_regime", "credit_regime", "vol_regime_code", "yc_regime_code",
]

BASE_FEATURE_COLS = (
    BASE_TECHNICAL_COLS + FUNDAMENTAL_COLS + MACRO_COLS +
    CROSS_ASSET_COLS + REGIME_COLS
)

# Cross-sectional rank columns (computed per date across all tickers)
CROSS_RANK_SOURCE_COLS = [
    "rsi", "return_5d", "return_20d", "return_252d",
    "volatility_20", "volume_ratio", "short_ratio",
]

FEATURE_COLS = BASE_FEATURE_COLS + [f"{c}_rank" for c in CROSS_RANK_SOURCE_COLS]

# Vol regime codes (0-3) used to select regime-specific models
VOL_REGIME_KEYS = {0: "low", 1: "normal", 2: "elevated", 3: "crisis"}


# ── Technical feature engineering ─────────────────────────────────────────────

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_values("date")
    c   = df["close"]
    vol = df["volume"].fillna(0).astype(float)
    hi  = df.get("high", c)
    dv  = c * vol   # dollar volume

    df["return_1d"]    = c.pct_change(1)
    df["return_5d"]    = c.pct_change(5)
    df["return_20d"]   = c.pct_change(20)
    df["return_60d"]   = c.pct_change(60)
    df["return_252d"]  = c.pct_change(252)
    df["ma_5"]         = c.rolling(5).mean() / c - 1
    df["ma_20"]        = c.rolling(20).mean() / c - 1
    df["ma_50"]        = c.rolling(50).mean() / c - 1
    df["volatility_20"] = c.pct_change().rolling(20).std()

    roll_mean = vol.rolling(20).mean().replace(0, np.nan)
    df["volume_ratio"] = vol / roll_mean

    # RSI (14)
    delta = c.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))

    # 52-week high ratio
    high_52w = c.rolling(252).max()
    df["high_52w_ratio"] = c / high_52w.replace(0, np.nan)

    # Amihud illiquidity: |return| / dollar volume (×10^6 for scale)
    abs_ret = c.pct_change().abs()
    dv_roll = dv.rolling(20).mean().replace(0, np.nan)
    df["amihud_illiquidity"] = (abs_ret / dv_roll * 1e6).rolling(5).mean()

    return df.dropna(subset=["return_1d", "return_5d", "return_20d", "rsi"])


# ── Training data preparation ─────────────────────────────────────────────────

def _load_macro_ts() -> pd.DataFrame:
    try:
        from backend.data.macro_feed import load_macro_timeseries
        return load_macro_timeseries()
    except Exception as e:
        logger.warning(f"Could not load macro timeseries: {e}")
        return pd.DataFrame()


def prepare_all_training_data(horizon_days: int) -> pd.DataFrame:
    conn = get_conn()

    price_df = conn.execute("""
        SELECT ticker, CAST(date AS VARCHAR) as date, open, high, low, close, volume
        FROM prices ORDER BY ticker, date
    """).df()
    price_df["date"] = pd.to_datetime(price_df["date"])

    sectors = conn.execute("""
        SELECT ticker, COALESCE(sector, 'Unknown') as sector FROM stocks
    """).df()
    sector_map = dict(zip(sectors["ticker"], sectors["sector"]))

    macro_ts = _load_macro_ts()
    macro_cols = [c for c in macro_ts.columns if c != "date"] if not macro_ts.empty else []
    has_macro  = not macro_ts.empty

    fund_snap = conn.execute("""
        SELECT DISTINCT ON (ticker) ticker, earnings_surprise, short_ratio
        FROM fundamentals WHERE earnings_surprise IS NOT NULL
        ORDER BY ticker, report_date DESC
    """).df()
    fund_map = {
        r["ticker"]: {"earnings_surprise": r["earnings_surprise"], "short_ratio": r["short_ratio"]}
        for _, r in fund_snap.iterrows()
    }

    hist_surp = conn.execute("""
        SELECT ticker, earnings_date, earnings_surprise
        FROM earnings_history ORDER BY ticker, earnings_date
    """).df()
    hist_surp["earnings_date"] = pd.to_datetime(hist_surp["earnings_date"])

    all_feat = []
    for ticker, group in price_df.groupby("ticker"):
        feat = build_features(group)
        if len(feat) < max(horizon_days + 60, 280):
            continue

        feat = feat.copy()
        feat["future_return"] = feat["close"].pct_change(horizon_days).shift(-horizon_days)
        feat["target"]        = (feat["future_return"] > 0).astype(int)
        feat = feat.dropna(subset=["return_1d", "rsi", "return_252d", "target"])
        if feat.empty:
            continue

        # Earnings surprise — point-in-time
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
                feat.drop(columns=["earnings_surprise_hist"], inplace=True)
            else:
                feat["earnings_surprise"] = fund_map.get(ticker, {}).get("earnings_surprise", 0.0)
        else:
            feat["earnings_surprise"] = fund_map.get(ticker, {}).get("earnings_surprise", 0.0)

        feat["short_ratio"] = fund_map.get(ticker, {}).get("short_ratio", 0.0)

        # Macro as-of join
        if has_macro:
            feat = pd.merge_asof(
                feat.sort_values("date"),
                macro_ts.sort_values("date"),
                on="date", direction="backward",
            )
            for col in MACRO_COLS + CROSS_ASSET_COLS:
                if col not in feat.columns:
                    feat[col] = 0.0
        else:
            for col in MACRO_COLS + CROSS_ASSET_COLS:
                feat[col] = 0.0

        # Regime columns from macro
        feat["monetary_regime"] = feat.get("monetary_regime_computed",
            feat["fed_rate"].apply(lambda v: 2.0 if v > 4.0 else (0.0 if v < 2.0 else 1.0))
            if "fed_rate" in feat.columns else 1.0)
        feat["credit_regime"] = feat.get("hy_spread",
            pd.Series(300.0, index=feat.index)).apply(
            lambda v: 2.0 if v >= 600 else (1.0 if v >= 350 else 0.0))
        feat["vol_regime_code"] = feat.get("vix",
            pd.Series(20.0, index=feat.index)).apply(
            lambda v: 3.0 if v >= 35 else (2.0 if v >= 25 else (1.0 if v >= 15 else 0.0)))
        feat["yc_regime_code"] = feat.get("yield_curve",
            pd.Series(0.5, index=feat.index)).apply(
            lambda v: 2.0 if v < 0 else (1.0 if v < 0.5 else 0.0))

        feat["sector"] = sector_map.get(ticker, "Unknown")
        feat["ticker"] = ticker

        available = ["date", "ticker", "sector"] + [c for c in BASE_FEATURE_COLS if c in feat.columns] + ["target"]
        all_feat.append(feat[available])

    if not all_feat:
        return pd.DataFrame()

    combined = pd.concat(all_feat, ignore_index=True).sort_values("date")

    # Cross-sectional percentile ranks
    for col in CROSS_RANK_SOURCE_COLS:
        if col in combined.columns:
            combined[f"{col}_rank"] = combined.groupby("date")[col].rank(pct=True)
        else:
            combined[f"{col}_rank"] = 0.5

    # Fill missing features with neutral values
    for col in FEATURE_COLS:
        if col in combined.columns:
            combined[col] = combined[col].fillna(0.0)
        else:
            combined[col] = 0.0

    combined = combined.dropna(subset=["return_5d", "rsi", "target"])
    return combined


# ── Walk-forward training ─────────────────────────────────────────────────────

def _fit_eval(train_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple:
    avail_feats = [c for c in FEATURE_COLS if c in train_df.columns]
    X_tr = train_df[avail_feats].values.astype(float)
    y_tr = train_df["target"].values
    X_te = test_df[avail_feats].values.astype(float)
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


def _walk_forward_train(combined: pd.DataFrame) -> tuple:
    """Expanding-window walk-forward CV. Returns (model, scaler, avg_cv_acc)."""
    all_dates = sorted(combined["date"].unique())
    n = len(all_dates)
    MIN_TRAIN = 252 * 2
    STEP      = 126

    fold_accs = []
    if n > MIN_TRAIN + STEP:
        for fold_end in range(MIN_TRAIN, n - STEP, STEP):
            train_end = all_dates[fold_end]
            test_end  = all_dates[min(fold_end + STEP, n - 1)]
            train = combined[combined["date"] < train_end]
            test  = combined[(combined["date"] >= train_end) & (combined["date"] < test_end)]
            if len(train) < 500 or len(test) < 100:
                continue
            _, _, acc = _fit_eval(train, test)
            fold_accs.append(acc)

    avg_acc = float(np.mean(fold_accs)) if fold_accs else 0.5
    logger.info(f"  Walk-forward: {len(fold_accs)} folds, avg acc={avg_acc:.4f}")

    avail_feats = [c for c in FEATURE_COLS if c in combined.columns]
    X_all = combined[avail_feats].values.astype(float)
    y_all = combined["target"].values
    scaler = StandardScaler()
    X_all_s = scaler.fit_transform(X_all)
    model = GradientBoostingClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.8, random_state=42,
    )
    model.fit(X_all_s, y_all)
    return model, scaler, avg_acc


# ── Save / load helpers ───────────────────────────────────────────────────────

def _sector_slug(sector: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", sector.lower()).strip("_")


def _save_model(model, scaler, horizon: str, avg_acc: float | None = None) -> None:
    avail_feats = [c for c in FEATURE_COLS]   # record full list
    with open(HORIZON_MODEL_PATHS[horizon], "wb") as f:
        pickle.dump(model, f)
    with open(HORIZON_SCALER_PATHS[horizon], "wb") as f:
        pickle.dump(scaler, f)
    meta = {"feature_cols": avail_feats, "version": MODEL_VERSION}
    if avg_acc is not None:
        meta["accuracy"] = avg_acc
    with open(HORIZON_FEATURES_PATHS[horizon], "w") as f:
        json.dump(meta, f)


def _save_sector_model(model, scaler, sector: str, horizon: str, accuracy: float | None = None) -> None:
    slug = _sector_slug(sector)
    with open(SECTORS_DIR / f"model_{slug}_{horizon}.pkl", "wb") as f:
        pickle.dump(model, f)
    with open(SECTORS_DIR / f"scaler_{slug}_{horizon}.pkl", "wb") as f:
        pickle.dump(scaler, f)
    meta = {"feature_cols": FEATURE_COLS, "version": MODEL_VERSION, "sector": sector}
    if accuracy is not None:
        meta["accuracy"] = accuracy
    with open(SECTORS_DIR / f"features_{slug}_{horizon}.json", "w") as f:
        json.dump(meta, f)


def _save_regime_model(model, scaler, vol_regime: int, horizon: str, accuracy: float | None = None) -> None:
    key = VOL_REGIME_KEYS[vol_regime]
    with open(REGIMES_DIR / f"model_vol{key}_{horizon}.pkl", "wb") as f:
        pickle.dump(model, f)
    with open(REGIMES_DIR / f"scaler_vol{key}_{horizon}.pkl", "wb") as f:
        pickle.dump(scaler, f)
    meta = {"feature_cols": FEATURE_COLS, "version": MODEL_VERSION, "vol_regime": key}
    if accuracy is not None:
        meta["accuracy"] = accuracy
    with open(REGIMES_DIR / f"features_vol{key}_{horizon}.json", "w") as f:
        json.dump(meta, f)


def _load_regime_model(vol_regime: int, horizon: str) -> tuple:
    """Returns (model, scaler, feature_cols, accuracy) or (None, None, None, None)."""
    key = VOL_REGIME_KEYS.get(vol_regime, "normal")
    mp = REGIMES_DIR / f"model_vol{key}_{horizon}.pkl"
    sp = REGIMES_DIR / f"scaler_vol{key}_{horizon}.pkl"
    fp = REGIMES_DIR / f"features_vol{key}_{horizon}.json"
    if not mp.exists() or not sp.exists():
        return None, None, None, None
    with open(mp, "rb") as f:
        model = pickle.load(f)
    with open(sp, "rb") as f:
        scaler = pickle.load(f)
    feat_cols = FEATURE_COLS
    acc = None
    if fp.exists():
        with open(fp) as f:
            meta = json.load(f)
            feat_cols = meta.get("feature_cols", FEATURE_COLS)
            acc = meta.get("accuracy")
    return model, scaler, feat_cols, acc


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
    horizon_days = HORIZON_DAYS.get(horizon, 5)
    logger.info(f"Training global {horizon} model ({horizon_days}d target)...")
    combined = prepare_all_training_data(horizon_days)
    if combined.empty:
        logger.warning(f"No training data for {horizon}")
        return 0.0
    model, scaler, avg_acc = _walk_forward_train(combined)
    _save_model(model, scaler, horizon, avg_acc)
    _update_accuracy_log(horizon, avg_acc)
    logger.info(f"[{horizon}] Global model trained, acc={avg_acc:.4f}")
    return avg_acc


def train_regime_models(horizon: str = "1w") -> dict[str, float]:
    """Train one model per VIX regime. Requires ≥500 samples per regime."""
    horizon_days = HORIZON_DAYS.get(horizon, 5)
    combined = prepare_all_training_data(horizon_days)
    if combined.empty:
        return {}

    results = {}
    for vol_code in [0, 1, 2, 3]:
        key = VOL_REGIME_KEYS[vol_code]
        regime_data = combined[combined["vol_regime_code"] == float(vol_code)]
        if len(regime_data) < 500:
            logger.debug(f"Skipping vol_regime={key}: only {len(regime_data)} rows")
            continue
        model, scaler, avg_acc = _walk_forward_train(regime_data)
        _save_regime_model(model, scaler, vol_code, horizon, accuracy=avg_acc)
        results[key] = avg_acc
        logger.info(f"[{horizon}] Vol-regime={key}: acc={avg_acc:.4f} ({len(regime_data)} rows)")

    return results


def train_sector_models(horizon: str = "1w") -> dict[str, float]:
    horizon_days = HORIZON_DAYS.get(horizon, 5)
    combined = prepare_all_training_data(horizon_days)
    if combined.empty:
        return {}
    results = {}
    for sector in combined["sector"].unique():
        if sector in ("Unknown", ""):
            continue
        sector_data = combined[combined["sector"] == sector]
        n_tickers   = sector_data["ticker"].nunique()
        if n_tickers < 5 or len(sector_data) < 2000:
            continue
        model, scaler, avg_acc = _walk_forward_train(sector_data)
        _save_sector_model(model, scaler, sector, horizon, accuracy=avg_acc)
        results[sector] = avg_acc
        logger.info(f"[{horizon}] Sector {sector!r}: acc={avg_acc:.4f}")
    return results


def train_all_models() -> float:
    all_accs = []
    for horizon in HORIZON_DAYS:
        acc = train_model(horizon)
        all_accs.append(acc)
        regime_accs = train_regime_models(horizon)
        all_accs.extend(regime_accs.values())
        sector_accs = train_sector_models(horizon)
        all_accs.extend(sector_accs.values())
    avg = float(np.mean(all_accs)) if all_accs else 0.0
    logger.info(f"All models trained — overall avg acc: {avg:.4f}")
    return avg


def models_need_retrain() -> bool:
    for horizon in HORIZON_DAYS:
        if not HORIZON_MODEL_PATHS[horizon].exists():
            return True
        fp = HORIZON_FEATURES_PATHS[horizon]
        if not fp.exists():
            return True
        with open(fp) as f:
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
    if ACCURACY_LOG_PATH.exists():
        with open(ACCURACY_LOG_PATH) as f:
            history = json.load(f)
        h1w = history.get("1w", {})
        if h1w:
            latest_acc = list(h1w.values())[-1]
            if latest_acc < ACCURACY_THRESHOLD:
                logger.info(f"Accuracy {latest_acc:.4f} below threshold — retraining")
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
