from fastapi import APIRouter, HTTPException
from backend.models.predictor import predict_ticker
from backend.config import PREDICTION_HORIZONS

router = APIRouter()


@router.get("/{ticker}")
def get_prediction(ticker: str, horizon: str = "1w"):
    if horizon not in PREDICTION_HORIZONS:
        raise HTTPException(status_code=400, detail=f"horizon must be one of {PREDICTION_HORIZONS}")
    result = predict_ticker(ticker.upper(), horizon)
    return {
        "ticker": result.ticker,
        "horizon": result.horizon,
        "direction": result.direction,
        "probability": result.probability,
        "expected_return_low": result.expected_return_low,
        "expected_return_high": result.expected_return_high,
        "volatility": result.volatility,
        "model_accuracy": result.model_accuracy,
        "model_ready": result.model_ready,
        "disclaimer": "This is a probabilistic prediction, not financial advice. Always verify with your own research.",
    }


@router.get("/batch/top")
def get_top_predictions(sector: str | None = None, limit: int = 20):
    from backend.database.duckdb_client import get_conn
    conn = get_conn()
    query = "SELECT ticker FROM stocks"
    params = []
    if sector:
        query += " WHERE sector = ?"
        params.append(sector)
    query += f" ORDER BY market_cap DESC NULLS LAST LIMIT {limit}"
    tickers = [r[0] for r in conn.execute(query, params).fetchall()]

    results = []
    for ticker in tickers:
        pred = predict_ticker(ticker, "1w")
        if pred.model_ready:
            results.append({
                "ticker": pred.ticker,
                "direction": pred.direction,
                "probability": pred.probability,
                "model_accuracy": pred.model_accuracy,
            })
    results.sort(key=lambda x: abs(x["probability"] - 0.5), reverse=True)
    return results
