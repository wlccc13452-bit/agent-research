@echo off
chcp 65001 >nul
REM K线快速加载测试脚本（JavaScript版本）
REM 
REM 功能：测试所有自持股票的K线数据快速加载

echo ====================================
echo K线快速加载测试
echo ====================================
echo.

REM 检查Node.js是否安装
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] 未找到Node.js，请先安装Node.js
    pause
    exit /b 1
)

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM 设置默认后端地址
set BASE_URL=http://localhost:8000

REM 检查是否有自定义参数
if "%1" neq "" (
    set BASE_URL=%1
)

echo 后端地址: %BASE_URL%
echo.

REM 运行JavaScript测试
echo [1/2] 运行测试...
echo.
node "%SCRIPT_DIR%test_kline_fast_load.mjs" --base=%BASE_URL%

if %ERRORLEVEL% equ 0 (
    echo.
    echo ====================================
    echo [成功] 测试完成
    echo ====================================
) else (
    echo.
    echo ====================================
    echo [失败] 测试失败，请检查错误信息
    echo ====================================
)

echo.
pause
