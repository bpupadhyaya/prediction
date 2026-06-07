#!/bin/bash
source .venv/bin/activate

# Kill any existing server on port 8080 to release the DuckDB lock
EXISTING=$(lsof -ti tcp:8080 2>/dev/null || true)
if [[ -n "$EXISTING" ]]; then
    echo "Stopping existing server (PID $EXISTING)..."
    kill "$EXISTING" 2>/dev/null || true
    sleep 1
fi

# Start server (APScheduler inside handles daily refresh — no separate process needed)
python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8080 &
SERVER_PID=$!

sleep 2

# Open browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:8080
elif command -v xdg-open &>/dev/null; then
    xdg-open http://localhost:8080
else
    echo "Open http://localhost:8080 in your browser"
fi

echo "Server running. Press Ctrl+C to stop."
wait $SERVER_PID
