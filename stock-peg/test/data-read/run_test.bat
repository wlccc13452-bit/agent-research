@echo off
chcp 65001 >nul
echo ========================================
echo 股票数据读取测试工具
echo 使用Server端服务直接读取数据库
echo ========================================
echo.

cd /d "%~dp0"

echo 正在启动测试工具...
echo.

python read_stock_data.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo 错误：启动失败！
    echo 请检查是否已安装依赖：
    echo   pip install sqlalchemy aiosqlite
    echo ========================================
    pause
)
