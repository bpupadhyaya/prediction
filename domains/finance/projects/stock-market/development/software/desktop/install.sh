#!/usr/bin/env bash
# install.sh — One-shot setup for the stock-market prediction desktop app.
#
# Usage:
#   ./install.sh             # full setup (safe to re-run — skips what's done)
#   ./install.sh --skip-data # install dependencies only, skip download + training
#
set -uo pipefail   # catch unbound vars; individual failures handled by pip_install()

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SKIP_DATA=false
for arg in "$@"; do
    [[ "$arg" == "--skip-data" ]] && SKIP_DATA=true
done

echo -e "${BLUE}Stock Market Prediction — Setup${NC}"
echo "================================="
echo ""

# ── Robust pip installer ──────────────────────────────────────────────────────
# Retries with --no-cache-dir on failure (handles corrupted cached wheels).
pip_install() {
    local desc="$1"; shift
    echo "  Installing $desc..."
    if pip install "$@" --quiet 2>/dev/null; then
        echo -e "  ${GREEN}✓ $desc${NC}"
        return 0
    fi
    echo -e "  ${YELLOW}First attempt failed — clearing pip cache and retrying...${NC}"
    pip cache purge 2>/dev/null || true
    if pip install "$@" --no-cache-dir --quiet; then
        echo -e "  ${GREEN}✓ $desc (retry ok)${NC}"
        return 0
    fi
    echo -e "  ${RED}✗ Could not install $desc${NC}"
    return 1
}

# ── Find compatible Python (3.10–3.12) ───────────────────────────────────────
# Python 3.13+ lacks pre-built ML wheels (scikit-learn, numpy, onnxruntime).
find_python() {
    for candidate in python3.12 python3.11 python3.10 python3; do
        if command -v "$candidate" &>/dev/null; then
            local major minor
            major=$("$candidate" -c "import sys; print(sys.version_info.major)" 2>/dev/null)
            minor=$("$candidate" -c "import sys; print(sys.version_info.minor)" 2>/dev/null)
            if [[ "$major" -eq 3 && "$minor" -ge 10 && "$minor" -le 12 ]]; then
                echo "$candidate"; return 0
            fi
        fi
    done
    return 1
}

PYTHON=$(find_python || true)

if [[ -z "$PYTHON" ]]; then
    echo -e "${YELLOW}No compatible Python (3.10–3.12) found.${NC}"
    echo "ML packages require Python 3.10–3.12."
    echo ""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Installing python@3.11 via Homebrew..."
        if ! command -v brew &>/dev/null; then
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install python@3.11
        PYTHON=python3.11
    else
        echo "Install Python 3.11: sudo apt-get install -y python3.11 python3.11-venv"
        exit 1
    fi
fi

echo "Python: $PYTHON ($($PYTHON --version))"
echo ""

# ── Virtual environment ───────────────────────────────────────────────────────
if [[ -d ".venv" ]]; then
    VENV_VER=$(.venv/bin/python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "unknown")
    NEED_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [[ "$VENV_VER" != "$NEED_VER" ]]; then
        echo -e "${YELLOW}Existing .venv uses Python $VENV_VER but need $NEED_VER — recreating...${NC}"
        rm -rf .venv
    fi
fi
if [[ ! -d ".venv" ]]; then
    echo "Creating virtual environment ($($PYTHON --version))..."
    "$PYTHON" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
echo "Venv: $(python3 --version) at $(which python3)"
echo ""

# ── Python dependencies ───────────────────────────────────────────────────────
echo "Installing dependencies..."
pip install --upgrade pip --quiet

# Install each package group separately so one failure doesn't block others
pip_install "core web framework"     fastapi==0.115.0 "uvicorn[standard]==0.30.0"
pip_install "database"               "duckdb>=1.0.0"
pip_install "data & ML"              pandas==2.2.2 "numpy==1.26.4" scikit-learn==1.5.0 xgboost==2.1.0
pip_install "ONNX export"            "onnx>=1.16.0" "skl2onnx>=1.17.0" "onnxruntime>=1.18.0"
pip_install "market data"            "yfinance>=0.2.50" "fredapi==0.5.2" "lxml>=4.9.0"
pip_install "utilities"              httpx==0.27.0 apscheduler==3.10.4 ta==0.11.0 python-dotenv==1.0.1 "psutil>=5.9.0"
echo ""

# ── llama-cpp-python (LLM inference, optional) ───────────────────────────────
if python3 -c "import llama_cpp" &>/dev/null 2>&1; then
    echo -e "${GREEN}✓ llama-cpp-python already installed${NC}"
else
    echo "Installing llama-cpp-python (LLM inference engine)..."
    ARCH=$(uname -m); OS_NAME=$(uname -s)
    if [[ "$OS_NAME" == "Darwin" && "$ARCH" == "arm64" ]]; then
        echo "  Apple Silicon — installing with Metal GPU acceleration..."
        if ! pip install llama-cpp-python \
                --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/metal \
                --quiet 2>/dev/null; then
            echo -e "  ${YELLOW}Metal wheel unavailable — falling back to CPU build...${NC}"
            pip_install "llama-cpp-python (CPU)" llama-cpp-python || \
                echo -e "  ${YELLOW}llama-cpp-python skipped — LLM tab will prompt to re-run install.sh${NC}"
        else
            echo -e "  ${GREEN}✓ llama-cpp-python (Metal)${NC}"
        fi
    else
        pip_install "llama-cpp-python (CPU)" llama-cpp-python || \
            echo -e "  ${YELLOW}llama-cpp-python skipped — LLM tab will prompt to re-run install.sh${NC}"
    fi
fi
echo ""

# ── Database + data download + training ──────────────────────────────────────
if [[ "$SKIP_DATA" == "true" ]]; then
    echo "Skipping data download and training (--skip-data)."
else
    echo "Setting up database and downloading market data..."
    echo "  • S&P 500 (~503 stocks, 5-year history) — 25–40 min first run"
    echo "  • Hot stocks not in S&P 500 (HOOD, PLTR, COIN, RDDT, etc.)"
    echo "  • Already-downloaded tickers are skipped — safe to re-run"
    echo ""
    python3 -m backend.setup
fi

echo ""
echo -e "${GREEN}✓ Setup complete!${NC}"
echo "Run ./start.sh to launch the app."
