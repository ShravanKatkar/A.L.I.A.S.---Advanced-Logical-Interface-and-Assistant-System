@echo off
title ALIAS Launcher
color 0b

echo ==================================================
echo       LAUNCHING ALIAS - AI DESKTOP ASSISTANT
echo ==================================================

:: 0. Cleanup Old Processes
echo [0/2] Cleaning up old processes...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM electron.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1

:: 1. Start Backend (Hidden/Minimized)
echo [1/2] Awakening the Brain (Python Backend)...
start "ALIAS Brain" /min cmd /k "cd backend && venv\Scripts\activate && python main.py"

:: 2. Wait for Backend
echo       Waiting for brain to initialize...
timeout /t 5 /nobreak >nul

:: 3. Start Frontend
:: 3. Start Frontend (Electron App)
echo [2/2] Opening Interface (Electron)...
cd frontend
call npm run electron:dev

echo Closing Launcher...
exit
