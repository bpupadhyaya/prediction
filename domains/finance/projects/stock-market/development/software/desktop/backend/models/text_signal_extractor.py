"""
LLM text pipeline — Layer 6 (text sources).

Extract structured market signals from financial TEXT — FOMC statements,
earnings-call transcripts, and arbitrary user-pasted text/URLs — into the same
658-parameter guidance-signal format used by the YouTube (YVIS) pipeline.

Design:
  • If a local LLM is active, use it for structured extraction (best quality).
  • If no model is installed, fall back to a transparent keyword lexicon so the
    feature still produces a coarse MARKET signal (graceful no-model degradation).

Signals are returned in the standard dict shape (ticker, parameter_name, domain,
direction, weight, confidence, key_quote, extracted_signal) and can be applied to
the prediction engine via user_signals — identical to video signals.
"""
from __future__ import annotations

import json
import logging
import re

logger = logging.getLogger(__name__)

_DOMAINS = {"macro", "technical", "fundamental", "cross_asset", "sentiment", "geopolitical"}

_SOURCE_PROMPTS = {
    "fomc": (
        "You are a Fed-watcher extracting monetary-policy signals from an FOMC "
        "statement or minutes. Hawkish language (rate hikes, tightening, "
        "persistent inflation) is bearish for equities; dovish language (cuts, "
        "easing, soft landing) is bullish. Most signals are domain 'macro', "
        "ticker 'MARKET'."
    ),
    "earnings": (
        "You are an equity analyst extracting signals from an earnings call. Focus "
        "on revenue growth, margins, guidance, and demand commentary. Beats and "
        "raised guidance are bullish; misses and cut guidance are bearish. Use the "
        "company's ticker; domain is usually 'fundamental'."
    ),
    "generic": (
        "You are a financial analyst extracting market signals from the text below."
    ),
}

_SCHEMA_INSTRUCTION = """
Extract specific, actionable market signals. Respond ONLY with a JSON array, no other text:
[
  {"ticker": "TSLA" or "MARKET", "domain": "macro|technical|fundamental|cross_asset|sentiment|geopolitical",
   "parameter_name": "fed_rate|revenue_growth_1y|market_sentiment|...", "direction": "UP" or "DOWN",
   "weight": 1-100, "confidence": 0.0-1.0, "key_quote": "exact supporting quote"}
]
If no clear signals, return [].
"""

# ── Heuristic lexicons (no-model fallback) ───────────────────────────────────
_HAWKISH = ["rate hike", "raise rates", "tightening", "restrictive", "elevated inflation",
            "persistent inflation", "higher for longer", "combat inflation", "hawkish"]
_DOVISH = ["rate cut", "lower rates", "easing", "accommodative", "soft landing",
           "cooling inflation", "disinflation", "pause", "dovish", "stimulus"]
_BULLISH = ["beat expectations", "raised guidance", "record revenue", "strong demand",
            "margin expansion", "outperform", "upgrade", "accelerating growth", "bullish"]
_BEARISH = ["missed expectations", "cut guidance", "weak demand", "margin compression",
            "downgrade", "slowing growth", "layoffs", "headwinds", "bearish", "recession"]


def _count(text: str, terms: list[str]) -> int:
    t = text.lower()
    return sum(t.count(term) for term in terms)


def _heuristic_signals(text: str, source_type: str) -> list[dict]:
    """Transparent keyword-lexicon fallback when no LLM is available."""
    if source_type == "fomc":
        pos, neg, param, domain = _DOVISH, _HAWKISH, "fed_rate", "macro"
    else:
        pos, neg, param, domain = _BULLISH, _BEARISH, "market_sentiment", "sentiment"

    p, n = _count(text, pos), _count(text, neg)
    if p == 0 and n == 0:
        return []
    direction = "up" if p >= n else "down"
    strength = abs(p - n)
    weight = max(20, min(70, 25 + 8 * strength))           # modest weight — it's a heuristic
    confidence = max(0.3, min(0.6, 0.3 + 0.05 * strength))  # capped low confidence
    return [{
        "ticker": None,
        "parameter_name": param,
        "domain": domain,
        "direction": direction,
        "weight": int(weight),
        "confidence": round(confidence, 2),
        "key_quote": f"[heuristic] {p} positive vs {n} negative keyword matches",
        "quote_ts_sec": 0,
        "extracted_signal": 1.0 if direction == "up" else -1.0,
        "method": "heuristic",
    }]


