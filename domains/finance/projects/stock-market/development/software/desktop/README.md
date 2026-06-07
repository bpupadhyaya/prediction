# Desktop Platform — Stock Market Prediction

Local-first app — runs entirely on your laptop/desktop. No cloud, no Docker, no server setup. One script does everything.

## System Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| **RAM** | 4 GB | 8 GB — model training loads ~600K feature rows into memory |
| **Disk** | 1 GB free | 2 GB — ~500 MB Python venv + deps, ~400 MB DuckDB history, ~100 MB model/ONNX files, ~50 MB frontend |
| **CPU** | Any modern x86_64 or Apple Silicon | 4+ cores — GradientBoostingClassifier training uses all cores; first setup takes 10–30 min depending on CPU |
| **OS** | macOS 12+, Ubuntu 20.04+, Windows 10+ | — |
| **Python** | 3.10 | 3.11+ |
| **Network** | Broadband | — (first-time data download: ~15 min for full S&P 500 history) |

## Software Requirements

- Python 3.10+ (check: `python3 --version`)
- Internet connection for first-time data download (~15 min for full S&P 500 history)
- Optional: Node.js 18+ to rebuild the frontend from source (pre-built `dist/` is committed)
- Optional: FRED API key for macro indicators (free at https://fred.stlouisfed.org/docs/api/api_key.html)

## Quick start

### macOS / Linux

```bash
cd domains/finance/projects/stock-market/development/software/desktop
chmod +x install.sh start.sh uninstall.sh
./install.sh          # one-time setup: venv, pip install, DB init, initial data download
./start.sh            # start the app (opens browser automatically)
```

### Windows

```cmd
cd domains\finance\projects\stock-market\development\software\desktop
install.bat
start.bat
```

## What the scripts do

| Script | Action |
|--------|--------|
| `install.sh` | Creates `.venv`, installs Python deps, optionally builds frontend, runs `setup.py` |
| `setup.py` | Initialises DuckDB, downloads 5yr S&P 500 price history, downloads macro indicators, trains initial model |
| `start.sh` | Activates venv, starts daily scheduler in background, launches FastAPI server on `localhost:8080`, opens browser |

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + uvicorn (Python) |
| Database | DuckDB (columnar, embedded, zero server) |
| ML | GradientBoostingClassifier → ONNX export |
| Frontend | TypeScript + Vite + Chart.js (pre-built, served by FastAPI) |
| Data | yfinance (prices), FRED API (macro), SEC EDGAR (fundamentals) |

## Uninstall

To remove everything this project installed (processes, data, venv, build artifacts):

```bash
./uninstall.sh            # interactive — shows sizes, asks for confirmation
./uninstall.sh --dry-run  # preview what would be removed, make no changes
./uninstall.sh --force    # skip confirmation prompt
```

Removes:
- Running server (`localhost:8080`) and scheduler processes
- `~/.prediction/stock-market/` — DuckDB database, trained models, ONNX export (~400 MB–1 GB)
- `.venv/` — Python virtual environment (~500 MB)
- `frontend/dist/` — built frontend

Does **not** touch source code, `install.sh`, `requirements.txt`, or any repo files.

## Data location

All data lives in `~/.prediction/stock-market/` — separate from the code. Delete this folder to reset to a clean state.

```
~/.prediction/stock-market/
  market.duckdb       main database
  models/             trained model files (.pkl + .onnx)
```

## API endpoints

The backend also exposes a REST API at `http://localhost:8080/api/`:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/stocks/search?q=AAPL` | Search stocks by ticker or name |
| GET | `/stocks/{ticker}/prices?days=365` | OHLCV price history |
| GET | `/stocks/{ticker}/info` | Stock metadata |
| GET | `/predict/{ticker}?horizon=1w` | Prediction for one stock |
| GET | `/predict/batch/top?limit=20` | Top predictions by signal strength |
| POST | `/portfolio/analyze` | Analyze a portfolio |
| POST | `/sync/refresh` | Trigger background data refresh |
| GET | `/sync/status` | Check refresh status |

Horizons: `1d` (1 day), `1w` (1 week), `1m` (1 month)
