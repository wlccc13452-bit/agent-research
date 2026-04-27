@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion
echo ================================
echo   Stock PEG 开发模式启动脚本
echo   （带热加载，可能不稳定）
echo ================================
echo.
echo ⚠️  警告：热加载在Windows上可能卡住
echo    如果卡住，请使用 start.bat（无热加载）
echo.
pause

echo.
echo [1/3] 检查并清理旧进程...
echo.

REM 使用PowerShell快速清理进程
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='SilentlyContinue'; $ports = @(8000, 5173); foreach ($port in $ports) { $procs = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; foreach ($p in $procs) { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue } }; Write-Host '[OK] 进程清理完成'"
if %errorlevel% neq 0 (
    echo   [OK] 无需清理或已清理
)

REM 等待端口释放
echo 等待端口释放...
timeout /t 2 /nobreak > nul
echo   [OK] 端口已检查

REM 快速清理日志文件
echo.
echo 清理日志文件...
set "LOGS_DIR=%~dp0backend\logs"
if exist "%LOGS_DIR%" (
    del /q /s "%LOGS_DIR%\*.log" > nul 2>&1
    del /q /s "%LOGS_DIR%\*.json" > nul 2>&1
    echo   [OK] 日志已清理
) else (
    echo   [OK] 无需清理
)

echo.
echo   [OK] 清理完成
timeout /t 1 /nobreak > nul

echo.
echo [2/3] 启动服务窗口（server/client 双面板，热加载模式）...
echo.
echo   配置：
echo   - WATCHFILES_FORCE_POLLING=true（使用轮询模式）
echo   - WATCHFILES_POLL_DELAY_MS=1000（每秒检查一次）
echo   - --reload-delay 2.0（延迟2秒重载）
echo   - 只监视关键目录（routers、services、database）
echo.
start "" wt -d "%~dp0backend" cmd /k "set WATCHFILES_FORCE_POLLING=true && set WATCHFILES_POLL_DELAY_MS=1000 && uv run uvicorn main:app --reload --reload-delay 2.0 --reload-dir routers --reload-dir services --reload-dir database --host 0.0.0.0 --port 8000" ; split-pane -V -s 0.4 -d "%~dp0frontend" powershell -NoExit -Command "npm run dev"
echo   [OK] 已启动单窗口双面板（左60%% server / 右40%% client）

echo.
echo [3/3] 等待服务初始化...
timeout /t 3 /nobreak > nul

echo.
echo ================================
echo   启动完成！
echo ================================
echo.
echo 后端服务: http://localhost:8000
echo 前端服务: http://localhost:5173
echo API文档:  http://localhost:8000/docs
echo.
echo ⚠️  如果热加载卡住，按 Ctrl+C 重启后端
echo.
echo 此窗口将自动关闭...
timeout /t 3 /nobreak > nul
