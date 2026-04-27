@echo off
REM K线快速加载测试脚本
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

REM 检查TypeScript是否安装
where npx >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] 未找到npx，请检查Node.js安装
    pause
    exit /b 1
)

REM 设置默认后端地址
set BASE_URL=http://localhost:8000

REM 检查是否有自定义参数
if "%1" neq "" (
    set BASE_URL=%1
)

echo 后端地址: %BASE_URL%
echo.

REM 运行TypeScript测试
echo [1/3] 检查TypeScript编译...
npx tsc --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [警告] TypeScript未安装，使用ts-node运行...
    echo.
    echo [2/3] 安装ts-node...
    call npm install -g ts-node typescript
    if %ERRORLEVEL% neq 0 (
        echo [错误] 安装ts-node失败
        pause
        exit /b 1
    )
)

echo [2/3] 运行测试...
echo.
npx ts-node test_kline_fast_load.ts --base=%BASE_URL%

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
