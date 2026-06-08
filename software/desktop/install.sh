#!/usr/bin/env bash
# Prediction — desktop install (all prediction modules)
set -euo pipefail

BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$SCRIPT_DIR/../../domains"

SKIP_DATA=false
for arg in "$@"; do [[ "$arg" == "--skip-data" ]] && SKIP_DATA=true; done

echo -e "${BLUE}Prediction — Desktop Install${NC}"
echo "=============================="
echo ""

# ── Stock Market ──────────────────────────────────────────────────────────────
echo -e "${BLUE}[1/1] Stock Market Prediction${NC}"
STOCK_DIR="$ROOT/finance/projects/stock-market/development/software/desktop"
if [[ -d "$STOCK_DIR" ]]; then
    bash "$STOCK_DIR/install.sh" ${SKIP_DATA:+--skip-data}
else
    echo -e "${YELLOW}Warning: stock-market desktop not found at $STOCK_DIR${NC}"
fi

echo ""
echo -e "${GREEN}✓ All desktop prediction modules installed.${NC}"
echo "Run ./start.sh to launch."
