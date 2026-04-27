@echo off
echo 启动市场情绪历史数据回填...
cd /d "%~dp0"
uv run python tools/backfill_market_sentiment.py --days 60
echo.
echo 回填完成！
pause
