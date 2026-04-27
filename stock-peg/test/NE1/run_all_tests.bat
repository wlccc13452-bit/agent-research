@echo off
chcp 65001 >nul
echo ====================================
echo 修复方案测试工具
echo ====================================
echo.
echo 使用虚拟环境: d:\play-ground\股票研究\stock-peg\backend\.venv\Scripts\python.exe
echo.

cd /d "%~dp0"

echo 【测试1】美股指数获取修复测试
echo ------------------------------------
d:\play-ground\股票研究\stock-peg\backend\.venv\Scripts\python.exe test_fix_us_indices.py
if %errorlevel% neq 0 (
    echo ✗ 测试1失败
    pause
    exit /b 1
)

echo.
echo 【测试2】A股指数获取修复测试
echo ------------------------------------
d:\play-ground\股票研究\stock-peg\backend\.venv\Scripts\python.exe test_fix_a_stock_indices.py
if %errorlevel% neq 0 (
    echo ✗ 测试2失败
    pause
    exit /b 1
)

echo.
echo ====================================
echo ⚠ 测试完成，发现需要修复的问题
echo ====================================
echo.
echo 发现问题:
echo 1. ✅ 美股指数 - 列名问题（已确认修复方案）
echo 2. ✅ A股指数 - 代码格式问题（已确认修复方案）
echo 3. ⚠️ 财务数据 - 表结构问题（需要修复）
echo.
echo 请查看详细报告:
echo - TEST_REPORT.md
echo - FIX_GUIDE.md
echo - FINANCIAL_DATA_ISSUE.md
echo.
pause
