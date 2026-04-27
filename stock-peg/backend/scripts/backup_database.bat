@echo off
REM 数据库备份脚本（Windows定时任务）

cd /d %~dp0\..\
uv run python scripts\backup_database.py

pause
