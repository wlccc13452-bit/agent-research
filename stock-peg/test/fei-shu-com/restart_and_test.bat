@echo off
chcp 65001 > nul
echo ========================================
echo   Restarting Backend Service
echo ========================================
echo.

echo Step 1: Stopping old backend processes...
taskkill /F /FI "WINDOWTITLE eq PegBot Backend*" > nul 2>&1
timeout /t 2 /nobreak > nul

echo Step 2: Starting new backend service...
cd /d "%~dp0..\..\backend"
start "PegBot Backend" cmd /k "python main.py"

echo.
echo Waiting for service to start (8 seconds)...
timeout /t 8 /nobreak > nul

echo.
echo ========================================
echo   Service Restarted Successfully
echo ========================================
echo.
echo Now test in Feishu:
echo   1. Send: 持仓
echo   2. Click stock name button
echo   3. Should see stock price (no error)
echo.
echo ========================================
pause
