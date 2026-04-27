@echo off
chcp 65001 > nul
echo ================================
echo   Stock PEG 项目启动脚本（调试版）
echo ================================
echo.
echo DEBUG: Step 1 - 显示信息
echo.

echo 将打开1个Windows Terminal窗口（双面板）:
echo   - 左侧60%%: 后端服务 (端口8000)
echo   - 右侧40%%: 前端服务 (端口5173)
echo.
pause

echo.
echo DEBUG: Step 2 - 准备启动命令
set "BACKEND_DIR=%~dp0backend"
set "FRONTEND_DIR=%~dp0frontend"
echo   后端目录: %BACKEND_DIR%
echo   前端目录: %FRONTEND_DIR%
pause

echo.
echo DEBUG: Step 3 - 启动Windows Terminal
echo   命令: start "" wt -d "%BACKEND_DIR%" ...
start "" wt -d "%BACKEND_DIR%" cmd /k "echo Backend starting... && uv run uvicorn main:app --host 0.0.0.0 --port 8000" ; split-pane -V -s 0.4 -d "%FRONTEND_DIR%" powershell -NoExit -Command "echo Frontend starting...; npm run dev"
echo   [OK] Windows Terminal启动命令已执行

echo.
echo DEBUG: Step 4 - 等待3秒
timeout /t 3 /nobreak

echo.
echo ================================
echo   启动完成！
echo ================================
echo.
echo 后端服务: http://localhost:8000
echo 前端服务: http://localhost:5173
echo API文档:  http://localhost:8000/docs
echo.
echo 此窗口将自动关闭...
timeout /t 2 /nobreak
