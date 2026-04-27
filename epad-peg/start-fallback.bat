@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ================================
echo   EPAD Bot 启动脚本 (备用模式)
echo ================================
echo.
echo 将打开3个独立的命令行窗口
echo.

echo [1/3] 清理端口...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8100 ^| findstr LISTENING') do (
    taskkill /PID %%a /F > nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :4040 ^| findstr LISTENING') do (
    taskkill /PID %%a /F > nul 2>&1
)
timeout /t 2 /nobreak > nul

echo [2/3] 启动服务...
echo   - 启动 ngrok...
start "EPAD Bot - ngrok" cmd /k "ngrok http 8100"
timeout /t 2 /nobreak > nul

echo   - 启动 epad-bot...
start "EPAD Bot - Server" cmd /k "uv run epad-bot"
timeout /t 2 /nobreak > nul

echo   - 启动 codebuddy...
start "EPAD Bot - CodeBuddy" cmd /k "codebuddy"

echo [3/3] 启动完成！
echo.
echo   ngrok: http://localhost:4040
echo   epad-bot: http://localhost:8100
echo.
echo 此窗口将在 5 秒后关闭...
timeout /t 5 /nobreak > nul
