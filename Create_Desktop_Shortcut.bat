@echo off
title Create Desktop Shortcut for AURA Store
cd /d "%~dp0"

set TARGET_SCRIPT=%~dp0Launch_Storefront.bat
set SHORTCUT_NAME=AURA Healthcare Store.lnk

powershell -ExecutionPolicy Bypass -File "%~dp0create_shortcut.ps1"

echo.
echo ========================================================
echo   [SUCCESS] Desktop Shortcut Created!
echo   Look on your Windows Desktop for: "AURA Healthcare Store"
echo   Double-clicking it will open your store anytime!
echo ========================================================
echo.
pause
