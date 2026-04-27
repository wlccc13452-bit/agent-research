@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

REM Set script directory (remove trailing backslash)
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

echo ================================
echo   EPAD Bot Launcher (3-Panel Mode)
echo ================================
echo.
echo Opening 1 Windows Terminal window (3-panel layout):
echo   Left Top (50%%): ngrok tunnel
echo   Left Bottom (50%%): epad-bot server
echo   Right (60%%): codebuddy AI assistant
echo.

echo [DEBUG] Finding Windows Terminal...
set "WT_EXE=D:\APPS\terminal-1.24.3504.0\WindowsTerminal.exe"

if not exist "!WT_EXE!" (
    echo   [ERROR] Windows Terminal not found at !WT_EXE!
    pause
    exit /b 1
)

echo   [OK] Found: !WT_EXE!
echo   [INFO] Working directory: %SCRIPT_DIR%
echo.
echo   [DEBUG] Launching Windows Terminal...
echo.

REM Launch Windows Terminal with 3 panels
start "" "!WT_EXE!" ^
new-tab --title "EPAD Bot - ngrok" ^
-d "%SCRIPT_DIR%" ^
pwsh -NoExit -Command "ngrok http 8100" ^
; split-pane -H --size 0.7 --title "EPAD Bot - Server" ^
-d "%SCRIPT_DIR%" ^
pwsh -NoExit -Command "uv run epad-bot" ^
; split-pane -V --size 0.7 --title "EPAD Bot - CodeBuddy" ^
-d "%SCRIPT_DIR%" ^
pwsh -NoExit -File "%SCRIPT_DIR%\start-codebuddy.ps1"

echo.
echo [OK] Windows Terminal launched
echo.
echo This window will close in 3 seconds...

timeout /t 3 /nobreak > nul
