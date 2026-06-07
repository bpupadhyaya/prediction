# Desktop Platform — Stock Market Prediction

Local-first app — runs entirely on your laptop/desktop. No cloud, no Docker, no server setup. One script does everything.

## System Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| **RAM** | 4 GB | 8 GB — model training loads ~600K feature rows into memory |
| **Disk** | 1 GB free | 2 GB — ~500 MB Python venv + deps, ~400 MB DuckDB history, ~100 MB model/ONNX files, ~50 MB frontend |
| **CPU** | Any modern x86_64 or Apple Silicon | 4+ cores — GradientBoostingClassifier training uses all cores; first setup takes 10–30 min |
| **OS** | macOS 12+, Ubuntu 20.04+, Windows 10+ | — |
| **Python** | 3.10–3.12 (auto-detected by install.sh) | 3.11 |
| **Network** | Broadband | Required only for first-time data download (~15 min) |

> **Note:** Python 3.13+ is not supported — ML packages (scikit-learn, onnxruntime, numpy) have no pre-built wheels for it yet. `install.sh` auto-detects a compatible version on your machine; if none is found it installs `python@3.11` via Homebrew automatically.

## Software Requirements

- Python 3.10–3.12 — auto-handled by `install.sh`
- Internet connection — required for first-time data download only
- Optional: Node.js 18+ to rebuild the frontend from source (pre-built `dist/` is included)
- Optional: FRED API key for macro indicators (free at https://fred.stlouisfed.org/docs/api/api_key.html)

---

## Installation

### First-time install

```bash
cd domains/finance/projects/stock-market/development/software/desktop
./install.sh
```

This does everything in one shot:
1. Detects a compatible Python (3.10–3.12), installs one via Homebrew if not found
2. Creates `.venv/` and installs all Python dependencies
3. Builds the frontend (if Node.js is available)
4. Downloads 5 years of S&P 500 price history (~15 min)
5. Downloads macro indicators (FRED)
6. Trains the initial prediction model (~10–30 min depending on CPU)

### Start the app

```bash
./start.sh
```

Opens `http://localhost:8080` in your browser. Also starts the daily background scheduler (refreshes data at 22:00 UTC).

---

## Re-installation Scenarios

### Update code only — keep existing database and trained model

Re-running `./install.sh` is safe. It detects the existing database and skips the data download and model training:

```bash
git pull
./install.sh    # updates deps only; database and model are untouched
./start.sh
```

What is preserved:
- `~/.prediction/stock-market/market.duckdb` — all historical price data
- `~/.prediction/stock-market/models/` — trained model and ONNX export

What is updated:
- Python dependencies (upgraded to latest compatible versions)
- Frontend build (if Node.js is available)

---

### Update Python dependencies only — skip everything else

```bash
./install.sh --skip-data
```

Installs/upgrades Python packages and rebuilds the frontend. Does not touch the database, model, or run any data download.

---

### Clean reinstall — remove everything and start fresh

Use this when you want a completely fresh state: new database, new model, updated data from scratch.

```bash
./uninstall.sh    # interactive — shows what will be removed and asks for confirmation
./install.sh      # full reinstall from scratch
```

Or non-interactively:

```bash
./uninstall.sh --force && ./install.sh
```

`uninstall.sh` removes:
- Running server and scheduler processes
- `~/.prediction/stock-market/` — database, models, ONNX export (~400 MB–1 GB)
- `.venv/` — Python virtual environment (~500 MB)
- `frontend/dist/` — built frontend

It does **not** touch source code, `install.sh`, `requirements.txt`, or any other repo files.

---

### Preview what uninstall will remove (dry run)

```bash
./uninstall.sh --dry-run
```

Shows file sizes and what would be deleted — makes no changes.

---

## File Locations

```
# Source code (inside repo — never deleted by uninstall.sh)
domains/finance/projects/stock-market/development/software/desktop/
  install.sh          one-shot installer
  start.sh            app launcher
  uninstall.sh        cleanup script
  requirements.txt    Python dependencies
  backend/            FastAPI backend + ML pipeline
  frontend/           TypeScript/Vite frontend source
  frontend/dist/      pre-built frontend (served by FastAPI)
  .venv/              Python virtual environment (created by install.sh)

# Data (outside repo — lives in home directory)
~/.prediction/stock-market/
  market.duckdb       main database (S&P 500 history, macro, predictions)
  models/             trained model (.pkl) + ONNX export (.onnx)
```

---

## What the scripts do

| Script | Action |
|--------|--------|
| `install.sh` | Auto-detects Python, creates `.venv`, installs deps, builds frontend, downloads data + trains model (skipped if DB exists) |
| `install.sh --skip-data` | Same but skips data download and model training unconditionally |
| `start.sh` | Activates venv, starts daily scheduler in background, launches FastAPI on `localhost:8080`, opens browser |
| `uninstall.sh` | Stops processes, removes data dir + venv + dist; interactive by default |
| `uninstall.sh --dry-run` | Preview only — no changes |
| `uninstall.sh --force` | Skip confirmation prompt |

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + uvicorn (Python) |
| Database | DuckDB (columnar, embedded, zero server) |
| ML | GradientBoostingClassifier → ONNX export |
| Frontend | TypeScript + Vite + Chart.js (pre-built, served by FastAPI) |
| Data | yfinance (prices), FRED API (macro), SEC EDGAR (fundamentals) |

---

## API Endpoints

The backend exposes a REST API at `http://localhost:8080/api/`:

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

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `install.sh` fails with Python version error | Script auto-installs `python@3.11` via Homebrew on macOS; on Linux run `sudo apt-get install python3.11 python3.11-venv` |
| Port 8080 already in use | `lsof -ti tcp:8080 \| xargs kill` then re-run `./start.sh` |
| Empty predictions after install | Wait for `setup.py` to finish — look for "Training complete" in terminal output |
| Browser doesn't open | Navigate manually to `http://localhost:8080` |
| Want to reset data without reinstalling code | `rm -rf ~/.prediction/stock-market && python3 -m backend.setup` (activate venv first) |
