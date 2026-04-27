@echo off
echo Testing Windows Terminal launch...
echo.

REM Set script directory
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Find Windows Terminal
set "WT_EXE="
for /f "tokens=*" %%i in ('where wt.exe 2^>nul') do (
    set "WT_EXE=%%i"
    goto :found
)

if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\wt.exe" (
    set "WT_EXE=%LOCALAPPDATA%\Microsoft\WindowsApps\wt.exe"
    goto :found
)

echo [ERROR] Windows Terminal not found!
pause
exit /b 1

:found
echo Windows Terminal found: !WT_EXE!
echo Working directory: %SCRIPT_DIR%
echo.
echo Press any key to launch Windows Terminal with 3 panels...
pause

start "" "!WT_EXE!" ^
new-tab --title "EPAD Bot - ngrok" ^
-d "%SCRIPT_DIR%" ^
pwsh -NoExit -Command "ngrok http 8100" ^
; split-pane -H --size 0.5 --title "EPAD Bot - Server" ^
-d "%SCRIPT_DIR%" ^
pwsh -NoExit -Command "uv run epad-bot" ^
; split-pane -V --size 0.6 --title "EPAD Bot - CodeBuddy" ^
-d "%SCRIPT_DIR%" ^
pwsh -NoExit -Command "codebuddy"

echo.
echo Windows Terminal command executed.
echo Please check if a new window appeared.
echo.
pause
