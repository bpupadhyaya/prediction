#!/bin/bash
set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}Stock Market Prediction — Setup${NC}"
echo "================================="

# Python check
if ! command -v python3 &>/dev/null; then
    echo "Python 3 not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if ! command -v brew &>/dev/null; then
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install python3
    else
        sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
    fi
fi

echo "Python: $(python3 --version)"

# Virtual environment
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

# Dependencies
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "Python dependencies installed."

# Frontend build (only if Node.js available)
if command -v node &>/dev/null; then
    echo "Building frontend..."
    cd frontend && npm install --silent && npm run build --silent && cd ..
    echo "Frontend built."
else
    echo "Node.js not found — using pre-built frontend (dist/)."
fi

# Database + initial data
echo "Initialising database and downloading initial data..."
echo "This may take a few minutes on first run..."
python3 -m backend.setup

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo "Run ./start.sh to launch."
