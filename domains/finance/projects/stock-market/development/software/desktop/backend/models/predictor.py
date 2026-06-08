import pickle
import numpy as np
import json
import pandas as pd
from dataclasses import dataclass
from datetime import date
from backend.config import MODELS_DIR
from backend.models.trainer import (
    build_features,
    BASE_TECHNICAL_COLS, CROSS_COLS, FEATURE_COLS,
    HORIZON_MODEL_PATHS, HORIZON_SCALER_PATHS, HORIZON_FEATURES_PATHS,
    HORIZON_DAYS, SECTORS_DIR, _sector_slug, latest_accuracy,
)
from backend.database.duckdb_client import get_conn
import logging

logger = logging.getLogger(__name__)


@dataclass
class Prediction:
    ticker: str
    horizon: str
    direction: str
    probability: float
    expected_return_low: float
    expected_return_high: float
    volatility: float
    model_accuracy: float
    model_ready: bool
    sector: str = "Unknown"
    model_type: str = "global"


# ── Per-day inference cache ───────────────────────────────────────────────────
# Rebuilding cross-sectional features + macro context for every request is expensive.
# Cache everything keyed to the current calendar date.

_cache: dict = {"date": None, "cs": None, "macro": None, "fund": None}


def _refresh_cache() -> None:
    today = date.today()
    if _cache["date"] == today:
        return

    conn = get_conn()

    # Technical + cross-sectional features for all tickers
    df = conn.execute("""
        SELECT ticker, CAST(date AS VARCHAR) as date, open, high, low, close, volume
        FROM prices
        WHERE date >= CURRENT_DATE - INTERVAL 150 DAY
        ORDER BY ticker, date
    """).df()
    df["date"] = pd.to_datetime(df["date"])

    # Build latest technical row per ticker
    rows = []
    for ticker, group in df.groupby("ticker"):
        feat = build_features(group)
        if feat.empty:
            continue
        last = feat.iloc[-1]
        row = {col: float(last[col]) for col in BASE_TECHNICAL_COLS if col in feat.columns}
        row["ticker"] = ticker
        row["_vol_ref"] = float(last["volatility_20"])
        rows.append(row)

    cs = pd.DataFrame(rows) if rows else pd.DataFrame()

    # Cross-sectional percentile ranks (same universe used at training time)
    if not cs.empty:
        for col in CROSS_COLS:
            if col in cs.columns:
                cs[f"{col}_rank"] = cs[col].rank(pct=True)

    # Macro context (most recent values from DB)
    try:
        from backend.data.macro_feed import get_macro_context
        macro = get_macro_context()
    except Exception:
        macro = {k: 0.0 for k in ["vix", "vix_regime", "yield_curve", "yield_curve_inverted", "fed_rate"]}

    # Latest fundamentals per ticker (earnings_surprise, short_ratio)
    fund_snap = conn.execute("""
        SELECT DISTINCT ON (ticker) ticker, earnings_surprise, short_ratio
        FROM fundamentals
        ORDER BY ticker, report_date DESC
    """).df()
    fund_map = {
        r["ticker"]: {"earnings_surprise": float(r["earnings_surprise"] or 0.0),
                      "short_ratio": float(r["short_ratio"] or 0.0)}
        for _, r in fund_snap.iterrows()
    }

    # Sector map
    sectors = conn.execute("SELECT ticker, COALESCE(sector, 'Unknown') as sector FROM stocks").df()
    sector_map = dict(zip(sectors["ticker"], sectors["sector"]))

    _cache.update({"date": today, "cs": cs, "macro": macro, "fund": fund_map, "sectors": sector_map})


def _load_model(horizon: str) -> tuple:
    """Load global model for horizon. Returns (model, scaler, feature_cols) or (None, None, None)."""
    mp = HORIZON_MODEL_PATHS.get(horizon)
    sp = HORIZON_SCALER_PATHS.get(horizon)
    fp = HORIZON_FEATURES_PATHS.get(horizon)
    if not mp or not mp.exists() or not sp or not sp.exists():
        return None, None, None
    with open(mp, "rb") as f:
        model = pickle.load(f)
    with open(sp, "rb") as f:
        scaler = pickle.load(f)
    feature_cols = FEATURE_COLS
    if fp and fp.exists():
        with open(fp) as f:
            feature_cols = json.load(f).get("feature_cols", FEATURE_COLS)
    return model, scaler, feature_cols


