@echo off
title SteamTools Auto Game Adder (Electron)
cd /d "%~dp0"

:: Set environment variables
set "UV_SYSTEM_CERTS=true"
set "NODE_TLS_REJECT_UNAUTHORIZED=0"
set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\AppData\Local\Microsoft\WinGet\Packages\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.19.0-win-x64;%PATH%"

echo ==========================================
echo   STEAMTOOLS AUTO (ELECTRON BASLATICISI)
echo ==========================================
echo.
echo [*] Arka plan Flask sunucusu ve Electron baslatiliyor...
echo [*] Lutfen bekleyin...
echo.

npx electron .
if %errorlevel% neq 0 (
    echo.
    echo [x] Uygulama baslatilamadigi veya kapandigi icin hata olustu.
    pause
)
