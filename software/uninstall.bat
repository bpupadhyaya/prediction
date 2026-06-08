@echo off
REM Prediction — top-level uninstall (Windows)
setlocal
set SCRIPT_DIR=%~dp0

echo Prediction — Uninstall
echo ========================
echo.

echo Desktop
call "%SCRIPT_DIR%desktop\uninstall.bat"

echo.
echo Uninstall complete.
echo Mobile: remove Prediction from your device via App Store or Google Play.
endlocal
