from fastapi import APIRouter
from pydantic import BaseModel
from backend.models.predictor import predict_ticker
from backend.database.duckdb_client import get_conn

router = APIRouter()


class Holding(BaseModel):
    ticker: str
    quantity: float
    purchase_price: float | None = None


class PortfolioRequest(BaseModel):
    holdings: list[Holding]
    horizon: str = "1w"


@router.post("/analyze")
def analyze_portfolio(req: PortfolioRequest):
    conn = get_conn()
    results = []
    total_value = 0.0

    for h in req.holdings:
        ticker = h.ticker.upper()
        price_row = conn.execute("""
            SELECT close FROM prices WHERE ticker = ?
            ORDER BY date DESC LIMIT 1
        """, [ticker]).fetchone()

        current_price = price_row[0] if price_row else 0.0
        position_value = current_price * h.quantity
        total_value += position_value

        pred = predict_ticker(ticker, req.horizon)
        gain_loss = None
        if h.purchase_price:
            gain_loss = round((current_price - h.purchase_price) / h.purchase_price * 100, 2)

        results.append({
            "ticker": ticker,
            "quantity": h.quantity,
            "current_price": round(current_price, 2),
            "position_value": round(position_value, 2),
            "gain_loss_pct": gain_loss,
            "prediction": {
                "direction": pred.direction,
                "probability": pred.probability,
                "expected_return_low": pred.expected_return_low,
                "expected_return_high": pred.expected_return_high,
                "volatility": pred.volatility,
                "model_accuracy": pred.model_accuracy,
            }
        })

    # Portfolio-level risk
    bullish = sum(1 for r in results if r["prediction"]["direction"] == "up")
    avg_volatility = sum(r["prediction"]["volatility"] for r in results) / len(results) if results else 0

    return {
        "total_value": round(total_value, 2),
        "holdings": results,
        "summary": {
            "bullish_count": bullish,
            "bearish_count": len(results) - bullish,
            "avg_volatility": round(avg_volatility, 4),
            "horizon": req.horizon,
        },
        "disclaimer": "Portfolio analysis is probabilistic. Not financial advice.",
    }
