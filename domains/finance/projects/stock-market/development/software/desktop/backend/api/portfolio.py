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

        current_price = float(price_row[0]) if price_row else 0.0
        position_value = current_price * h.quantity
        total_value += position_value

        pred = predict_ticker(ticker, req.horizon)
        gain_loss = None
        if h.purchase_price and h.purchase_price > 0:
            gain_loss = round((current_price - h.purchase_price) / h.purchase_price * 100, 2)

        results.append({
            "ticker": ticker,
            "quantity": h.quantity,
            "current_price": round(current_price, 2),
            "position_value": round(position_value, 2),
            "gain_loss_pct": gain_loss,
            "weight": 0.0,  # filled in below once total_value is known
            "prediction": {
                "direction": pred.direction,
                "probability": pred.probability,
                "expected_return_low": pred.expected_return_low,
                "expected_return_high": pred.expected_return_high,
                "volatility": pred.volatility,
                "model_accuracy": pred.model_accuracy,
            }
        })

    # Portfolio-level weighted metrics
    weighted_return = 0.0
    weighted_vol = 0.0
    bullish = 0

    for r in results:
        w = r["position_value"] / total_value if total_value > 0 else 0.0
        r["weight"] = round(w * 100, 1)
        mid = (r["prediction"]["expected_return_low"] + r["prediction"]["expected_return_high"]) / 2
        weighted_return += w * mid
        weighted_vol += w * r["prediction"]["volatility"]
        if r["prediction"]["direction"] == "up":
            bullish += 1

    return {
        "total_value": round(total_value, 2),
        "holdings": results,
        "summary": {
            "bullish_count": bullish,
            "bearish_count": len(results) - bullish,
            "portfolio_return_low": round((weighted_return - weighted_vol), 4),
            "portfolio_return_high": round((weighted_return + weighted_vol), 4),
            "weighted_volatility": round(weighted_vol, 4),
            "horizon": req.horizon,
        },
        "disclaimer": "Portfolio analysis is probabilistic and for informational purposes only. Not financial advice.",
    }
