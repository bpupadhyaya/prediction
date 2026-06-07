@echo off
call .venv\Scripts\activate.bat

start /B python -m backend.data.scheduler --once

start /B python -m uvicorn backend.main:app --host 127.0.0.1 --port 8080

timeout /t 3 /nobreak >nul

start http://localhost:8080

echo Server running. Close this window to stop.
pause
