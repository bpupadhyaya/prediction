"""
Regime Context Engine — Layer 2 of the ADPS architecture.

Classifies current market regime across 4 dimensions:
  1. Monetary  : CUTTING(0) | PAUSING(1) | HIKING(2)
  2. Credit    : EXPANSION(0) | STRESS(1) | CRISIS(2)
  3. Volatility: LOW(0) | NORMAL(1) | ELEVATED(2) | CRISIS(3)
  4. Yield curve: NORMAL(0) | FLAT(1) | INVERTED(2) | RE-STEEPENING(3)

Each dimension is stored in the regime_history table and cached in memory.
"""

from __future__ import annotations

import logging
import json
from dataclasses import dataclass, asdict
from datetime import date, datetime
from typing import Optional

import numpy as np
import pandas as pd

from backend.database.duckdb_client import get_conn

logger = logging.getLogger(__name__)

# ── Thresholds ────────────────────────────────────────────────────────────────

# Monetary regime: based on 6-month change in short-term rate (FEDFUNDS / DGS3M)
_MONETARY_HIKE_THRESHOLD  = 0.25   # +25bp over 6m → HIKING
_MONETARY_CUT_THRESHOLD   = -0.25  # −25bp over 6m → CUTTING

# Credit regime: based on HY OAS spread in basis points
_CREDIT_STRESS_BP   = 350   # Above → STRESS
_CREDIT_CRISIS_BP   = 600   # Above → CRISIS

# Volatility regime: VIX level
_VOL_LOW       = 15
_VOL_NORMAL    = 25
_VOL_ELEVATED  = 35

# Yield curve regime: T10Y2Y spread in percentage points
_YC_FLAT_THRESHOLD         = 0.50   # Below → FLAT
_YC_RESTEEPEN_IMPROVEMENT  = 0.30   # 3m improvement above this → RE-STEEPENING


@dataclass
class Regime:
    monetary:    int   # 0=CUTTING, 1=PAUSING, 2=HIKING
    credit:      int   # 0=EXPANSION, 1=STRESS, 2=CRISIS
    volatility:  int   # 0=LOW, 1=NORMAL, 2=ELEVATED, 3=CRISIS
    yield_curve: int   # 0=NORMAL, 1=FLAT, 2=INVERTED, 3=RE-STEEPENING
    as_of:       date  = None

    def label(self) -> str:
        mon = ["CUTTING", "PAUSING", "HIKING"][self.monetary]
        crd = ["EXPANSION", "STRESS", "CRISIS"][self.credit]
        vol = ["LOW", "NORMAL", "ELEVATED", "CRISIS"][self.volatility]
        yc  = ["NORMAL", "FLAT", "INVERTED", "RE-STEEPENING"][self.yield_curve]
        return f"MON={mon} | CREDIT={crd} | VOL={vol} | YC={yc}"

    def to_dict(self) -> dict:
        return {
            "monetary": self.monetary,
            "monetary_label": ["CUTTING", "PAUSING", "HIKING"][self.monetary],
            "credit": self.credit,
            "credit_label": ["EXPANSION", "STRESS", "CRISIS"][self.credit],
            "volatility": self.volatility,
            "volatility_label": ["LOW", "NORMAL", "ELEVATED", "CRISIS"][self.volatility],
            "yield_curve": self.yield_curve,
            "yield_curve_label": ["NORMAL", "FLAT", "INVERTED", "RE-STEEPENING"][self.yield_curve],
            "as_of": str(self.as_of) if self.as_of else None,
        }

    @property
    def vol_regime_key(self) -> str:
        return ["low", "normal", "elevated", "crisis"][self.volatility]

    @property
    def monetary_regime_key(self) -> str:
        return ["cutting", "pausing", "hiking"][self.monetary]


_DEFAULT_REGIME = Regime(monetary=1, credit=0, volatility=1, yield_curve=0)
_regime_cache: dict = {"date": None, "regime": None}


# ── Classification logic ──────────────────────────────────────────────────────

def _latest_series(conn, series_id: str, lookback_days: int = 1) -> Optional[float]:
    row = conn.execute("""
        SELECT value FROM macro_indicators
        WHERE series_id = ? AND value IS NOT NULL
        ORDER BY date DESC LIMIT 1
    """, [series_id]).fetchone()
    return float(row[0]) if row else None


def _series_n_months_ago(conn, series_id: str, months: int = 6) -> Optional[float]:
    row = conn.execute("""
        SELECT value FROM macro_indicators
        WHERE series_id = ?
          AND date <= (CURRENT_DATE - INTERVAL (? * 30) DAY)
          AND value IS NOT NULL
        ORDER BY date DESC LIMIT 1
    """, [series_id, months]).fetchone()
    return float(row[0]) if row else None


