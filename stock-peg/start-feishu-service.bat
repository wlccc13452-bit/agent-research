@echo off
cd /d "d:\play-ground\股票研究\stock-peg\backend"
echo ============================================================
echo Starting Feishu Long Connection Service
echo ============================================================
echo.
echo This service connects to Feishu servers to receive messages.
echo Keep this window open while using the application.
echo.
echo ============================================================
uv run python d:\play-ground\股票研究\stock-peg\test\temp\quick_start.py
pause
