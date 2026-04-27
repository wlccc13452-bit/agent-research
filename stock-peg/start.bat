@echo off
chcp 65001 > nul
echo Starting Stock PEG...
wt -d "%~dp0backend" cmd /k "uv run uvicorn main:app --host 0.0.0.0 --port 8000" ; split-pane -V -s 0.4 -d "%~dp0frontend" powershell -NoExit -Command "npm run dev"
echo Done!
