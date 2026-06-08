#!/usr/bin/env bash
# Prediction — desktop uninstall (all prediction modules)
set -euo pipefail

YELLOW='\033[1;33m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; NC='\033[0m'
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$SCRIPT_DIR/../../domains"

echo -e "${BLUE}Prediction — Desktop Uninstall${NC}"
echo "================================"
echo ""

STOCK_DIR="$ROOT/finance/projects/stock-market/development/software/desktop"
if [[ -f "$STOCK_DIR/uninstall.sh" ]]; then
    echo -e "${BLUE}[1/1] Stock Market Prediction${NC}"
    bash "$STOCK_DIR/uninstall.sh"
fi

echo ""
echo -e "${GREEN}✓ All desktop prediction modules removed.${NC}"
