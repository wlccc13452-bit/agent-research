@echo off
cd /d d:\2026projects\stocks-research\stock-peg\backend
echo 正在启动服务器...
echo.
.venv\Scripts\python.exe main.py 2>&1
echo.
echo 服务器已停止运行
echo.
pause
