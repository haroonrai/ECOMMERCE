@echo off
title AURA Healthcare - Public Online Store Launcher
color 0B
echo ========================================================
echo   AURA HEALTHCARE & CLINICAL DERMA LABS
echo   Public Online Store Launcher (Cloudflare Tunnel)
echo ========================================================
echo.

cd /d "%~dp0"

:: 1. Ensure local server is running
netstat -ano | findstr ":5000" | findstr "LISTENING" >nul
if %errorlevel% neq 0 (
    echo [1/2] Starting local store server...
    start /b py app.py
    timeout /t 3 /nobreak >nul
) else (
    echo [1/2] Local store server is already running on port 5000.
)

:: 2. Launch Cloudflare Tunnel
echo [2/2] Generating secure public internet link...
echo.
py tunnel.py
pause
