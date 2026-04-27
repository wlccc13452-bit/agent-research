@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d d:\play-ground\股票研究\stock-peg\backend
d:\play-ground\股票研究\stock-peg\backend\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
