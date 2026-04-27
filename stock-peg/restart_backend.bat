@echo off
setlocal enabledelayedexpansion

echo [INFO] 正在停止现有的后端服务...
:: 强制关闭所有 python.exe 进程（针对该项目环境）
taskkill /F /IM python.exe /T 2>nul

:: 如果你想更精确点，可以根据端口杀进程（假设后端在 8000 端口）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    taskkill /F /PID %%a 2>nul
)

:: 使用 ping 代替 timeout 以避开“重定向”报错
ping 127.0.0.1 -n 3 >nul

echo [INFO] 正在启动后端服务 (uv run)...
cd /d %~dp0\backend
:: 使用 /B 启动，避免弹出多余窗口，且不在 VS Code 终端中产生重定向冲突
start "Stock-PEG" uv run python main.py

echo [INFO] 服务已启动，等待 5 秒进行健康检查...
ping 127.0.0.1 -n 6 >nul

echo [INFO] 正在推送测试事件...
curl -s -X POST http://localhost:8000/api/feishu/push-event/STOCK_RESEARCH_START

echo ========================================
echo [OK] 重启流程已完成！
echo ========================================
pause