@echo off
REM Prediction — launch desktop modules (Windows)
setlocal

set SCRIPT_DIR=%~dp0
set ROOT=%SCRIPT_DIR%..\..\domains

echo Prediction — Starting Desktop Modules
echo =======================================

set STOCK_DIR=%ROOT%\finance\projects\stock-market\development\software\desktop
if exist "%STOCK_DIR%\start.bat" (
    echo Starting Stock Market Prediction...
    call "%STOCK_DIR%\start.bat"
) else (
    echo Stock Market not installed. Run install.bat first.
)
endlocal
