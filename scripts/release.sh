#!/usr/bin/env bash
# release.sh — Publish a new data + model snapshot to GitHub Releases.
#
# What it does:
#   1. Exports the trained ONNX model (backend/models/exporter.py)
#   2. Exports the DuckDB database to a SQLite file (mobile apps use SQLite)
#   3. Compresses the SQLite file with gzip
#   4. Creates a GitHub Release with both files as assets
#
# Mobile apps (iOS + Android) download these assets via SyncManager to refresh
# their local database and on-device model.
#
# Requirements:
#   - Python venv activated: source domains/finance/projects/stock-market/development/software/desktop/.venv/bin/activate
#   - gh CLI authenticated: gh auth login
#   - GITHUB_TOKEN or gh CLI session with write:packages permission
#
# Usage:
#   ./scripts/release.sh                     # auto-increment patch tag (v0.1.1, v0.1.2 ...)
#   ./scripts/release.sh v1.0.0              # explicit tag
#   ./scripts/release.sh --dry-run           # build artifacts only, skip GitHub publish
#
# Output:
#   /tmp/prediction-release/
#     market.sqlite.gz          → DuckDB snapshot exported to SQLite, gzipped
#     stock_predictor.onnx      → ONNX model ready for iOS/Android inference
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DESKTOP_DIR="$REPO_ROOT/domains/finance/projects/stock-market/development/software/desktop"
VENV="$DESKTOP_DIR/.venv"
DATA_DIR="$HOME/.prediction/stock-market"
RELEASE_DIR="/tmp/prediction-release"
GH_REPO="bpupadhyaya/prediction"

# --- Parse args ---
TAG=""
DRY_RUN=false
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        v*) TAG="$arg" ;;
    esac
done

# --- Auto-generate tag if not provided ---
if [[ -z "$TAG" ]]; then
    LATEST=$(gh release list --repo "$GH_REPO" --limit 1 --json tagName --jq '.[0].tagName' 2>/dev/null || echo "")
    if [[ -z "$LATEST" ]]; then
        TAG="v0.1.0"
    else
        # Increment patch version
        MAJOR=$(echo "$LATEST" | cut -d. -f1 | tr -d 'v')
        MINOR=$(echo "$LATEST" | cut -d. -f2)
        PATCH=$(echo "$LATEST" | cut -d. -f3)
        TAG="v${MAJOR}.${MINOR}.$((PATCH + 1))"
    fi
fi

echo "==> Release tag: $TAG"
echo "==> Dry run: $DRY_RUN"
echo ""

# --- Activate venv ---
if [[ ! -f "$VENV/bin/activate" ]]; then
    echo "ERROR: Python venv not found at $VENV. Run ./domains/finance/projects/stock-market/development/software/desktop/install.sh first." >&2
    exit 1
fi
source "$VENV/bin/activate"

# --- Prepare release dir ---
rm -rf "$RELEASE_DIR"
mkdir -p "$RELEASE_DIR"

# --- Step 1: Export ONNX model ---
echo "==> Exporting ONNX model..."
cd "$REPO_ROOT/domains/finance/projects/stock-market/development/software/desktop"
python3 -m backend.models.exporter --verify
ONNX_SRC="$DATA_DIR/models/stock_predictor.onnx"
if [[ ! -f "$ONNX_SRC" ]]; then
    echo "ERROR: ONNX export failed — $ONNX_SRC not found." >&2
    exit 1
fi
cp "$ONNX_SRC" "$RELEASE_DIR/stock_predictor.onnx"
echo "    OK: stock_predictor.onnx ($(du -h "$RELEASE_DIR/stock_predictor.onnx" | cut -f1))"

# --- Step 2: Export DuckDB → SQLite ---
echo "==> Exporting DuckDB → SQLite..."
DUCKDB_PATH="$DATA_DIR/market.duckdb"
if [[ ! -f "$DUCKDB_PATH" ]]; then
    echo "ERROR: DuckDB database not found at $DUCKDB_PATH. Run setup.py first." >&2
    exit 1
fi

SQLITE_PATH="$RELEASE_DIR/market.sqlite"
python3 - <<PYEOF
import duckdb, sqlite3, json
from pathlib import Path

src = duckdb.connect("$DUCKDB_PATH", read_only=True)
dst_path = "$SQLITE_PATH"
dst = sqlite3.connect(dst_path)

