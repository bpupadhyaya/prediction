"""
CFTC Commitments of Traders (COT) feed — Tier-1 positioning data.

Source: CFTC public reporting Socrata API (free, no key) — Traders in Financial
Futures (TFF) combined report. We track the E-MINI S&P 500 contract and derive
speculative (leveraged-money / hedge-fund) and institutional (asset-manager) net
positioning as a fraction of open interest. Released weekly (Friday, as of Tuesday).

These populate the previously zero-defaulted feature `cftc_speculative_positioning`
(plus institutional positioning) in the macro feature pipeline.

Stored into macro_indicators as series:
    CFTC_SP500_LEV_NET_PCT     leveraged-money (speculative) net / open interest  [-1, 1]
    CFTC_SP500_ASSET_MGR_NET_PCT  asset-manager (institutional) net / open interest [-1, 1]
    CFTC_SP500_OI              open interest (contracts)
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

import pandas as pd
import requests

from backend.data.macro_feed import upsert_macro

logger = logging.getLogger(__name__)

_COT_BASE = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"
_CONTRACT = "E-MINI S&P 500"


def _fetch_cot(days: int) -> pd.DataFrame:
    """Fetch COT history for the E-mini S&P 500 and derive net-positioning series."""
    start = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")
    params = {
        "$select": (
            "report_date_as_yyyy_mm_dd,open_interest_all,"
            "lev_money_positions_long,lev_money_positions_short,"
            "asset_mgr_positions_long,asset_mgr_positions_short"
        ),
        "$where": f"contract_market_name = '{_CONTRACT}' "
                  f"AND report_date_as_yyyy_mm_dd >= '{start}T00:00:00.000'",
        "$order": "report_date_as_yyyy_mm_dd ASC",
        "$limit": "1000",
    }
    try:
        resp = requests.get(_COT_BASE, params=params, timeout=25)
        resp.raise_for_status()
        rows = resp.json()
    except Exception as e:
        logger.warning(f"CFTC COT fetch failed: {e}")
        return pd.DataFrame()

    records = []
    for r in rows:
        try:
            oi = float(r.get("open_interest_all", 0) or 0)
            if oi <= 0:
                continue
            date = pd.to_datetime(r["report_date_as_yyyy_mm_dd"]).tz_localize(None)
            lev_net = float(r.get("lev_money_positions_long", 0) or 0) - \
                      float(r.get("lev_money_positions_short", 0) or 0)
            am_net = float(r.get("asset_mgr_positions_long", 0) or 0) - \
                     float(r.get("asset_mgr_positions_short", 0) or 0)
            records.append({
                "date": date,
                "CFTC_SP500_LEV_NET_PCT": lev_net / oi,
                "CFTC_SP500_ASSET_MGR_NET_PCT": am_net / oi,
                "CFTC_SP500_OI": oi,
            })
        except Exception:
            continue

    if not records:
        return pd.DataFrame()

    wide = pd.DataFrame(records)
    # Melt to the (series_id, date, value) long form macro_indicators expects.
    long = wide.melt(id_vars=["date"], var_name="series_id", value_name="value")
    return long[["series_id", "date", "value"]].dropna()


def load_cot(days: int = 365 * 5) -> int:
    """Fetch + upsert COT positioning series. Returns rows written."""
    df = _fetch_cot(days)
    if df.empty:
        logger.warning("CFTC COT: no data loaded")
        return 0
    upsert_macro(df)
    n_dates = df["date"].nunique()
    logger.info(f"CFTC COT: loaded {len(df)} rows across {n_dates} weekly reports")
    return len(df)
