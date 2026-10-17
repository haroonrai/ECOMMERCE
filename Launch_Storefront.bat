@echo off
title AURA Healthcare Store Launcher
cd /d "%~dp0"

:: Check if server is already running on port 5000
netstat -ano | findstr ":5000" | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo [INFO] Store server is already running!
    echo Opening storefront in your browser...
    start "" "http://127.0.0.1:5000"
    exit /b 0
)

echo [INFO] Starting AURA Healthcare Server in background...
start /b py app.py >nul 2>&1

:: Wait 2 seconds for server startup
timeout /t 2 /nobreak >nul

echo [INFO] Opening storefront in your browser...
start "" "http://127.0.0.1:5000"
exit /b 0
