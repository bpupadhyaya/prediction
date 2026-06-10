import logging
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from backend.models.predictor import predict_ticker
from backend.config import PREDICTION_HORIZONS

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Response helpers ──────────────────────────────────────────────────────────

def _pred_to_dict(result, include_explanation: bool = False) -> dict:
    d = {
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
    if include_explanation:
        d["explanation"] = result.explanation
        d["calc_chain"]  = result.calc_chain
    return d

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
        raise HTTPException(status_code=422, detail=f"horizon must be one of {PREDICTION_HORIZONS}")
    try:
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LLM prediction failed for {ticker}/{horizon}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"LLM prediction error: {e}")


@router.get("/{ticker}/explain")
def get_prediction_explain(ticker: str, horizon: str = "1w"):
    """Full prediction with SHAP domain breakdown, regime, and user signal info."""
    if horizon not in PREDICTION_HORIZONS:
        raise HTTPException(status_code=422, detail=f"horizon must be one of {PREDICTION_HORIZONS}")
    try:
        result = predict_ticker(ticker.upper(), horizon)
        return _pred_to_dict(result, include_explanation=True)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction explain failed for {ticker}/{horizon}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction error: {e}")


@router.get("/{ticker}")
def get_prediction(ticker: str, horizon: str = "1w"):
    if horizon not in PREDICTION_HORIZONS:
        raise HTTPException(status_code=422, detail=f"horizon must be one of {PREDICTION_HORIZONS}")
    try:
        result = predict_ticker(ticker.upper(), horizon)
        return _pred_to_dict(result, include_explanation=False)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed for {ticker}/{horizon}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction error: {e}")


@router.get("/batch/top")
def get_top_predictions(sector: Optional[str] = None, limit: int = 500):
    try:
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
            try:
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
            except Exception as e:
                logger.warning(f"Skipping {ticker} in batch/top: {e}")
                continue

        # Sort by strongest signal (furthest from 50/50)
        results.sort(key=lambda x: abs(x["probability"] - 0.5), reverse=True)
        return results[:limit]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"batch/top failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not load top predictions: {e}")


@router.get("/batch/hot")
def get_hot_predictions():
    """Predictions for curated high-profile stocks + pre-IPO company list."""
    try:
        traded = []
        for ticker in _HOT_TRADED:
            try:
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
            except Exception as e:
                logger.warning(f"Skipping {ticker} in batch/hot: {e}")
                entry = {"ticker": ticker, "model_ready": False}
            traded.append(entry)

        return {"traded": traded, "pre_ipo": _PRE_IPO}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"batch/hot failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not load hot predictions: {e}")


# ── Retrain ───────────────────────────────────────────────────────────────────

_retrain_status: dict = {"running": False, "last_result": None}


def _run_retrain():
    from backend.models.trainer import train_all_models
    from backend.models.exporter import export as export_onnx
    try:
        _retrain_status["running"] = True
        avg_acc = train_all_models()
        onnx_path = None
        try:
            onnx_path = str(export_onnx(verify=True))
        except Exception as e:
            logger.warning(f"ONNX export failed (non-fatal): {e}")
        _retrain_status["last_result"] = {
            "status": "ok",
            "avg_directional_accuracy": round(avg_acc, 4),
            "onnx_exported": onnx_path is not None,
            "onnx_path": onnx_path,
        }
        logger.info(f"Retrain complete — avg accuracy: {avg_acc:.4f}")
    except Exception as e:
        _retrain_status["last_result"] = {"status": "error", "error": str(e)}
        logger.error(f"Retrain failed: {e}", exc_info=True)
    finally:
        _retrain_status["running"] = False


@router.post("/retrain", status_code=202)
def retrain_models(background_tasks: BackgroundTasks):
    """Retrain all GBM models on expanded feature set and re-export ONNX."""
    if _retrain_status["running"]:
        return {"status": "already_running", "message": "Retrain already in progress"}
    background_tasks.add_task(_run_retrain)
    return {"status": "started", "message": "Retrain started in background"}


@router.get("/retrain/status")
def retrain_status():
    return _retrain_status
