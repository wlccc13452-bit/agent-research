@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion
echo ================================
echo   Stock PEG 项目停止脚本
echo ================================
echo.

echo 正在停止所有服务...
echo.

REM 1. 停止后端（端口8000）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo 停止后端进程 %%a...
    taskkill /PID %%a /F > nul 2>&1
)

REM 2. 停止前端（端口5173）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    echo 停止前端进程 %%a...
    taskkill /PID %%a /F > nul 2>&1
)

REM 3. 清理所有 Node 进程
for /f "tokens=2" %%a in ('tasklist ^| findstr "node.exe" 2^>nul') do (
    echo 清理 Node 进程 %%a...
    taskkill /PID %%a /F > nul 2>&1
)

REM 4. 清理 Python 后端进程
for /f "tokens=2" %%a in ('tasklist ^| findstr "python.exe" 2^>nul') do (
    wmic process where "processid=%%a and commandline like '%%main.py%%'" get processid 2>nul | findstr %%a >nul
    if !errorlevel! equ 0 (
        echo 清理 Python 进程 %%a...
        taskkill /PID %%a /F > nul 2>&1
    )
)

REM 5. 清理卡住的网络连接
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*CLOSE_WAIT\|:8000.*FIN_WAIT" 2^>nul') do (
    echo 清理卡住的连接 %%a...
    taskkill /PID %%a /F > nul 2>&1
)

echo.
echo ✅ 所有服务已停止
echo.
pause
