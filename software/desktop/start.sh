#!/usr/bin/env bash
# Prediction — launch all active desktop modules
set -euo pipefail

BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$SCRIPT_DIR/../../domains"

echo -e "${BLUE}Prediction — Starting Desktop Modules${NC}"
echo "======================================="

STOCK_DIR="$ROOT/finance/projects/stock-market/development/software/desktop"
if [[ -f "$STOCK_DIR/start.sh" ]]; then
    echo -e "${BLUE}Starting Stock Market Prediction...${NC}"
    bash "$STOCK_DIR/start.sh"
else
    echo -e "${YELLOW}Stock Market not installed. Run ./install.sh first.${NC}"
fi
