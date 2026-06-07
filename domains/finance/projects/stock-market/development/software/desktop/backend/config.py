import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = Path.home() / ".prediction" / "stock-market"
DB_PATH = DATA_DIR / "market.duckdb"
MODELS_DIR = DATA_DIR / "models"
LLM_MODELS_DIR = DATA_DIR / "models" / "llm"
LLM_CONFIG_PATH = DATA_DIR / "llm_config.json"
SYNC_DB_PATH = DATA_DIR / "sync.sqlite"

DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
LLM_MODELS_DIR.mkdir(parents=True, exist_ok=True)

# S&P 500 tickers — Phase 1 universe
SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

FRED_API_KEY = os.getenv("FRED_API_KEY", "")

# GitHub releases URL for mobile sync exports
SYNC_RELEASE_URL = "https://api.github.com/repos/bpupadhyaya/prediction/releases/latest"

PREDICTION_HORIZONS = ["1d", "1w", "1m"]

# Accuracy threshold — retrain if directional accuracy drops below this
ACCURACY_THRESHOLD = 0.52
