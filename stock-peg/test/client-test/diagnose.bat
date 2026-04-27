@echo off
chcp 65001 >nul
REM 环境诊断脚本

echo ====================================
echo 环境诊断
echo ====================================
echo.

REM 1. 检查Node.js
echo [1/4] 检查Node.js...
where node >nul 2>&1
if %ERRORLEVEL% equ 0 (
    for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
    echo   ✅ Node.js已安装: %NODE_VERSION%
) else (
    echo   ❌ Node.js未安装
    pause
    exit /b 1
)

REM 2. 检查后端服务（使用curl测试API）
echo.
echo [2/4] 检查后端服务...
curl -s --max-time 3 http://localhost:8000/api/holdings/ >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo   ✅ 后端服务正在运行 (端口8000)
) else (
    echo   ❌ 后端服务未运行 (端口8000)
    echo   请先启动后端服务: cd backend ^&^& python main.py
    pause
    exit /b 1
)

REM 3. 测试API连接
echo.
echo [3/4] 测试API连接...
curl -s --max-time 3 http://localhost:8000/api/holdings/ | findstr "sectors" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo   ✅ API连接正常
) else (
    echo   ❌ API连接失败
    echo   请检查后端服务是否正常运行
    pause
    exit /b 1
)

REM 4. 测试数据可用性
echo.
echo [4/4] 测试数据可用性...
curl -s --max-time 3 "http://localhost:8000/api/stocks/kline-db-fast/600219?period=day&count=10&quick_load=true&local_only=true" | findstr "data" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo   ✅ K线数据API正常
) else (
    echo   ❌ K线数据API失败
    echo   请检查数据库是否有数据
    pause
    exit /b 1
)

echo.
echo ====================================
echo [成功] 环境诊断通过，可以运行测试
echo ====================================
echo.
echo 运行测试: run_test_mjs.bat
echo.
pause
