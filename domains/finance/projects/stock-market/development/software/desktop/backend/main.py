import logging
import os
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.database.duckdb_client import init_db
from backend.api import stocks, predict, portfolio, sync, models_api, guidance, video_intelligence, text_intelligence
from backend.api.interactive import router as interactive_router
from backend.data.scheduler import start_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _background_retrain():
    try:
        from backend.models.trainer import train_all_models
        train_all_models()
    except Exception as e:
        logger.warning(f"Background retrain failed: {e}")


def _background_initial_load():
    """Load macro + fundamentals data then retrain (first-run or feature upgrade)."""
    try:
        from backend.data.scheduler import run_initial_data_load
        run_initial_data_load()
    except Exception as e:
        logger.warning(f"Initial data load failed: {e}")
    _background_retrain()


def _needs_initial_load() -> bool:
    from backend.database.duckdb_client import get_conn
    conn = get_conn()
    macro_count = conn.execute("SELECT COUNT(*) FROM macro_indicators").fetchone()[0]
    return macro_count < 100


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()

    from backend.models.trainer import models_need_retrain, HORIZON_MODEL_PATHS
    models_missing = any(not p.exists() for p in HORIZON_MODEL_PATHS.values())

    if _needs_initial_load():
        logger.info("Initial data load required — fetching macro + fundamentals then training models...")
        threading.Thread(target=_background_initial_load, daemon=True).start()
    elif models_missing or models_need_retrain():
        logger.info("Models missing or feature set changed — retraining in background...")
        threading.Thread(target=_background_retrain, daemon=True).start()

    # Resolve any outstanding prediction outcomes and update domain weights
    threading.Thread(target=_background_online_learning, daemon=True).start()

    yield


def _background_online_learning():
    """Resolve prediction outcomes and update domain weights in background."""
    try:
        from backend.models.online_learner import resolve_outcomes, update_domain_weights
        n = resolve_outcomes()
        if n > 0:
            update_domain_weights()
    except Exception as e:
        logger.debug(f"Online learning update failed (non-fatal): {e}")


app = FastAPI(
    title="Stock Market Prediction",
    description="Local stock market prediction — offline capable",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "https://bpupadhyaya.github.io",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router,     prefix="/api/stocks",    tags=["stocks"])
app.include_router(predict.router,    prefix="/api/predict",   tags=["predict"])
app.include_router(portfolio.router,  prefix="/api/portfolio", tags=["portfolio"])
app.include_router(sync.router,       prefix="/api/sync",      tags=["sync"])
app.include_router(models_api.router, prefix="/api/models",    tags=["models"])
app.include_router(guidance.router,           prefix="/api/guidance",            tags=["guidance"])
app.include_router(video_intelligence.router, prefix="/api/video-intelligence",   tags=["video-intelligence"])
app.include_router(text_intelligence.router,  prefix="/api/text-intelligence",    tags=["text-intelligence"])
app.include_router(interactive_router)

frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")
