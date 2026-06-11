"""
Extract structured market signals from video transcripts using the local LLM.
Maps transcript content to our 656 parameter names and guidance signal format.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Key domains and parameter examples for LLM context
DOMAIN_EXAMPLES = {
    "macro":        "interest rates, inflation, GDP, Fed policy, yield curve, employment",
    "technical":    "price momentum, moving averages, RSI, volume patterns, support/resistance",
    "fundamental":  "earnings, revenue growth, margins, P/E ratio, balance sheet strength",
    "cross_asset":  "dollar strength, commodity prices, bond yields, sector rotation, crypto",
    "sentiment":    "market sentiment, fear/greed, put/call ratios, institutional flows, short interest",
    "geopolitical": "trade policy, regulatory risk, international tensions, political uncertainty",
}

_SYSTEM_PROMPT_TEMPLATE = """You are a financial analyst extracting market intelligence signals from video transcripts.

Video: "{title}" by {channel}

Your task: analyze the transcript and extract specific, actionable market signals.
For each signal, identify:
1. Which stock ticker(s) are affected (use standard NYSE/NASDAQ symbols, or "MARKET" for broad market)
2. Which financial domain it belongs to: macro, technical, fundamental, cross_asset, sentiment, geopolitical
3. Direction: UP (bullish) or DOWN (bearish) for the ticker
4. Weight: importance 1-100 (100 = critically important)
5. Confidence: 0.0-1.0
6. Key quote: exact text from transcript supporting this signal
7. Parameter name: most relevant parameter from this list per domain:
   - macro: fed_rate, yield_curve, inflation_rate, unemployment_rate, gdp_growth, pmi, credit_spread
   - technical: price_momentum, rsi, volume_trend, moving_average_trend, volatility_regime
   - fundamental: revenue_growth_1y, pe_ratio_forward, eps_growth_1y, profit_margins, debt_equity_ratio
   - cross_asset: dxy_index, gold_price, oil_price, vix, sector_rotation
   - sentiment: market_sentiment, institutional_flow_change, short_interest_pct_float, analyst_consensus_buy_pct
   - geopolitical: regulatory_risk_score, trade_policy_uncertainty, epu_index

Respond ONLY with a JSON array. No other text. Example:
[
  {{"ticker": "TSLA", "domain": "fundamental", "parameter_name": "revenue_growth_1y", "direction": "UP", "weight": 80, "confidence": 0.85, "key_quote": "exact quote here"}},
  {{"ticker": "MARKET", "domain": "macro", "parameter_name": "fed_rate", "direction": "DOWN", "weight": 70, "confidence": 0.75, "key_quote": "exact quote here"}}
]

If no clear signals found, return [].
"""


def extract_signals_from_transcript(
    transcript: str,
    title: str = "",
    channel: str = "",
    llm_fn=None,
) -> list[dict]:
    """
    Use the local LLM to extract structured signals from a video transcript.

    Returns list of dicts with: ticker, parameter_name, domain, direction, weight,
    confidence, key_quote, quote_ts_sec, extracted_signal.
    """
    if not transcript or len(transcript.strip()) < 100:
        return []

    # Truncate transcript to fit LLM context (keep first 12 000 chars)
    transcript_excerpt = transcript[:12000]

    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        title=title or "Unknown video",
        channel=channel or "Unknown channel",
    )
    user_msg = f"Extract market signals from this transcript:\n\n{transcript_excerpt}"

    response_text = ""
    try:
        if llm_fn:
            def _collect(token: str) -> None:
                nonlocal response_text
                response_text += token
            llm_fn(system_prompt, user_msg, _collect)
        else:
            # Attempt to call the project's local llama-cpp inference helper
            from backend.models.llm_predictor import _run_llm_inference
            response_text = _run_llm_inference(system_prompt, user_msg)
    except Exception as e:
        logger.warning("LLM call for signal extraction failed: %s", e)
        return []

    # Parse JSON array out of whatever the model returned
    json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
    if not json_match:
        logger.warning("No JSON array found in LLM response for signal extraction")
        return []

    try:
        signals = json.loads(json_match.group())
    except json.JSONDecodeError as e:
        logger.warning("JSON parse error in signal extraction: %s", e)
        return []

    validated: list[dict] = []
    for s in signals:
        if not isinstance(s, dict):
            continue

        ticker = str(s.get("ticker", "MARKET")).upper().strip()
        domain = str(s.get("domain", "macro")).lower().strip()
        direction = str(s.get("direction", "UP")).upper().strip()

        if direction not in ("UP", "DOWN"):
            direction = "UP"
        if domain not in DOMAIN_EXAMPLES:
            domain = "macro"

        weight = max(1, min(100, int(s.get("weight", 50))))
        confidence = max(0.1, min(1.0, float(s.get("confidence", 0.7))))

        validated.append({
            "ticker":           ticker if ticker != "MARKET" else None,
            "parameter_name":   str(s.get("parameter_name", "market_sentiment")),
            "domain":           domain,
            "direction":        direction.lower(),
            "weight":           weight,
            "confidence":       confidence,
            "key_quote":        str(s.get("key_quote", ""))[:500],
            "quote_ts_sec":     0,  # approximate — no timestamp correlation yet
            "extracted_signal": 1.0 if direction == "UP" else -1.0,
        })

    return validated


def aggregate_signals_for_ticker(
    ticker: str,
    time_range_days: int,
    min_confidence: float = 0.6,
) -> dict:
    """
    Aggregate all video signals for a ticker over a time window.
    Returns {ticker, signal_count, direction, strength, top_signals}.
    """
    from backend.database.duckdb_client import get_conn

    conn = get_conn()
    cutoff = (datetime.now() - timedelta(days=time_range_days)).isoformat()

    rows = conn.execute(
        """
        SELECT vs.direction, vs.weight, vs.confidence, vs.key_quote,
               vs.parameter_name, vs.domain, src.title, src.channel_name,
               src.published_at, src.speaker_name
        FROM video_signals vs
        JOIN video_sources src ON vs.video_id = src.id
        WHERE (vs.ticker = ? OR vs.ticker IS NULL)
          AND src.published_at >= ?
          AND vs.confidence >= ?
        ORDER BY src.published_at DESC
        """,
        [ticker, cutoff, min_confidence],
    ).fetchall()

    if not rows:
        return {"ticker": ticker, "signal_count": 0, "signals": []}

    up_weight   = sum(r[1] * r[2] for r in rows if r[0] == "up")
    down_weight = sum(r[1] * r[2] for r in rows if r[0] == "down")
    total       = up_weight + down_weight
    avg_dir     = "up" if up_weight >= down_weight else "down"
    strength    = abs(up_weight - down_weight) / total if total > 0 else 0.0

    return {
        "ticker":       ticker,
        "signal_count": len(rows),
        "direction":    avg_dir,
        "strength":     round(strength, 3),
        "top_signals": [
            {
                "direction":    r[0],
                "weight":       r[1],
                "confidence":   r[2],
                "key_quote":    r[3],
                "parameter_name": r[4],
                "domain":       r[5],
                "video_title":  r[6],
                "channel":      r[7],
                "published_at": str(r[8]),
                "speaker":      r[9],
            }
            for r in rows[:10]
        ],
    }
