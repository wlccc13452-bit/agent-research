@echo off
chcp 65001 > nul
echo ================================
echo   Stock PEG 项目启动脚本（简单版）
echo ================================
echo.
echo 将打开2个命令行窗口：
echo   - 后端服务 (端口8000)
echo   - 前端服务 (端口5173)
echo.

echo 启动后端服务...
start "Backend - Port 8000" cmd /k "cd /d %~dp0backend && uv run uvicorn main:app --host 0.0.0.0 --port 8000"
timeout /t 2 /nobreak > nul

echo 启动前端服务...
start "Frontend - Port 5173" cmd /k "cd /d %~dp0frontend && npm run dev"

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
timeout /t 3 /nobreak > nul
