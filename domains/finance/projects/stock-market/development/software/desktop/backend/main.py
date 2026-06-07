import logging
import os
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.database.duckdb_client import init_db
from backend.api import stocks, predict, portfolio, sync
from backend.data.scheduler import start_scheduler
from backend.models.trainer import HORIZON_MODEL_PATHS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _background_retrain():
    try:
        from backend.models.trainer import retrain_if_needed
        retrain_if_needed()
    except Exception as e:
        logger.warning(f"Background retrain failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    # If new per-horizon model files are missing, retrain in background so server starts instantly
    if any(not p.exists() for p in HORIZON_MODEL_PATHS.values()):
        logger.info("Per-horizon models not found — retraining in background...")
        threading.Thread(target=_background_retrain, daemon=True).start()
    yield


app = FastAPI(
    title="Stock Market Prediction",
    description="Local stock market prediction — offline capable",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router, prefix="/api/stocks", tags=["stocks"])
app.include_router(predict.router, prefix="/api/predict", tags=["predict"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(sync.router, prefix="/api/sync", tags=["sync"])

# Serve frontend — standalone index.html, no build step required
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")
