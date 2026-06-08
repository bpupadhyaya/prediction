@echo off
REM Prediction — desktop install (Windows)
setlocal

set SCRIPT_DIR=%~dp0
set ROOT=%SCRIPT_DIR%..\..\domains

echo Prediction — Desktop Install
echo ==============================
echo.

echo [1/1] Stock Market Prediction
set STOCK_DIR=%ROOT%\finance\projects\stock-market\development\software\desktop
if exist "%STOCK_DIR%\install.bat" (
    call "%STOCK_DIR%\install.bat" %*
) else (
    echo Warning: stock-market desktop not found at %STOCK_DIR%
)

echo.
echo All desktop prediction modules installed.
echo Run start.bat to launch.
endlocal
