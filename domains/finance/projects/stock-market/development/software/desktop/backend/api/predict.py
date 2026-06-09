from fastapi import APIRouter, HTTPException
from backend.models.predictor import predict_ticker
from backend.config import PREDICTION_HORIZONS

router = APIRouter()

# ── Hot Stocks ────────────────────────────────────────────────────────────────
# Curated high-profile tickers — some may not be in DB yet (shown as no-data)
_HOT_TRADED = [
    "NVDA", "AAPL", "MSFT", "META", "GOOGL", "AMZN", "TSLA",
    "AMD", "NFLX", "HOOD", "PLTR", "ARM", "SMCI", "COIN",
    "MSTR", "UBER", "LYFT", "SOFI", "RBLX", "SNAP", "RIVN",
    "SOUN", "AI", "IONQ", "QUBT", "RDDT", "ACHR", "JOBY",
]

_PRE_IPO = [
    {"name": "OpenAI",      "sector": "AI / LLM",      "description": "Maker of ChatGPT, GPT-4o, and Sora",                        "status": "Pre-IPO",  "est_valuation": "$157B"},
    {"name": "Anthropic",   "sector": "AI / LLM",      "description": "AI safety company, maker of Claude",                        "status": "Pre-IPO",  "est_valuation": "$61B"},
    {"name": "SpaceX",      "sector": "Aerospace",     "description": "Rockets, Starship, Starlink satellite internet",             "status": "Pre-IPO",  "est_valuation": "$350B"},
    {"name": "Stripe",      "sector": "Fintech",       "description": "Global payments infrastructure for internet businesses",    "status": "Pre-IPO",  "est_valuation": "$65B"},
    {"name": "Databricks",  "sector": "Data / AI",     "description": "Unified data analytics and AI platform",                    "status": "Pre-IPO",  "est_valuation": "$62B"},
    {"name": "Canva",       "sector": "Design / SaaS", "description": "Online visual design and content creation platform",        "status": "Pre-IPO",  "est_valuation": "$26B"},
    {"name": "Chime",       "sector": "Neobank",       "description": "Mobile-first banking and financial services",               "status": "Pre-IPO",  "est_valuation": "$25B"},
    {"name": "Klarna",      "sector": "Fintech",       "description": "Buy now, pay later — filed for US IPO",                    "status": "Filed IPO","est_valuation": "$20B"},
    {"name": "Discord",     "sector": "Social",        "description": "Community and gaming communication platform",               "status": "Pre-IPO",  "est_valuation": "$15B"},
    {"name": "Epic Games",  "sector": "Gaming",        "description": "Fortnite, Unreal Engine, Epic Games Store",                 "status": "Private",  "est_valuation": "$32B"},
]


@router.post("/{ticker}/llm")
def get_llm_prediction(ticker: str, horizon: str = "1w"):
    """Run prediction with the active LLM model. Slower than GBM but returns reasoning."""
    if horizon not in PREDICTION_HORIZONS:
        raise HTTPException(status_code=400, detail=f"horizon must be one of {PREDICTION_HORIZONS}")
    from backend.api.models_api import _load_config
    from backend.models.llm_predictor import predict_with_llm
    cfg = _load_config()
    model_id = cfg.get("active_model_id")
    if not model_id:
        raise HTTPException(status_code=400, detail="No LLM model activated. Go to Models tab to download and activate one.")
    result = predict_with_llm(ticker.upper(), horizon, model_id)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return {"ticker": ticker.upper(), "horizon": horizon, "model_id": model_id, **result}


@router.get("/{ticker}/explain")
def get_prediction_explain(ticker: str, horizon: str = "1w"):
    """Full prediction with SHAP domain breakdown, regime, and user signal info."""
    if horizon not in PREDICTION_HORIZONS:
        raise HTTPException(status_code=400, detail=f"horizon must be one of {PREDICTION_HORIZONS}")
    result = predict_ticker(ticker.upper(), horizon)
    return {
        "ticker":               result.ticker,
        "horizon":              result.horizon,
        "direction":            result.direction,
        "probability":          result.probability,
        "expected_return_low":  result.expected_return_low,
        "expected_return_high": result.expected_return_high,
        "volatility":           result.volatility,
        "model_accuracy":       result.model_accuracy,
        "model_ready":          result.model_ready,
        "sector":               result.sector,
        "model_type":           result.model_type,
        "regime_label":         result.regime_label,
        "regime":               result.regime,
        "explanation":          result.explanation,
        "user_signals_active":  result.user_signals_active,
        "recent_accuracy":      result.recent_accuracy,
        "disclaimer": "This is a probabilistic prediction, not financial advice.",
    }


@router.get("/{ticker}")
def get_prediction(ticker: str, horizon: str = "1w"):
    if horizon not in PREDICTION_HORIZONS:
        raise HTTPException(status_code=400, detail=f"horizon must be one of {PREDICTION_HORIZONS}")
    result = predict_ticker(ticker.upper(), horizon)
    return {
        "ticker":               result.ticker,
        "horizon":              result.horizon,
        "direction":            result.direction,
        "probability":          result.probability,
        "expected_return_low":  result.expected_return_low,
        "expected_return_high": result.expected_return_high,
        "volatility":           result.volatility,
        "model_accuracy":       result.model_accuracy,
        "model_ready":          result.model_ready,
        "sector":               result.sector,
        "model_type":           result.model_type,
        "regime_label":         result.regime_label,
        "regime":               result.regime,
        "user_signals_active":  result.user_signals_active,
        "recent_accuracy":      result.recent_accuracy,
        "disclaimer": "This is a probabilistic prediction, not financial advice.",
    }


@router.get("/batch/top")
def get_top_predictions(sector: str | None = None, limit: int = 500):
    from backend.database.duckdb_client import get_conn
    conn = get_conn()
    query = """
        SELECT p.ticker
        FROM (SELECT DISTINCT ticker FROM prices) p
        LEFT JOIN stocks s ON p.ticker = s.ticker
    """
    params = []
    if sector:
        query += " WHERE s.sector = ?"
        params.append(sector)
    query += " ORDER BY COALESCE(s.market_cap, 0) DESC"
    tickers = [r[0] for r in conn.execute(query, params).fetchall()]

    results = []
    for ticker in tickers:
        pred = predict_ticker(ticker, "1w")
        if pred.model_ready:
            results.append({
                "ticker": pred.ticker,
                "direction": pred.direction,
                "probability": pred.probability,
                "expected_return_low": pred.expected_return_low,
                "expected_return_high": pred.expected_return_high,
                "volatility": pred.volatility,
                "model_accuracy": pred.model_accuracy,
            })

    # Sort by strongest signal (furthest from 50/50)
    results.sort(key=lambda x: abs(x["probability"] - 0.5), reverse=True)
    return results[:limit]


@router.get("/batch/hot")
def get_hot_predictions():
    """Predictions for curated high-profile stocks + pre-IPO company list."""
    traded = []
    for ticker in _HOT_TRADED:
        pred = predict_ticker(ticker, "1w")
        entry: dict = {"ticker": ticker, "model_ready": pred.model_ready}
        if pred.model_ready:
            entry.update({
                "direction": pred.direction,
                "probability": pred.probability,
                "expected_return_low": pred.expected_return_low,
                "expected_return_high": pred.expected_return_high,
                "volatility": pred.volatility,
                "model_accuracy": pred.model_accuracy,
            })
        traded.append(entry)

    return {"traded": traded, "pre_ipo": _PRE_IPO}
