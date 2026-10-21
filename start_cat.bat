@echo off
title CAT Launcher

echo ========================================
echo       Starting CAT (Taskmate)
echo ========================================
echo.

echo [1/2] Launching Backend (Uvicorn Server)...
start "CAT Backend" cmd /k "cd /d %~dp0 && call conda activate CAT 2>nul || call C:\anaconda\Scripts\activate.bat CAT 2>nul && python -m uvicorn services.gateway.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Launching Frontend (Tauri Desktop App)...
start "CAT Frontend" cmd /k "cd /d %~dp0\apps\desktop && npm run tauri dev"

echo.
echo Both services have been successfully launched in new windows!
echo You can close this window now.
pause
