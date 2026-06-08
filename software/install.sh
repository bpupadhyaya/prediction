#!/usr/bin/env bash
# Prediction — top-level install script
#
# Usage:
#   ./install.sh              # install desktop modules (default)
#   ./install.sh --skip-data  # install dependencies only, skip data download
#   ./install.sh --all        # install all platforms (desktop + print mobile instructions)
#
# Mobile apps: download from the App Store (iOS) or Google Play (Android).
# Desktop: installs all active prediction modules for Mac/Linux.
# Windows: use install.bat instead.

set -euo pipefail

BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

SKIP_DATA=false
SHOW_ALL=false
for arg in "$@"; do
    [[ "$arg" == "--skip-data" ]] && SKIP_DATA=true
    [[ "$arg" == "--all" ]] && SHOW_ALL=true
done

echo -e "${BOLD}Prediction — Install${NC}"
echo "====================="
echo ""

# ── Desktop ───────────────────────────────────────────────────────────────────
echo -e "${BLUE}Desktop${NC}"
bash "$SCRIPT_DIR/desktop/install.sh" ${SKIP_DATA:+--skip-data}

echo ""

# ── Mobile (informational) ────────────────────────────────────────────────────
if [[ "$SHOW_ALL" == "true" ]]; then
    echo -e "${BLUE}Mobile (app store links)${NC}"
    echo "  iOS (iPhone/iPad):"
    echo "    App Store → search 'Prediction by Bhim Upadhyaya'"
    echo "    Or open: https://apps.apple.com (link added after App Store submission)"
    echo ""
    echo "  Android:"
    echo "    Google Play → search 'Prediction by Bhim Upadhyaya'"
    echo "    Or download the APK from the GitHub releases page"
    echo ""
fi

echo -e "${GREEN}✓ Installation complete.${NC}"
echo "Run ./desktop/start.sh to launch the desktop app."