# Export each table
tables = [r[0] for r in src.execute("SHOW TABLES").fetchall()]
for tbl in tables:
    rows = src.execute(f"SELECT * FROM {tbl}").fetchall()
    if not rows:
        continue
    cols = [d[0] for d in src.execute(f"DESCRIBE {tbl}").fetchall()]
    placeholders = ",".join(["?"] * len(cols))
    col_defs = ",".join([f'"{c}" TEXT' for c in cols])
    dst.execute(f'CREATE TABLE IF NOT EXISTS "{tbl}" ({col_defs})')
    # Convert all values to strings for maximum compatibility
    str_rows = [tuple(str(v) if v is not None else "" for v in row) for row in rows]
    dst.executemany(f'INSERT INTO "{tbl}" VALUES ({placeholders})', str_rows)
    print(f"    {tbl}: {len(rows)} rows")

dst.commit()
dst.close()
src.close()
print(f"SQLite export complete → {dst_path}")
PYEOF

# --- Step 3: Gzip the SQLite file ---
echo "==> Compressing SQLite..."
gzip -9 -f -k "$SQLITE_PATH"
rm "$SQLITE_PATH"
echo "    OK: market.sqlite.gz ($(du -h "$RELEASE_DIR/market.sqlite.gz" | cut -f1))"

# --- Step 4: Write release metadata sidecar ---
echo "==> Writing metadata..."
python3 - <<PYEOF
import json, datetime, duckdb

src = duckdb.connect("$DUCKDB_PATH", read_only=True)
try:
    row = src.execute("SELECT COUNT(*) FROM stocks").fetchone()
    n_stocks = row[0]
    row = src.execute("SELECT COUNT(*) FROM prices").fetchone()
    n_prices = row[0]
    row = src.execute("SELECT COUNT(*) FROM predictions").fetchone()
    n_preds = row[0]
except Exception as e:
    n_stocks = n_prices = n_preds = 0
src.close()

meta = {
    "tag": "$TAG",
    "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
    "stocks": n_stocks,
    "price_bars": n_prices,
    "predictions": n_preds,
    "files": ["market.sqlite.gz", "stock_predictor.onnx"],
}
with open("$RELEASE_DIR/release_meta.json", "w") as f:
    json.dump(meta, f, indent=2)
print(json.dumps(meta, indent=2))
PYEOF

# --- Step 4b: Copy ONNX into mobile platform source trees ---
echo "==> Copying ONNX into iOS Resources + Android assets..."
IOS_RESOURCES="$REPO_ROOT/domains/finance/projects/stock-market/development/software/ios/StockPrediction/Resources"
ANDROID_ASSETS="$REPO_ROOT/domains/finance/projects/stock-market/development/software/android/app/src/main/assets"
mkdir -p "$IOS_RESOURCES" "$ANDROID_ASSETS"
cp "$RELEASE_DIR/stock_predictor.onnx" "$IOS_RESOURCES/stock_predictor.onnx"
cp "$RELEASE_DIR/stock_predictor.onnx" "$ANDROID_ASSETS/stock_predictor.onnx"
echo "    iOS:     $IOS_RESOURCES/stock_predictor.onnx"
echo "    Android: $ANDROID_ASSETS/stock_predictor.onnx"

echo ""
echo "==> Artifacts:"
ls -lh "$RELEASE_DIR/"

if [[ "$DRY_RUN" == "true" ]]; then
    echo ""
    echo "==> DRY RUN — skipping GitHub Release creation."
    echo "    Artifacts are at: $RELEASE_DIR/"
    exit 0
fi

# --- Step 5: Create GitHub Release ---
echo ""
echo "==> Creating GitHub Release $TAG..."
NOTES="## Data Snapshot $TAG

Auto-generated data + model snapshot for mobile sync.

| Asset | Description |
|-------|-------------|
| \`market.sqlite.gz\` | S&P 500 price history + macro indicators + predictions (gzip-compressed SQLite) |
| \`stock_predictor.onnx\` | Trained GradientBoostingClassifier for on-device inference (iOS + Android) |

**Mobile apps:** Tap *Sync Now* in the Sync tab to download this release.

---
*Generated by scripts/release.sh — $(date -u '+%Y-%m-%d %H:%M UTC')*"

gh release create "$TAG" \
    --repo "$GH_REPO" \
    --title "Data Snapshot $TAG" \
    --notes "$NOTES" \
    "$RELEASE_DIR/market.sqlite.gz" \
    "$RELEASE_DIR/stock_predictor.onnx" \
    "$RELEASE_DIR/release_meta.json"

echo ""
echo "==> Release $TAG published:"
echo "    https://github.com/$GH_REPO/releases/tag/$TAG"
echo ""
echo "==> Mobile apps will download this on next Sync."