def _load_sector_model(sector: str, horizon: str) -> tuple:
    """Load sector-specific model. Returns (model, scaler, feature_cols, accuracy) or (None, None, None, None)."""
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
    feature_cols = FEATURE_COLS
    sector_acc = None
    if fp.exists():
        with open(fp) as f:
            meta = json.load(f)
            feature_cols = meta.get("feature_cols", FEATURE_COLS)
            sector_acc = meta.get("accuracy")
    return model, scaler, feature_cols, sector_acc


def _build_feature_vector(ticker: str, feature_cols: list[str]) -> np.ndarray | None:
    """
    Assemble the full feature vector for a ticker using cached data.
    Handles both old (14-feature) and new (26-feature) feature sets gracefully.
    """
    _refresh_cache()
    cs = _cache.get("cs")
    macro = _cache.get("macro", {})
    fund = _cache.get("fund", {})

    if cs is None or cs.empty:
        return None

    row = cs[cs["ticker"] == ticker]
    if row.empty:
        return None

    # Collect all available values
    values: dict[str, float] = {}

    # Technical + cross-sectional
    for col in feature_cols:
        if col in row.columns:
            values[col] = float(row[col].iloc[0])

    # Macro
    for k, v in macro.items():
        values[k] = float(v)

    # Fundamentals
    fund_data = fund.get(ticker, {})
    values["earnings_surprise"] = float(fund_data.get("earnings_surprise", 0.0))
    values["short_ratio"]       = float(fund_data.get("short_ratio", 0.0))

    # Cross-sectional ranks for new columns (use 0.5 = median rank if not in cs)
    for col in CROSS_COLS:
        rank_col = f"{col}_rank"
        if rank_col not in values:
            if rank_col in row.columns:
                values[rank_col] = float(row[rank_col].iloc[0])
            else:
                values[rank_col] = 0.5

    # Build vector in exact feature_cols order; fill missing with 0
    vec = np.array([values.get(col, 0.0) for col in feature_cols], dtype=float)
    if np.any(np.isnan(vec)):
        vec = np.nan_to_num(vec, nan=0.0)

    return vec.reshape(1, -1)


def predict_ticker(ticker: str, horizon: str = "1w") -> Prediction:
    _refresh_cache()
    sector = _cache.get("sectors", {}).get(ticker, "Unknown")
    global_acc = latest_accuracy(horizon)

    # Prefer sector model (more specific), fall back to global
    model, scaler, feature_cols, sector_acc = _load_sector_model(sector, horizon)
    used_sector_model = model is not None
    if model is None:
        model, scaler, feature_cols = _load_model(horizon)

    acc = sector_acc if (used_sector_model and sector_acc is not None) else global_acc
    model_type = f"sector:{sector}" if used_sector_model else "global"

    if model is None:
        return Prediction(ticker, horizon, "unknown", 0.5, 0.0, 0.0, 0.0, global_acc, False, sector, "none")

    X = _build_feature_vector(ticker, feature_cols)
    if X is None:
        return Prediction(ticker, horizon, "unknown", 0.5, 0.0, 0.0, 0.0, global_acc, False, sector, "none")

    try:
        X_s = scaler.transform(X)
        prob_up = float(model.predict_proba(X_s)[0][1])
    except Exception as e:
        logger.warning(f"Prediction error for {ticker}/{horizon}: {e}")
        return Prediction(ticker, horizon, "unknown", 0.5, 0.0, 0.0, 0.0, global_acc, False, sector, "none")

    direction = "up" if prob_up >= 0.5 else "down"

    cs = _cache.get("cs")
    row = cs[cs["ticker"] == ticker] if cs is not None else pd.DataFrame()
    vol_ref = float(row["_vol_ref"].iloc[0]) if not row.empty and "_vol_ref" in row.columns else 0.02

    horizon_days = HORIZON_DAYS.get(horizon, 5)
    vol_horizon  = vol_ref * np.sqrt(horizon_days)
    expected     = (prob_up - 0.5) * 2 * vol_horizon

    if used_sector_model:
        logger.info(f"Using sector model for {ticker} ({sector}) [{horizon}]")

    return Prediction(
        ticker=ticker,
        horizon=horizon,
        direction=direction,
        probability=round(prob_up, 4),
        expected_return_low=round(float(expected - vol_horizon), 4),
        expected_return_high=round(float(expected + vol_horizon), 4),
        volatility=round(float(vol_ref * np.sqrt(252 / max(1, horizon_days))), 4),
        model_accuracy=round(acc, 4),
        model_ready=True,
        sector=sector,
        model_type=model_type,
    )
