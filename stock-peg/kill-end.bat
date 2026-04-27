@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion
echo ================================
echo   Stock PEG 项目启动脚本
echo ================================
echo.
echo 将打开1个PowerShell窗口（分割显示）:
echo   - 左侧Pane: 后端服务 (端口8000)
echo   - 右侧Pane: 前端服务 (端口5173)
echo.

echo [1/3] 检查并清理旧进程...
echo.

REM 检查并杀死端口8000的进程（后端）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo 发现端口8000被占用，正在终止进程 %%a...
    taskkill /PID %%a /F > nul 2>&1
    if !errorlevel! equ 0 (
        echo   [OK] 后端进程 %%a 已终止
    ) else (
        echo   [SKIP] 无法终止进程 %%a
    )
)

REM 检查并杀死端口5173的进程（前端）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    echo 发现端口5173被占用，正在终止进程 %%a...
    taskkill /PID %%a /F > nul 2>&1
    if !errorlevel! equ 0 (
        echo   [OK] 前端进程 %%a 已终止
    ) else (
        echo   [SKIP] 无法终止进程 %%a
    )
)
REM 检查并杀死端口5175的进程（前端）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5175 ^| findstr LISTENING') do (
    echo 发现端口5173被占用，正在终止进程 %%a...
    taskkill /PID %%a /F > nul 2>&1
    if !errorlevel! equ 0 (
        echo   [OK] 前端进程 %%a 已终止
    ) else (
        echo   [SKIP] 无法终止进程 %%a
    )
)

REM 同时检查node进程（Vite开发服务器）
for /f "tokens=2" %%a in ('tasklist ^| findstr "node.exe"') do (
    echo 发现node进程 %%a，正在终止...
    taskkill /PID %%a /F > nul 2>&1
)

REM 同时检查python进程（后端FastAPI）
for /f "tokens=2" %%a in ('tasklist ^| findstr "python.exe"') do (
    wmic process where "processid=%%a and commandline like '%%main.py%%'" get processid 2>nul | findstr %%a >nul
    if !errorlevel! equ 0 (
        echo 发现Python后端进程 %%a，正在终止...
        taskkill /PID %%a /F > nul 2>&1
    )
)

echo   [OK] 清理完成