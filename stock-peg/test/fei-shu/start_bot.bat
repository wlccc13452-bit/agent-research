@echo off
chcp 65001 >nul
echo ========================================
echo   飞书机器人测试启动脚本
echo ========================================
echo.

cd /d D:\play-ground\股票研究\stock-peg\test\fei-shu

echo [启动] 正在启动机器人...
echo.
echo [提示] 请在飞书中：
echo   1. 打开机器人聊天窗口（会显示"[进入会话]"日志）
echo   2. 发送文本消息测试（如：查询 700）
echo.

D:\play-ground\股票研究\stock-peg\backend\.venv\Scripts\python.exe bot_chat.py

pause
