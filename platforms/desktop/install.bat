@echo off
echo Stock Market Prediction -- Setup
echo =================================

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

python --version

if not exist ".venv" (
    python -m venv .venv
)
call .venv\Scripts\activate.bat

python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo Python dependencies installed.

where node >nul 2>&1
if %errorlevel% equ 0 (
    echo Building frontend...
    cd frontend && npm install --silent && npm run build --silent && cd ..
    echo Frontend built.
) else (
    echo Node.js not found -- using pre-built frontend.
)

echo Initialising database and downloading initial data...
echo This may take a few minutes on first run...
python -m backend.setup

echo.
echo Setup complete! Run start.bat to launch.
pause
