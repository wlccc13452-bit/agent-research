@echo off
chcp 65001 >nul
echo ====================================
echo 数据获取问题诊断工具
echo ====================================
echo.
echo 使用虚拟环境: d:\play-ground\股票研究\stock-peg\backend\.venv\Scripts\python.exe
echo.

cd /d "%~dp0"

d:\play-ground\股票研究\stock-peg\backend\.venv\Scripts\python.exe diagnose_data_issue.py

echo.
echo ====================================
echo 诊断完成
echo ====================================
echo.
pause
