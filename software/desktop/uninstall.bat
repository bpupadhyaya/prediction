@echo off
REM Prediction — desktop uninstall (Windows)
setlocal

set SCRIPT_DIR=%~dp0
set ROOT=%SCRIPT_DIR%..\..\domains

echo Prediction — Desktop Uninstall
echo ================================
echo.

set STOCK_DIR=%ROOT%\finance\projects\stock-market\development\software\desktop
if exist "%STOCK_DIR%\uninstall.bat" (
    echo [1/1] Stock Market Prediction
    call "%STOCK_DIR%\uninstall.bat"
)

echo.
echo All desktop prediction modules removed.
endlocal
