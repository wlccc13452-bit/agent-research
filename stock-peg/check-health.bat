@echo off
chcp 65001 > nul
echo ================================
echo   Stock PEG 健康检查
echo ================================
echo.

echo [1/3] 检查后端服务（端口8000）...
netstat -ano | findstr ":8000.*LISTENING" > nul 2>&1
if %errorlevel% equ 0 (
    echo   OK - 后端服务运行中
) else (
    echo   ERROR - 后端服务未运行
)

echo.
echo [2/3] 检查前端服务（端口5173）...
netstat -ano | findstr ":5173.*LISTENING" > nul 2>&1
if %errorlevel% equ 0 (
    echo   OK - 前端服务运行中
) else (
    echo   ERROR - 前端服务未运行
)

echo.
echo [3/3] 检查进程状态...
for /f %%a in ('tasklist ^| findstr /C:"python.exe" ^| find /c /v ""') do set PYTHON_COUNT=%%a
for /f %%a in ('tasklist ^| findstr /C:"node.exe" ^| find /c /v ""') do set NODE_COUNT=%%a
echo   Python 进程数: %PYTHON_COUNT%
echo   Node 进程数: %NODE_COUNT%

echo.
echo ================================
echo   检查完成
echo ================================
pause
