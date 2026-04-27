@echo off
chcp 65001 > nul
echo ================================
echo   清理旧进程和日志
echo ================================
echo.

echo [1/3] 清理端口占用的进程...
echo.

REM 手动清理端口8000
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000.*LISTENING"') do (
    echo   终止进程 %%a (端口8000^)
    taskkill /PID %%a /F > nul 2>&1
)

REM 手动清理端口5173
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5173.*LISTENING"') do (
    echo   终止进程 %%a (端口5173^)
    taskkill /PID %%a /F > nul 2>&1
)

echo   [OK] 进程清理完成

echo.
echo [2/3] 清理日志文件...
set "LOGS_DIR=%~dp0backend\logs"
if exist "%LOGS_DIR%" (
    echo   删除日志文件...
    del /q "%LOGS_DIR%\*.log" 2>nul
    echo   [OK] 日志已清理
) else (
    echo   [OK] 无需清理
)

echo.
echo [3/3] 等待端口释放...
timeout /t 2 /nobreak > nul
echo   [OK] 端口已检查

echo.
echo ================================
echo   清理完成！
echo ================================
echo.
echo 现在可以运行 start.bat 启动服务
echo.
pause
