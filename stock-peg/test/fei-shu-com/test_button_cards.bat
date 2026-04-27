@echo off
chcp 65001 > nul
echo ========================================
echo   Button-Based Cards Test
echo ========================================
echo.
echo Starting backend service...
echo.

cd /d "%~dp0..\..\backend"

echo Starting Python backend...
start "PegBot Backend" cmd /k "python main.py"

echo.
echo Waiting for service to start (5 seconds)...
timeout /t 5 /nobreak > nul

echo.
echo ========================================
echo   Test Instructions
echo ========================================
echo.
echo 1. Open Feishu app
echo 2. Send message: 持仓
echo    or: 查看关注
echo.
echo 3. Test buttons:
echo    - Stock name button: Query price
echo    - Query button: Query details
echo    - Delete button: Delete stock
echo.
echo 4. Check backend console for logs
echo.
echo ========================================
echo.
echo Press any key to close this window...
pause > nul
