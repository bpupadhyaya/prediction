@echo off
:: uninstall.bat — Remove everything installed by install.bat for the stock-market project.
::
:: Removes:
::   - Running server and scheduler processes (port 8080)
::   - Python virtual environment (.venv\)
::   - All data: DuckDB database, trained models, ONNX exports (%USERPROFILE%\.prediction\stock-market\)
::   - Built frontend (frontend\dist\)
::
:: Does NOT touch:
::   - Source code (backend\, frontend\src\, etc.)
::   - requirements.txt, install.bat, or any repo files
::
:: Usage:
::   uninstall.bat            -- interactive, asks for confirmation
::   uninstall.bat --force    -- skip confirmation prompt
::   uninstall.bat --dry-run  -- show what would be removed, do nothing
::

setlocal EnableDelayedExpansion

set SCRIPT_DIR=%~dp0
set DATA_DIR=%USERPROFILE%\.prediction\stock-market
set VENV_DIR=%SCRIPT_DIR%.venv
set DIST_DIR=%SCRIPT_DIR%frontend\dist

set FORCE=0
set DRY_RUN=0

for %%A in (%*) do (
    if "%%A"=="--force"   set FORCE=1
    if "%%A"=="--dry-run" set DRY_RUN=1
)

echo.
echo Stock Market Prediction -- Uninstaller
echo ======================================
echo.

:: --- Find running server on port 8080 ---
set PORT_PID=
for /f "tokens=5" %%P in ('netstat -ano 2^>nul ^| findstr ":8080 " ^| findstr "LISTENING"') do (
    set PORT_PID=%%P
)

:: --- Find running scheduler process ---
set SCHED_PID=
for /f "tokens=2" %%P in ('wmic process where "commandline like '%%backend.data.scheduler%%'" get processid 2^>nul ^| findstr /r "[0-9]"') do (
    set SCHED_PID=%%P
)

echo The following will be removed:
echo.

if defined PORT_PID (
    echo   [proc]   uvicorn server (PID !PORT_PID!, port 8080)
) else (
    echo   [skip]   uvicorn server (not running)
)

if defined SCHED_PID (
    echo   [proc]   scheduler (PID !SCHED_PID!)
) else (
    echo   [skip]   scheduler (not running)
)

if exist "%DATA_DIR%" (
    echo   [data]   %DATA_DIR%  (DuckDB database + trained models + ONNX export)
) else (
    echo   [skip]   %DATA_DIR%  (not found)
)

if exist "%VENV_DIR%" (
    echo   [dir]    %VENV_DIR%  (Python virtual environment)
) else (
    echo   [skip]   %VENV_DIR%  (not found)
)

if exist "%DIST_DIR%" (
    echo   [dir]    %DIST_DIR%  (built frontend)
) else (
    echo   [skip]   %DIST_DIR%  (not found)
)

echo.

:: --- Dry run ---
if %DRY_RUN%==1 (
    echo Dry run -- no changes made.
    echo.
    goto :end
)

:: --- Confirmation ---
if %FORCE%==0 (
    set /p CONFIRM="Proceed with uninstall? This cannot be undone. [y/N] "
    echo.
    if /i not "!CONFIRM!"=="y" (
        echo Cancelled.
        goto :end
    )
)

:: --- Stop processes ---
if defined PORT_PID (
    echo Stopping server (PID !PORT_PID!)...
    taskkill /PID !PORT_PID! /F >nul 2>&1
    timeout /t 1 /nobreak >nul
)
if defined SCHED_PID (
    echo Stopping scheduler (PID !SCHED_PID!)...
    taskkill /PID !SCHED_PID! /F >nul 2>&1
)

:: --- Remove data and build artifacts ---
if exist "%DATA_DIR%" (
    rmdir /s /q "%DATA_DIR%"
    echo   Removed: %DATA_DIR%
)

if exist "%VENV_DIR%" (
    rmdir /s /q "%VENV_DIR%"
    echo   Removed: %VENV_DIR%
)

if exist "%DIST_DIR%" (
    rmdir /s /q "%DIST_DIR%"
    echo   Removed: %DIST_DIR%
)

:: --- Remove parent data dir if now empty ---
set PARENT_DATA=%USERPROFILE%\.prediction
if exist "%PARENT_DATA%" (
    dir /b /a "%PARENT_DATA%" 2>nul | findstr "." >nul 2>&1
    if errorlevel 1 (
        rmdir "%PARENT_DATA%"
        echo   Removed: %PARENT_DATA% (empty after project removal)
    )
)

echo.
echo Uninstall complete. Source code is untouched.
echo To reinstall: install.bat
echo.

:end
endlocal
pause
