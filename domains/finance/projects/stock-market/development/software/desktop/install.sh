#!/usr/bin/env bash
# install.sh — One-shot setup for the stock-market prediction desktop app.
#
# Usage:
#   ./install.sh          # full setup
#   ./install.sh --skip-data  # install deps only, skip data download + training
#
set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SKIP_DATA=false
for arg in "$@"; do
    [[ "$arg" == "--skip-data" ]] && SKIP_DATA=true
done

echo -e "${BLUE}Stock Market Prediction — Setup${NC}"
echo "================================="
echo ""

# --- Find a compatible Python (3.10–3.12) ---
# Default python3 may be 3.13+ which lacks ML package wheels.
# Auto-detect a compatible version before requiring manual steps.
find_python() {
    for candidate in python3.12 python3.11 python3.10 python3; do
        if command -v "$candidate" &>/dev/null; then
            local minor
            minor=$("$candidate" -c "import sys; print(sys.version_info.minor)" 2>/dev/null)
            local major
            major=$("$candidate" -c "import sys; print(sys.version_info.major)" 2>/dev/null)
            if [[ "$major" -eq 3 && "$minor" -ge 10 && "$minor" -le 12 ]]; then
                echo "$candidate"
                return 0
            fi
        fi
    done
    return 1
}

PYTHON=$(find_python || true)

if [[ -z "$PYTHON" ]]; then
    echo -e "${YELLOW}No compatible Python (3.10–3.12) found.${NC}"
    echo "ML packages (scikit-learn, onnxruntime, numpy) require Python 3.10–3.12."
    echo ""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Installing python@3.11 via Homebrew..."
        if ! command -v brew &>/dev/null; then
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install python@3.11
        PYTHON=python3.11
    else
        echo "Run: sudo apt-get install -y python3.11 python3.11-venv"
        exit 1
    fi
fi

echo "Using: $PYTHON ($($PYTHON --version))"
echo ""

# --- Virtual environment ---
# Recreate if it was built with the wrong Python version
if [[ -d ".venv" ]]; then
    VENV_VER=$(.venv/bin/python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "unknown")
    NEED_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [[ "$VENV_VER" != "$NEED_VER" ]]; then
        echo -e "${YELLOW}Existing .venv uses Python $VENV_VER but need $NEED_VER — recreating...${NC}"
        rm -rf .venv
    fi
fi
if [[ ! -d ".venv" ]]; then
    echo "Creating virtual environment with $($PYTHON --version)..."
    "$PYTHON" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
echo "Virtual environment: $(python3 --version) at $(which python3)"
echo ""

# --- Dependencies ---
echo "Installing Python dependencies (this takes a few minutes first time)..."
pip install --upgrade pip --quiet
pip install -r requirements.txt

# llama-cpp-python: install with Metal support on Apple Silicon, CPU-only elsewhere.
# This is separate from requirements.txt because the Metal wheel needs a special index URL.
if ! python3 -c "import llama_cpp" &>/dev/null 2>&1; then
    echo "Installing llama-cpp-python (LLM inference engine)..."
    ARCH=$(uname -m)
    OS=$(uname -s)
    if [[ "$OS" == "Darwin" && "$ARCH" == "arm64" ]]; then
        echo "  Apple Silicon detected — installing with Metal GPU acceleration..."
        pip install llama-cpp-python \
            --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/metal \
            --quiet || pip install llama-cpp-python --quiet
    else
        echo "  Installing CPU-only llama-cpp-python..."
        pip install llama-cpp-python --quiet
    fi
else
    echo "llama-cpp-python already installed."
fi
echo ""


# --- Database + initial data + model training ---
if [[ "$SKIP_DATA" == "true" ]]; then
    echo "Skipping data download and model training (--skip-data)."
else
    echo "Downloading S&P 500 history and training model..."
    echo "Already-downloaded tickers are skipped — safe to re-run after interruption."
    echo "First run: 20–35 min. Resume after Ctrl+C: only downloads what's missing."
    echo ""
    python3 -m backend.setup
fi

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo "Run ./start.sh to launch the app."
