"""
Transparency & Explainability Engine — Layer 8 of the ADPS architecture.

Uses SHAP TreeExplainer to decompose each prediction into per-feature
contributions, then groups them by domain for user-friendly presentation.
SHAP is optional — falls back to model.feature_importances_ if unavailable.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ── Feature → domain mapping ──────────────────────────────────────────────────

FEATURE_DOMAINS: dict[str, str] = {
    # Momentum / technical
    "return_1d":          "momentum",
    "return_5d":          "momentum",
    "return_20d":         "momentum",
    "return_60d":         "momentum",
    "return_252d":        "momentum",
    "ma_5":               "momentum",
    "ma_20":              "momentum",
    "ma_50":              "momentum",
    "rsi":                "momentum",
    "high_52w_ratio":     "momentum",
    "amihud_illiquidity": "momentum",
    "volume_ratio":       "momentum",
    "rsi_rank":           "momentum",
    "return_5d_rank":     "momentum",
    "return_20d_rank":    "momentum",
    "volatility_20_rank": "momentum",
    "volume_ratio_rank":  "momentum",
    # Volatility
    "volatility_20":      "volatility",
    "vix":                "volatility",
    "vix_regime":         "volatility",
    "vvix":               "volatility",
    # Macro / monetary
    "yield_curve":        "macro",
    "yield_curve_inverted": "macro",
    "fed_rate":           "macro",
    "hy_spread":          "macro",
    "ig_spread":          "macro",
    "tips_real_yield":    "macro",
    "m2_growth_yoy":      "macro",
    "initial_claims":     "macro",
    "nfci":               "macro",
    "pce_core_yoy":       "macro",
    "fed_balance_sheet":  "macro",
    # Fundamental
    "earnings_surprise":  "fundamental",
    "short_ratio":        "fundamental",
    "short_ratio_rank":   "fundamental",
    # Cross-asset
    "dxy":                "cross_asset",
    "dxy_ret20":          "cross_asset",
    "gold_equity_ratio":  "cross_asset",
    "copper_ret20":       "cross_asset",
    "usdjpy_ret5":        "cross_asset",
    "oil_ret20":          "cross_asset",
    "btc_spx_corr":       "cross_asset",
    # Regime (computed)
    "monetary_regime":    "macro",
    "credit_regime":      "macro",
    "vol_regime_code":    "volatility",
    "yc_regime_code":     "macro",
}

DOMAIN_LABELS = {
    "momentum":    "Momentum & Technical",
    "volatility":  "Volatility",
    "macro":       "Macro & Monetary",
    "fundamental": "Fundamental",
    "cross_asset": "Cross-Asset",
    "sentiment":   "Sentiment",
}

DOMAIN_ORDER = ["macro", "momentum", "volatility", "fundamental", "cross_asset", "sentiment"]

_SHAP_AVAILABLE: Optional[bool] = None


def _shap_available() -> bool:
    global _SHAP_AVAILABLE
    if _SHAP_AVAILABLE is None:
        try:
            import shap  # noqa: F401
            _SHAP_AVAILABLE = True
        except ImportError:
            _SHAP_AVAILABLE = False
            logger.info("shap not installed — using feature_importances_ for explanations")
    return _SHAP_AVAILABLE


def explain(
    model,
    scaler,
    X_scaled: np.ndarray,
    feature_cols: list[str],
    feature_values_raw: dict[str, float],
    prob_up: float,
) -> dict:
    """
    Generate a full prediction explanation.

    Returns:
        {
          "base_probability": float,
          "domains": {
            "macro": {
              "label": "Macro & Monetary",
              "total_contribution": float,   # sum of |SHAP| for domain
              "direction": "positive"|"negative"|"neutral",
              "top_factors": [
                {"name": str, "value": float, "contribution": float,
                 "direction": "up"|"down", "explanation": str}
              ]
            }, ...
          },
          "method": "shap" | "importance"
        }
    """
    shap_values = _compute_shap(model, scaler, X_scaled, feature_cols, prob_up)

    # Build per-feature dict
    factor_contribs: dict[str, float] = {}
    for i, col in enumerate(feature_cols):
        if i < len(shap_values):
            factor_contribs[col] = float(shap_values[i])

    # Group by domain
    domain_data: dict[str, dict] = {}
    for domain in DOMAIN_ORDER:
        cols_in_domain = [c for c in feature_cols if FEATURE_DOMAINS.get(c) == domain]
        if not cols_in_domain:
            continue
        contribs = {c: factor_contribs.get(c, 0.0) for c in cols_in_domain}
        total = sum(abs(v) for v in contribs.values())
        net   = sum(contribs.values())

        # Top 5 factors by absolute contribution
        top = sorted(contribs.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
        top_factors = []
        for name, contrib in top:
            if abs(contrib) < 1e-6:
                continue
            raw_val = feature_values_raw.get(name, 0.0)
            top_factors.append({
                "name":         name,
                "value":        round(raw_val, 6),
                "contribution": round(contrib, 6),
                "direction":    "up" if contrib > 0 else "down",
                "explanation":  _explain_factor(name, raw_val, contrib),
            })

        direction = "positive" if net > 0.01 else ("negative" if net < -0.01 else "neutral")
        domain_data[domain] = {
            "label":              DOMAIN_LABELS.get(domain, domain),
            "total_contribution": round(total, 4),
            "net_contribution":   round(net, 4),
            "direction":          direction,
            "top_factors":        top_factors,
        }

    method = "shap" if _shap_available() else "importance"
    return {
        "base_probability": round(prob_up, 4),
        "domains":          domain_data,
        "method":           method,
    }


def _compute_shap(model, scaler, X_scaled: np.ndarray, feature_cols: list[str], prob_up: float) -> list[float]:
    """Return SHAP values (or importance-proxy) as a list aligned to feature_cols."""
    n = len(feature_cols)

    if _shap_available():
        try:
            import shap
            explainer  = shap.TreeExplainer(model)
            shap_vals  = explainer.shap_values(X_scaled)
            # shap_values for binary classification: shape (2, 1, n_features)
            # We want values for class=1 (UP)
            if isinstance(shap_vals, list) and len(shap_vals) == 2:
                vals = shap_vals[1][0]   # class=1, first sample
            elif hasattr(shap_vals, "ndim") and shap_vals.ndim == 2:
                vals = shap_vals[0]
            else:
                vals = np.array(shap_vals).flatten()
            return list(vals[:n])
        except Exception as e:
            logger.debug(f"SHAP computation failed: {e} — falling back to importance")

    # Fallback: use feature_importances_ as proxy, sign from (prob_up - 0.5)
    try:
        importances = model.feature_importances_[:n]
        sign = 1.0 if prob_up >= 0.5 else -1.0
        return list(importances * sign * (prob_up - 0.5) * 2)
    except Exception:
        return [0.0] * n


def _explain_factor(name: str, value: float, contribution: float) -> str:
    """Generate a short plain-English explanation for a factor contribution."""
    direction = "bullish" if contribution > 0 else "bearish"
    explanations = {
        "yield_curve":        f"Yield curve at {value:.2f}% — {'normal/positive slope' if value > 0.5 else ('flat' if value > 0 else 'inverted (recession signal)')} → {direction}",
        "hy_spread":          f"HY credit spread {value:.0f}bp — {'tight (risk appetite high)' if value < 350 else ('stressed' if value < 600 else 'crisis-level')} → {direction}",
        "ig_spread":          f"IG credit spread {value:.0f}bp — {'low (good credit conditions)' if value < 100 else 'elevated'} → {direction}",
        "tips_real_yield":    f"Real 10Y yield {value:.2f}% — {'negative (good for growth)' if value < 0 else 'positive (headwind for equities)'} → {direction}",
        "vix":                f"VIX at {value:.1f} — {'low fear' if value < 15 else ('normal' if value < 25 else 'elevated fear')} → {direction}",
        "vvix":               f"VVIX (vol-of-vol) at {value:.1f} — {'calm' if value < 90 else 'volatile vol regime'} → {direction}",
        "rsi":                f"RSI at {value:.0f} — {'oversold (potential bounce)' if value < 35 else ('overbought' if value > 65 else 'neutral')} → {direction}",
        "return_252d":        f"12-month momentum {value*100:.1f}% — {'strong uptrend' if value > 0.15 else ('strong downtrend' if value < -0.15 else 'moderate')} → {direction}",
        "return_60d":         f"3-month momentum {value*100:.1f}% → {direction}",
        "return_5d":          f"5-day return {value*100:.1f}% → {direction}",
        "high_52w_ratio":     f"Price at {value*100:.0f}% of 52-week high → {direction}",
        "amihud_illiquidity": f"Illiquidity ratio {value:.2e} — {'liquid' if value < 0.01 else 'illiquid'} → {direction}",
        "volume_ratio":       f"Volume {value:.1f}× 20-day avg — {'high activity' if value > 1.5 else 'low activity'} → {direction}",
        "m2_growth_yoy":      f"M2 growth {value:.1f}% YoY — {'expansionary' if value > 5 else ('tight' if value < 2 else 'moderate')} → {direction}",
        "initial_claims":     f"Jobless claims {value:,.0f} — {'low (strong labor)' if value < 220000 else 'elevated (labor weakening)'} → {direction}",
        "nfci":               f"NFCI financial conditions {value:.3f} — {'loose (risk-on)' if value < 0 else 'tight (risk-off)'} → {direction}",
        "pce_core_yoy":       f"PCE Core inflation {value:.1f}% — {'above target' if value > 2.5 else 'near target'} → {direction}",
        "earnings_surprise":  f"Earnings surprise {value*100:.1f}% → {direction}",
        "short_ratio":        f"Short interest days-to-cover {value:.1f} — {'high short interest' if value > 5 else 'low short interest'} → {direction}",
        "gold_equity_ratio":  f"Gold/equity ratio {value:.2f} — {'risk-off positioning' if value > 6 else 'risk-on'} → {direction}",
        "copper_ret20":       f"Copper 20d momentum {value*100:.1f}% — {'global growth signal' if value > 0 else 'growth concern'} → {direction}",
        "usdjpy_ret5":        f"USDJPY 5d change {value*100:.2f}% — {'yen weakening (carry on)' if value > 0 else 'yen strengthening (carry unwind risk)'} → {direction}",
        "oil_ret20":          f"Oil 20d momentum {value*100:.1f}% → {direction}",
        "btc_spx_corr":       f"BTC/SPX 30d correlation {value:.2f} — {'risk-on correlation' if value > 0.5 else 'decorrelated'} → {direction}",
        "dxy_ret20":          f"Dollar 20d momentum {value*100:.1f}% — {'dollar strength (headwind for intl)' if value > 0 else 'dollar weakness'} → {direction}",
        "fed_balance_sheet":  f"Fed balance sheet ${value/1e6:.1f}T → {direction}",
    }
    return explanations.get(name, f"{name} = {value:.4f} → {direction}")
