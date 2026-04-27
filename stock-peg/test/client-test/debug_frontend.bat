@echo off
chcp 65001 >nul
REM 前端API调试工具

echo ====================================
echo 前端API调试工具
echo ====================================
echo.

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0

REM 设置默认后端地址
set BASE_URL=http://localhost:8000

REM 检查是否有自定义参数
if "%1" neq "" (
    set BASE_URL=%1
)

echo 后端地址: %BASE_URL%
echo.

REM 运行调试工具
node "%SCRIPT_DIR%debug_frontend_api.mjs" %BASE_URL%

echo.
pause