def _classify_monetary(conn) -> int:
    now  = _latest_series(conn, "FEDFUNDS")
    past = _series_n_months_ago(conn, "FEDFUNDS", months=6)
    if now is None or past is None:
        return 1  # default: PAUSING
    delta = now - past
    if delta >= _MONETARY_HIKE_THRESHOLD:
        return 2  # HIKING
    if delta <= _MONETARY_CUT_THRESHOLD:
        return 0  # CUTTING
    return 1  # PAUSING


def _classify_credit(conn) -> int:
    hy = _latest_series(conn, "BAMLH0A0HYM2")
    if hy is None:
        return 0  # default: EXPANSION
    if hy >= _CREDIT_CRISIS_BP:
        return 2  # CRISIS
    if hy >= _CREDIT_STRESS_BP:
        return 1  # STRESS
    return 0  # EXPANSION


def _classify_volatility(conn) -> int:
    vix = _latest_series(conn, "VIXCLS")
    if vix is None:
        return 1  # default: NORMAL
    if vix >= _VOL_ELEVATED:
        return 3  # CRISIS
    if vix >= _VOL_NORMAL:
        return 2  # ELEVATED
    if vix >= _VOL_LOW:
        return 1  # NORMAL
    return 0  # LOW


def _classify_yield_curve(conn) -> int:
    now  = _latest_series(conn, "T10Y2Y")
    past = _series_n_months_ago(conn, "T10Y2Y", months=3)
    if now is None:
        return 0  # default: NORMAL

    if now < 0:
        # Check for re-steepening: was it more inverted 3 months ago?
        if past is not None and (now - past) >= _YC_RESTEEPEN_IMPROVEMENT:
            return 3  # RE-STEEPENING (still inverted but improving)
        return 2  # INVERTED

    if now < _YC_FLAT_THRESHOLD:
        return 1  # FLAT
    return 0  # NORMAL


# ── Public API ────────────────────────────────────────────────────────────────

def classify_current() -> Regime:
    """Classify the current regime from the latest macro data in DB. Cached daily."""
    global _regime_cache
    today = date.today()
    if _regime_cache["date"] == today and _regime_cache["regime"] is not None:
        return _regime_cache["regime"]

    try:
        conn = get_conn()
        regime = Regime(
            monetary=_classify_monetary(conn),
            credit=_classify_credit(conn),
            volatility=_classify_volatility(conn),
            yield_curve=_classify_yield_curve(conn),
            as_of=today,
        )
        _regime_cache = {"date": today, "regime": regime}
        _persist_regime(conn, regime)
        logger.info(f"Regime classified: {regime.label()}")
        return regime
    except Exception as e:
        logger.warning(f"Regime classification failed: {e} — using defaults")
        return _DEFAULT_REGIME


def classify_for_date(macro_row: dict) -> Regime:
    """
    Classify regime for a historical data point during training.
    macro_row must contain: vix, yield_curve, fed_rate, hy_spread (optional)
    """
    vix  = float(macro_row.get("vix", 20))
    yc   = float(macro_row.get("yield_curve", 0.5))
    fed  = float(macro_row.get("fed_rate", 3.0))
    hy   = float(macro_row.get("hy_spread", 300))

    # Monetary: approximate from fed rate level (can't compute 6m change in row context)
    # Use level as proxy: >4% = likely hiking/high, <2% = likely cutting/low
    if fed > 4.0:
        monetary = 2
    elif fed < 2.0:
        monetary = 0
    else:
        monetary = 1

    credit = 2 if hy >= _CREDIT_CRISIS_BP else (1 if hy >= _CREDIT_STRESS_BP else 0)

    if vix >= _VOL_ELEVATED:
        volatility = 3
    elif vix >= _VOL_NORMAL:
        volatility = 2
    elif vix >= _VOL_LOW:
        volatility = 1
    else:
        volatility = 0

    if yc < 0:
        yield_curve = 2
    elif yc < _YC_FLAT_THRESHOLD:
        yield_curve = 1
    else:
        yield_curve = 0

    return Regime(monetary=monetary, credit=credit, volatility=volatility, yield_curve=yield_curve)


def _persist_regime(conn, regime: Regime) -> None:
    try:
        conn.execute("""
            INSERT OR REPLACE INTO regime_history
            (as_of_date, monetary, credit, volatility, yield_curve, label, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            regime.as_of, regime.monetary, regime.credit,
            regime.volatility, regime.yield_curve,
            regime.label(), datetime.now(),
        ])
        conn.commit()
    except Exception as e:
        logger.debug(f"Could not persist regime: {e}")


def get_historical_regimes(days: int = 365 * 5) -> pd.DataFrame:
    """Load historical regime classifications for training augmentation."""
    conn = get_conn()
    return conn.execute("""
        SELECT as_of_date as date, monetary, credit, volatility, yield_curve
        FROM regime_history
        WHERE as_of_date >= (CURRENT_DATE - INTERVAL ? DAY)
        ORDER BY date
    """, [days]).df()
