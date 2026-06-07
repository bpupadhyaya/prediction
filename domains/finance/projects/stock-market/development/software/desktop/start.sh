#!/bin/bash
source .venv/bin/activate

# Refresh data in background if internet is available
python3 -m backend.data.scheduler --once &

# Start server
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
