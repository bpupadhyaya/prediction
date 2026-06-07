#!/usr/bin/env bash
# uninstall.sh — Remove everything installed by install.sh for the stock-market project.
#
# Removes:
#   - Running server and scheduler processes (port 8080)
#   - Python virtual environment (.venv/)
#   - All data: DuckDB database, trained models, ONNX exports (~/.prediction/stock-market/)
#   - Built frontend (frontend/dist/)
#
# Does NOT touch:
#   - Source code (backend/, frontend/src/, etc.)
#   - requirements.txt, install.sh, or any repo files
#
# Usage:
#   ./uninstall.sh            # interactive — asks for confirmation
#   ./uninstall.sh --force    # skip confirmation prompt
#   ./uninstall.sh --dry-run  # show what would be removed, do nothing
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$HOME/.prediction/stock-market"
VENV_DIR="$SCRIPT_DIR/.venv"
DIST_DIR="$SCRIPT_DIR/frontend/dist"

FORCE=false
DRY_RUN=false
for arg in "$@"; do
    case "$arg" in
        --force)   FORCE=true ;;
        --dry-run) DRY_RUN=true ;;
    esac
done

# --- Helpers ---
print_size() {
    local path="$1"
    if [[ -e "$path" ]]; then
        du -sh "$path" 2>/dev/null | cut -f1
    else
        echo "0"
    fi
}

will_remove() {
    local path="$1"
    local desc="$2"
    local size
    size=$(print_size "$path")
    if [[ -e "$path" ]]; then
        echo "  [${size}]  $path  ($desc)"
    else
        echo "  [skip]   $path  (not found)"
    fi
}

do_remove() {
    local path="$1"
    if [[ -e "$path" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            echo "  DRY RUN: would remove $path"
        else
            rm -rf "$path"
            echo "  Removed: $path"
        fi
    fi
}

echo ""
echo "Stock Market Prediction — Uninstaller"
echo "======================================"
echo ""

# --- Show what will be removed ---
echo "The following will be removed:"
echo ""

# Processes
PORT_PID=$(lsof -ti tcp:8080 2>/dev/null || true)
SCHED_PID=$(pgrep -f "backend.data.scheduler" 2>/dev/null || true)

if [[ -n "$PORT_PID" ]]; then
    echo "  [proc]   uvicorn server (PID $PORT_PID, port 8080)"
else
    echo "  [skip]   uvicorn server (not running)"
fi
if [[ -n "$SCHED_PID" ]]; then
    echo "  [proc]   scheduler (PID $SCHED_PID)"
else
    echo "  [skip]   scheduler (not running)"
fi

will_remove "$DATA_DIR"   "DuckDB database + trained models + ONNX export"
will_remove "$VENV_DIR"   "Python virtual environment"
will_remove "$DIST_DIR"   "built frontend"

echo ""

# --- Confirmation ---
if [[ "$FORCE" == "false" && "$DRY_RUN" == "false" ]]; then
    read -r -p "Proceed with uninstall? This cannot be undone. [y/N] " confirm
    echo ""
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
fi

if [[ "$DRY_RUN" == "true" ]]; then
    echo "Dry run — no changes made."
    echo ""
fi

# --- Stop processes ---
if [[ -n "$PORT_PID" && "$DRY_RUN" == "false" ]]; then
    echo "Stopping server (PID $PORT_PID)..."
    kill "$PORT_PID" 2>/dev/null || true
    sleep 1
fi
if [[ -n "$SCHED_PID" && "$DRY_RUN" == "false" ]]; then
    echo "Stopping scheduler (PID $SCHED_PID)..."
    kill "$SCHED_PID" 2>/dev/null || true
fi

# --- Remove data and build artifacts ---
do_remove "$DATA_DIR"
do_remove "$VENV_DIR"
do_remove "$DIST_DIR"

if [[ "$DRY_RUN" == "false" ]]; then
    # Remove parent data dir if now empty
    PARENT_DATA="$HOME/.prediction"
    if [[ -d "$PARENT_DATA" ]] && [[ -z "$(ls -A "$PARENT_DATA" 2>/dev/null)" ]]; then
        rm -rf "$PARENT_DATA"
        echo "  Removed: $PARENT_DATA (empty after project removal)"
    fi

    echo ""
    echo "Uninstall complete. Source code is untouched."
    echo "To reinstall: ./install.sh"
fi
echo ""
