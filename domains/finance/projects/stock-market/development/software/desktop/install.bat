@echo off
:: install.bat — One-shot setup for the stock-market prediction desktop app.
::
:: Usage:
::   install.bat             -- full setup
::   install.bat --skip-data -- install deps only, skip data download + training
::

setlocal EnableDelayedExpansion

set SKIP_DATA=0
for %%A in (%*) do (
    if "%%A"=="--skip-data" set SKIP_DATA=1
)

echo Stock Market Prediction -- Setup
echo =================================
echo.

:: --- Find compatible Python (3.10-3.12) ---
:: Python 3.13+ lacks pre-built ML package wheels (scikit-learn, onnxruntime, numpy).
set PYTHON=
for %%V in (3.12 3.11 3.10) do (
    if not defined PYTHON (
        where python%%V >nul 2>&1
        if !errorlevel! equ 0 (
            set PYTHON=python%%V
        )
    )
)

:: Fall back to bare 'python' and check its version
if not defined PYTHON (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        for /f "tokens=2 delims=." %%M in ('python --version 2^>^&1') do (
            set PY_MINOR=%%M
        )
        if !PY_MINOR! geq 10 if !PY_MINOR! leq 12 set PYTHON=python
    )
)

if not defined PYTHON (
    echo ERROR: No compatible Python (3.10-3.12) found.
    echo ML packages require Python 3.10-3.12. Python 3.13+ is not yet supported.
    echo.
    echo Download Python 3.11 from: https://www.python.org/downloads/release/python-3119/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=*" %%V in ('!PYTHON! --version 2^>^&1') do echo Using: %%V
echo.

:: --- Virtual environment ---
:: Recreate if it was built with a different Python version
if exist ".venv" (
    for /f "tokens=*" %%V in ('.venv\Scripts\python.exe -c "import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}\")" 2^>nul') do set VENV_VER=%%V
    for /f "tokens=*" %%V in ('!PYTHON! -c "import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}\")"') do set NEED_VER=%%V
    if not "!VENV_VER!"=="!NEED_VER!" (
        echo Existing .venv uses Python !VENV_VER! but need !NEED_VER! -- recreating...
        rmdir /s /q .venv
    )
)
if not exist ".venv" (
    echo Creating virtual environment...
    !PYTHON! -m venv .venv
)
call .venv\Scripts\activate.bat
echo Virtual environment ready.
echo.

:: --- Dependencies ---
echo Installing Python dependencies...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt
echo.


:: --- Database + initial data + model training ---
if %SKIP_DATA%==1 (
    echo Skipping data download and model training (--skip-data^).
) else (
    echo Downloading S^&P 500 history and training model...
    echo Already-downloaded tickers are skipped -- safe to re-run after interruption.
    echo First run: 20-35 min. Resume after Ctrl+C: only downloads what's missing.
    echo.
    python -m backend.setup
)

echo.
echo Setup complete! Run start.bat to launch.
pause
endlocal
