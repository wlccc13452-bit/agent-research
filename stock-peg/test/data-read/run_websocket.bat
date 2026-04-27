@echo off
chcp 65001 >nul
cls
echo ========================================
echo 股票数据读取测试工具
echo ========================================
echo.
echo 请选择运行模式：
echo.
echo [1] GUI界面模式（推荐）
echo     - 图形界面，支持选择股票和数据类型
echo     - 可查看实时行情、K线、报告等多种数据
echo     - 直接读取数据库（不通过WebSocket）
echo.
echo [2] 命令行测试模式
echo     - 快速验证数据库连接
echo     - 测试各数据表读取功能
echo     - 直接读取数据库（不通过WebSocket）
echo.
echo [3] WebSocket测试模式
echo     - 通过WebSocket连接读取数据
echo     - 测试实时行情推送功能
echo     - 需要Backend服务器运行
echo.
echo [4] 验证修复（测试 StockQuote 模型）
echo     - 验证 timestamp 字段修复
echo     - 测试数据库读取功能
echo.
echo [5] 退出
echo.
set /p choice="请输入选项 (1/2/3/4/5): "

if "%choice%"=="1" goto gui_mode
if "%choice%"=="2" goto cli_mode
if "%choice%"=="3" goto websocket_mode
if "%choice%"=="4" goto verify_mode
if "%choice%"=="5" goto end

echo.
echo 无效选项，请重新运行
pause
exit /b

:gui_mode
cls
echo 启动GUI界面（直接读取数据库）...
python "%~dp0read_stock_data.py"
if errorlevel 1 (
    echo.
    echo ========================================
    echo 错误：启动失败！
    echo 请检查Python环境和依赖包
    echo ========================================
    pause
)
goto end

:cli_mode
cls
echo 运行命令行测试（直接读取数据库）...
python "%~dp0test_db_connection.py"
echo.
echo 测试完成，按任意键退出...
pause >nul
goto end

:websocket_mode
cls
echo ========================================
echo WebSocket测试模式
echo ========================================
echo.
echo 注意：需要Backend服务器运行在端口8000
echo.
pause
echo.
echo 启动WebSocket客户端...
python "%~dp0test_websocket_client.py"
echo.
echo 测试完成，按任意键退出...
pause >nul
goto end

:verify_mode
cls
echo 验证修复...
python "%~dp0verify_fix.py"
echo.
echo 验证完成，按任意键退出...
pause >nul
goto end

:end
