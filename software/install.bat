@echo off
REM Prediction — top-level install (Windows)
REM Usage: install.bat [--skip-data]
REM Mobile: download from App Store (iOS) or Google Play (Android)

setlocal
set SCRIPT_DIR=%~dp0

echo Prediction — Install
echo =====================
echo.

echo Desktop
call "%SCRIPT_DIR%desktop\install.bat" %*

echo.
echo Installation complete.
echo Run desktop\start.bat to launch.
endlocal
