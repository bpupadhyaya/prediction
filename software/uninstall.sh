#!/usr/bin/env bash
# Prediction — top-level uninstall
# Removes all desktop prediction modules. Mobile: uninstall via App Store / Google Play.
set -euo pipefail

BLUE='\033[0;34m'; GREEN='\033[0;32m'; BOLD='\033[1m'; NC='\033[0m'
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${BOLD}Prediction — Uninstall${NC}"
echo "========================"
echo ""

echo -e "${BLUE}Desktop${NC}"
bash "$SCRIPT_DIR/desktop/uninstall.sh"

echo ""
echo -e "${GREEN}✓ Uninstall complete.${NC}"
echo "Mobile: remove the Prediction app from your device via App Store / Google Play."