def _validate(signals) -> list[dict]:
    out: list[dict] = []
    if not isinstance(signals, list):
        return out
    for s in signals:
        if not isinstance(s, dict):
            continue
        ticker = str(s.get("ticker", "MARKET")).upper().strip()
        domain = str(s.get("domain", "macro")).lower().strip()
        direction = str(s.get("direction", "UP")).upper().strip()
        if direction not in ("UP", "DOWN"):
            direction = "UP"
        if domain not in _DOMAINS:
            domain = "macro"
        out.append({
            "ticker": ticker if ticker not in ("MARKET", "") else None,
            "parameter_name": str(s.get("parameter_name", "market_sentiment")),
            "domain": domain,
            "direction": direction.lower(),
            "weight": max(1, min(100, int(s.get("weight", 50)))),
            "confidence": max(0.1, min(1.0, float(s.get("confidence", 0.7)))),
            "key_quote": str(s.get("key_quote", ""))[:500],
            "quote_ts_sec": 0,
            "extracted_signal": 1.0 if direction == "UP" else -1.0,
            "method": "llm",
        })
    return out


def extract_signals_from_text(
    text: str,
    source_type: str = "generic",
    title: str = "",
    llm_fn=None,
) -> dict:
    """
    Extract signals from financial text.

    Returns {"signals": [...], "method": "llm"|"heuristic"|"none", "source_type": ...}.
    Never raises — degrades to the keyword heuristic when no LLM is available.
    """
    source_type = source_type if source_type in _SOURCE_PROMPTS else "generic"
    if not text or len(text.strip()) < 80:
        return {"signals": [], "method": "none", "source_type": source_type}

    excerpt = text[:12000]
    system_prompt = _SOURCE_PROMPTS[source_type] + "\n" + _SCHEMA_INSTRUCTION
    user_msg = f'Source: "{title or source_type}"\n\nText:\n{excerpt}'

    response_text = ""
    try:
        if llm_fn is not None:
            buf: list[str] = []
            llm_fn(system_prompt, user_msg, buf.append)
            response_text = "".join(buf)
        else:
            from backend.models.llm_predictor import _run_llm_inference
            response_text = _run_llm_inference(system_prompt, user_msg)
    except Exception as e:
        logger.info("Text LLM extraction unavailable (%s) — using heuristic fallback", e)
        return {"signals": _heuristic_signals(text, source_type),
                "method": "heuristic", "source_type": source_type}

    m = re.search(r"\[.*\]", response_text, re.DOTALL)
    if not m:
        return {"signals": _heuristic_signals(text, source_type),
                "method": "heuristic", "source_type": source_type}
    try:
        parsed = json.loads(m.group())
    except json.JSONDecodeError:
        return {"signals": _heuristic_signals(text, source_type),
                "method": "heuristic", "source_type": source_type}

    return {"signals": _validate(parsed), "method": "llm", "source_type": source_type}


def apply_text_signals(signals: list[dict], source_type: str, title: str = "",
                       expires_days: int = 14) -> int:
    """Persist extracted text signals into user_signals so they nudge predictions.
    Mirrors the YVIS apply path; source_tag encodes the text source."""
    import uuid
    from datetime import datetime, timedelta
    from backend.database.duckdb_client import get_conn

    conn = get_conn()
    tag = {"fomc": "FOMC_TEXT", "earnings": "EARNINGS_TEXT"}.get(source_type, "USER_TEXT")
    expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
    count = 0
    for s in signals:
        try:
            conn.execute(
                """
                INSERT INTO user_signals
                    (id, ticker, signal_type, domain, content, extracted_signal,
                     weight_multiplier, confidence, source_tag, created_at, expires_at, is_active,
                     parameter_name, horizon)
                VALUES (?, ?, 'text', ?, ?, ?, ?, ?, ?, now(), ?, TRUE, ?, '1w')
                """,
                [str(uuid.uuid4()), s.get("ticker"), s.get("domain", "macro"),
                 f"[{tag}] {title} — {s.get('key_quote', '')[:200]}",
                 s.get("extracted_signal", 0.0),
                 max(0.5, min(2.0, s.get("weight", 50) / 50.0)),
                 s.get("confidence", 0.6), tag, expires_at, s.get("parameter_name", "market_sentiment")],
            )
            count += 1
        except Exception as e:
            logger.warning("Failed to apply text signal: %s", e)
    conn.commit()
    return count
