"""
Local LLM-based stock prediction using llama-cpp-python (GGUF models).
Falls back gracefully if llama-cpp-python is not installed.
"""
import json
import re
import platform
import os
import logging
import numpy as np

from backend.config import LLM_MODELS_DIR
from backend.models.registry import MODEL_BY_ID
from backend.models.trainer import build_features
from backend.database.duckdb_client import get_conn

logger = logging.getLogger(__name__)

HORIZON_LABELS = {
    "1d": "1 trading day",
    "1w": "1 trading week (5 days)",
    "1m": "1 month (~21 trading days)",
}
HORIZON_DAYS = {"1d": 1, "1w": 5, "1m": 21}

_PROMPT = """You are a quantitative financial analyst. Analyze the following technical indicators for {ticker} and predict the likely price direction over the next {horizon_label}.

Technical Indicators (latest trading day):
- RSI (14-day): {rsi:.1f}  [<30 = oversold, >70 = overbought]
- 5-day return: {r5:+.2%}
- 20-day return: {r20:+.2%}
- Price vs 20-day moving average: {ma20:+.2%}
- Price vs 50-day moving average: {ma50:+.2%}
- 20-day annualized volatility: {vol:.1%}
- Volume vs 20-day average: {volr:.2f}x
- RSI percentile rank vs S&P 500 peers: {rsi_rank:.0%}
- 20-day momentum rank vs S&P 500 peers: {mom_rank:.0%}

Recent closing prices (oldest → newest, last 15 days):
{price_table}

Based solely on these technical signals, respond with ONLY valid JSON — no text before or after:
{{"direction": "up" or "down", "confidence": 0.50-0.95, "reasoning": "one concise sentence explaining the key signal"}}"""


# ─── Model cache — reloaded only when model_id changes ────────────────────────
_cache: dict = {"model_id": None, "llm": None}


