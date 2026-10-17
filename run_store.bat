@echo off
title AURA Healthcare & Derma Labs E-Commerce Server
color 0A
echo ========================================================
echo   AURA HEALTHCARE & CLINICAL DERMA LABS
echo   Luxury E-Commerce Platform - Local Server
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/3] Checking Python installation...
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not detected! Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

echo [2/3] Verifying dependencies...
py -c "import flask, waitress, whitenoise" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing required dependencies...
    py -m pip install -r requirements.txt
)

echo [3/3] Starting Storefront Server on http://127.0.0.1:5000 ...
echo.
echo ========================================================
echo   STOREFRONT:  http://127.0.0.1:5000
echo   ADMIN LOGIN: http://127.0.0.1:5000/auth
echo   ADMIN EMAIL: admin@store.com
echo   ADMIN PASS:  admin123
echo ========================================================
echo.
echo Opening browser in 2 seconds...
start /b cmd /c "timeout /t 2 >nul & start http://127.0.0.1:5000"

set HOST=0.0.0.0
py app.py
pause
