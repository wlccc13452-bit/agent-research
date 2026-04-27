@echo off
chcp 65001 >nul
echo ================================================================================
echo 检查服务器数据完整性测试
echo ================================================================================
echo.

cd /d "%~dp0"

REM 使用虚拟环境Python运行测试
set PYTHON_EXE=d:\play-ground\股票研究\stock-peg\backend\.venv\Scripts\python.exe

if not exist "%PYTHON_EXE%" (
    echo [!] 虚拟环境Python不存在，使用系统Python
    set PYTHON_EXE=python
)

echo 使用Python: %PYTHON_EXE%
echo.
echo 开始检查...
echo ================================================================================
echo.

"%PYTHON_EXE%" check_missing_data_v2.py

echo.
echo ================================================================================
echo 检查完成！
echo.
echo 如需更新缺失数据，请：
echo   1. 重启后端服务（推荐）
echo   2. 或手动调用 API：POST /api/stocks/update/^<code^>/day
echo ================================================================================
pause