def _load_llm(model_id: str):
    try:
        from llama_cpp import Llama
    except ImportError:
        raise RuntimeError(
            "llama-cpp-python is not installed. Re-run install.sh to set it up."
        )

    meta = MODEL_BY_ID.get(model_id)
    if meta is None:
        raise ValueError(f"Unknown model id: {model_id!r}")

    model_path = LLM_MODELS_DIR / meta["hf_file"]
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found at {model_path}. Download it from the Models tab."
        )

    is_apple_silicon = platform.system() == "Darwin" and platform.machine() == "arm64"
    n_gpu_layers = -1 if is_apple_silicon else 0   # -1 = offload all layers to Metal
    n_threads = max(1, (os.cpu_count() or 4) // 2)

    logger.info(
        f"Loading {meta['name']} — Metal={'on' if is_apple_silicon else 'off'}, "
        f"threads={n_threads}"
    )
    return Llama(
        model_path=str(model_path),
        n_ctx=1024,
        n_threads=n_threads,
        n_gpu_layers=n_gpu_layers,
        verbose=False,
    )


def get_llm(model_id: str):
    if _cache["model_id"] != model_id:
        _cache["llm"] = _load_llm(model_id)
        _cache["model_id"] = model_id
    return _cache["llm"]


def unload_llm() -> None:
    """Release the cached LLM from memory (e.g., when user clears a model)."""
    _cache["model_id"] = None
    _cache["llm"] = None


def get_active_model_id() -> str | None:
    """Active LLM model id from llm_config.json, or None if none selected."""
    from backend.config import LLM_CONFIG_PATH
    try:
        if LLM_CONFIG_PATH.exists():
            return json.loads(LLM_CONFIG_PATH.read_text()).get("active_model_id")
    except Exception:
        pass
    return None


def _run_llm_inference(system_prompt: str, user_msg: str, max_tokens: int = 512) -> str:
    """
    Run a single text completion with the active local LLM and return raw text.

    Shared entry point for the text/video intelligence extractors. Raises if no
    model is active or installed — callers are expected to fall back to a
    heuristic so the feature degrades gracefully without a downloaded model.
    """
    model_id = get_active_model_id()
    if not model_id:
        raise RuntimeError("No active LLM model selected (download + activate one in the Models tab).")
    llm = get_llm(model_id)
    prompt = f"{system_prompt}\n\n{user_msg}\n"
    response = llm(prompt, max_tokens=max_tokens, temperature=0.1, stop=["```"])
    return response["choices"][0]["text"].strip()


# ─── Cross-sectional rank helper ───────────────────────────────────────────────
def _peer_ranks(ticker: str) -> tuple[float, float]:
    """Return (rsi_rank, momentum_rank) percentiles vs current S&P 500 peers."""
    try:
        from backend.models.predictor import _get_cross_sectional_features
        cs = _get_cross_sectional_features()
        if cs is None:
            return 0.5, 0.5
        row = cs[cs["ticker"] == ticker]
        if row.empty:
            return 0.5, 0.5
        return (
            float(row["rsi_rank"].iloc[0]) if "rsi_rank" in row.columns else 0.5,
            float(row["return_20d_rank"].iloc[0]) if "return_20d_rank" in row.columns else 0.5,
        )
    except Exception:
        return 0.5, 0.5


# ─── Main prediction function ──────────────────────────────────────────────────
def predict_with_llm(ticker: str, horizon: str, model_id: str) -> dict:
    """
    Run LLM-based prediction for one ticker.
    Returns: {"direction": "up"|"down", "confidence": float, "reasoning": str}
          or {"error": str} on failure.
    """
    conn = get_conn()
    df = conn.execute("""
        SELECT date, open, high, low, close, volume
        FROM prices WHERE ticker = ?
        ORDER BY date DESC LIMIT 120
    """, [ticker]).df().sort_values("date")

    if len(df) < 60:
        return {"error": "Insufficient price history for this ticker"}

    feat = build_features(df)
    if feat.empty:
        return {"error": "Could not compute technical features"}

    last = feat.iloc[-1]
    rsi_rank, mom_rank = _peer_ranks(ticker)

    recent = df.tail(15)
    price_table = "\n".join(
        f"  {str(r['date'])[:10]}: ${float(r['close']):.2f}"
        for _, r in recent.iterrows()
    )

    prompt = _PROMPT.format(
        ticker=ticker,
        horizon_label=HORIZON_LABELS.get(horizon, horizon),
        rsi=float(last["rsi"]),
        r5=float(last["return_5d"]),
        r20=float(last["return_20d"]),
        ma20=float(last["ma_20"]),
        ma50=float(last["ma_50"]),
        vol=float(last["volatility_20"]) * np.sqrt(252),
        volr=float(last["volume_ratio"]),
        rsi_rank=rsi_rank,
        mom_rank=mom_rank,
        price_table=price_table,
    )

    llm = get_llm(model_id)
    try:
        response = llm(
            prompt,
            max_tokens=150,
            temperature=0.1,
            stop=["\n\n", "```"],
        )
        raw = response["choices"][0]["text"].strip()
        return _parse(raw)
    except Exception as e:
        logger.error(f"LLM inference error for {ticker}: {e}")
        return {"error": str(e)}


def _parse(raw: str) -> dict:
    match = re.search(r'\{[^{}]+\}', raw, re.DOTALL)
    if not match:
        return {"error": f"No JSON found in response: {raw[:120]!r}"}
    try:
        data = json.loads(match.group())
        direction = str(data.get("direction", "unknown")).lower().strip()
        confidence = float(data.get("confidence", 0.5))
        confidence = round(max(0.5, min(0.95, confidence)), 4)
        reasoning = str(data.get("reasoning", "")).strip()
        if direction not in ("up", "down"):
            direction = "unknown"
        return {"direction": direction, "confidence": confidence, "reasoning": reasoning}
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        return {"error": f"JSON parse error: {e}  raw={raw[:120]!r}"}
