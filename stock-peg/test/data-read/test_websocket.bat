@echo off
chcp 65001 >nul
cls
echo ========================================
echo WebSocket 股票数据测试客户端
echo ========================================
echo.
echo 注意：运行此测试前，请确保：
echo   1. Backend服务器已启动（端口8000）
echo   2. 已安装 websockets 库
echo      pip install websockets
echo.
echo ========================================
echo.
echo 请选择测试模式：
echo.
echo [1] 前端流程测试（推荐）
echo     - 完整模拟前端流程
echo     - 自动获取持仓并订阅
echo     - 提供详细诊断信息
echo.
echo [2] 直接订阅测试
echo     - 手动输入股票代码
echo     - 快速测试订阅功能
echo.
set /p choice="请输入选项 (1/2): "

if "%choice%"=="1" goto frontend_mode
if "%choice%"=="2" goto subscribe_mode
echo.
echo [ERROR] 无效选项
pause
exit /b

:frontend_mode
cls
echo ========================================
echo 前端流程测试模式
echo ========================================
echo.
set /p duration="监听时长(秒，默认30): "
if "%duration%"=="" set duration=30
echo.
echo 启动测试...
python "%~dp0test_websocket_client.py" frontend %duration%
goto end

:subscribe_mode
cls
echo ========================================
echo 直接订阅测试模式
echo ========================================
echo.
set /p codes="请输入股票代码(多个用逗号分隔): "
if "%codes%"=="" (
    echo [ERROR] 必须提供股票代码
    pause
    exit /b
)
set /p duration="监听时长(秒，默认30): "
if "%duration%"=="" set duration=30
echo.
echo 启动测试...
python "%~dp0test_websocket_client.py" batch %codes% %duration%
goto end

:end
echo.
echo 测试完成，按任意键退出...
pause >nul
