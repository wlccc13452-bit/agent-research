@echo off
cd /d d:\play-ground\股票研究\stock-peg\backend
start /b cmd /c ".venv\Scripts\python.exe main.py > logs\startup.log 2>&1"
timeout /t 5 /nobreak >nul
echo 后端服务启动完成
pause
