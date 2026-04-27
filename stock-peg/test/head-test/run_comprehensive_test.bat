@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================================================================
echo 综合功能测试
echo ================================================================================
echo.

set PYTHON_EXE=d:\play-ground\股票研究\stock-peg\backend\.venv\Scripts\python.exe

echo 使用Python: %PYTHON_EXE%
echo.

echo 开始测试...
echo ================================================================================
echo.

%PYTHON_EXE% comprehensive_test.py

echo.
echo ================================================================================
echo 测试完成！
echo.
pause
