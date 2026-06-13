"""
Build the bundled MOBILE model metadata: honest backtest accuracy, probability
calibration, and feature baselines — the single sidecar the iOS/Android/Pages
apps load alongside the 16-feature ONNX.

Why this exists
---------------
* The apps used to hard-code ``modelAccuracy = 0.54`` and showed the model's raw
  probability as "confidence". Neither was honest. This module measures the model
  out-of-sample (time-ordered, no leakage) and fits a calibration map so the
  displayed probability matches reality.
* It also exports per-feature **baseline means**. The apps use these as the
  neutral reference for on-device, perturbation-based explanations: replace one
  feature with its baseline, re-run the model, and the change in P(up) is that
  feature's local contribution to this prediction.

Everything here uses ONLY the 16 OHLCV-derived MOBILE_FEATURES (via
``trainer.build_features``) — no macro / fundamentals / network — so it is fast
and matches exactly what the apps can compute on-device.

Output: ``MODELS_DIR / mobile_model_meta.json`` plus copies into each app bundle.

Usage (stop the backend first — DuckDB is single-writer):
    python3 -m backend.models.mobile_meta
"""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from backend.config import DB_PATH, MODELS_DIR
from backend.models.exporter import MOBILE_FEATURES
from backend.models.trainer import build_features, HORIZON_DAYS

logger = logging.getLogger(__name__)

META_PATH = MODELS_DIR / "mobile_model_meta.json"

# App bundle locations that must carry a copy (mirrors the .onnx bundling).
_SOFTWARE = Path(__file__).resolve().parents[3]  # .../development/software
APP_BUNDLE_DIRS = [
    _SOFTWARE / "ios" / "StockPrediction" / "Resources",
    _SOFTWARE / "android" / "core" / "src" / "main" / "assets",
    _SOFTWARE / "pages" / "public",
]

# Time-ordered split fractions (no leakage: train is oldest, test is newest).
TRAIN_FRAC, CALIB_FRAC = 0.70, 0.15  # remainder (0.15) is the held-out test


def _build_pooled() -> pd.DataFrame:
    """Per-ticker features pooled into one frame with a `date` column (read-only DB)."""
    import duckdb

    con = duckdb.connect(str(DB_PATH), read_only=True)
    price_df = con.execute(
        "SELECT ticker, CAST(date AS VARCHAR) AS date, open, high, low, close, volume "
        "FROM prices ORDER BY ticker, date"
    ).df()
    con.close()
    price_df["date"] = pd.to_datetime(price_df["date"])

    frames = []
    for ticker, group in price_df.groupby("ticker"):
        feat = build_features(group)
        if len(feat) < 280:
            continue
        keep = feat[["date"] + MOBILE_FEATURES].copy()
        keep["close"] = feat["close"].values
        keep["ticker"] = ticker
        frames.append(keep)
    pooled = pd.concat(frames, ignore_index=True)
    return pooled


def _pipeline():
    """Identical estimator to exporter.export() so the metadata describes the shipped model."""
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    return Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", GradientBoostingClassifier(
            n_estimators=200, max_depth=3, learning_rate=0.05,
            max_features="sqrt", subsample=0.8, random_state=42,
        )),
    ])


def _fit_platt(prob_up: np.ndarray, y: np.ndarray):
    """Platt scaling: calibrated = sigmoid(w * p_up + b). Returns (w, b)."""
    from sklearn.linear_model import LogisticRegression

    lr = LogisticRegression(C=1e6, solver="lbfgs")
    lr.fit(prob_up.reshape(-1, 1), y)
    return float(lr.coef_[0][0]), float(lr.intercept_[0])


def _apply_platt(prob_up: np.ndarray, w: float, b: float) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-(w * prob_up + b)))


def _brier(prob: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((prob - y) ** 2))


def build_meta(verbose: bool = True) -> dict:
    pooled = _build_pooled()
    pooled = pooled.sort_values("date").reset_index(drop=True)
    if verbose:
        logger.info(
            "Pooled %s rows across %s tickers (%s → %s)",
            f"{len(pooled):,}", pooled["ticker"].nunique(),
            pooled["date"].min().date(), pooled["date"].max().date(),
        )

    # Feature baselines (neutral reference for on-device explanations).
    baselines = {f: float(pooled[f].mean()) for f in MOBILE_FEATURES}

    horizons = {}
    for hkey, hdays in HORIZON_DAYS.items():
        df = pooled.copy()
        # Forward return per ticker → directional target.
        df["future_return"] = df.groupby("ticker")["close"].pct_change(hdays).shift(-hdays)
        df = df.dropna(subset=MOBILE_FEATURES + ["future_return"])
        df["target"] = (df["future_return"] > 0).astype(int)
        df = df.sort_values("date").reset_index(drop=True)

        n = len(df)
        i_tr = int(n * TRAIN_FRAC)
        i_ca = int(n * (TRAIN_FRAC + CALIB_FRAC))
        X = df[MOBILE_FEATURES].to_numpy(dtype=np.float32)
        y = df["target"].to_numpy(dtype=int)

        Xtr, ytr = X[:i_tr], y[:i_tr]
        Xca, yca = X[i_tr:i_ca], y[i_tr:i_ca]
        Xte, yte = X[i_ca:], y[i_ca:]

        pipe = _pipeline()
        pipe.fit(Xtr, ytr)

        p_ca = pipe.predict_proba(Xca)[:, 1]
        p_te = pipe.predict_proba(Xte)[:, 1]

        w, b = _fit_platt(p_ca, yca)
        p_te_cal = _apply_platt(p_te, w, b)

        acc_raw = float(((p_te >= 0.5).astype(int) == yte).mean())
        base_rate = float(yte.mean())  # share of UP days in the test window
        brier_raw = _brier(p_te, yte)
        brier_cal = _brier(p_te_cal, yte)

        horizons[hkey] = {
            "backtest_accuracy": round(acc_raw, 4),
            "test_up_rate": round(base_rate, 4),
            "n_test": int(len(yte)),
            "calibration": {"w": round(w, 6), "b": round(b, 6)},
            "brier_raw": round(brier_raw, 5),
            "brier_calibrated": round(brier_cal, 5),
        }
        if verbose:
            logger.info(
                "[%s] OOS acc=%.4f (UP base=%.3f) | Brier %.4f→%.4f | "
                "calib w=%.3f b=%.3f | n_test=%d",
                hkey, acc_raw, base_rate, brier_raw, brier_cal, w, b, len(yte),
            )

    return {
        "features": MOBILE_FEATURES,
        "baselines": baselines,
        "horizons": horizons,
        "note": (
            "backtest_accuracy is out-of-sample directional accuracy on a "
            "time-ordered hold-out (no leakage). calibration maps the raw model "
            "probability p_up to an honest probability via sigmoid(w*p_up+b)."
        ),
    }


def write_meta() -> Path:
    meta = build_meta()
    META_PATH.parent.mkdir(parents=True, exist_ok=True)
    META_PATH.write_text(json.dumps(meta, indent=2))
    logger.info("Wrote %s", META_PATH)

    payload = json.dumps(meta, indent=2)
    for d in APP_BUNDLE_DIRS:
        if d.exists():
            (d / "mobile_model_meta.json").write_text(payload)
            logger.info("Bundled → %s", d / "mobile_model_meta.json")
        else:
            logger.warning("Bundle dir missing (skipped): %s", d)
    return META_PATH


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    write_meta()
