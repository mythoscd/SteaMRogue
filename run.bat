@echo off
title SteamTools Auto Game Adder v2.0
echo ==========================================
echo   STEAMTOOLS AUTO BASLATICISI
echo ==========================================
echo.

:: Ensure working directory is the script folder
cd /d "%~dp0"

:: Set environment variables
set "UV_SYSTEM_CERTS=true"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"

:: Verify if uv is available
where uv >nul 2>nul
if %errorlevel% equ 0 goto start_app

echo [!] uv (Python Paket Yoneticisi) bulunamadi.
echo [*] uv otomatik olarak yukleniyor, lutfen bekleyin...
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
echo.

:start_app
echo [*] Gerekli paketler kuruluyor ve uygulama baslatiliyor...
echo [*] (Ilk acilista paketlerin yuklenmesi birkac saniye surebilir)
echo.
uv run --with-requirements requirements.txt python app.py
if %errorlevel% neq 0 (
    echo.
    echo [x] Uygulama baslatilamadigi veya kapandigi icin hata olustu.
    pause
)
