@echo off
title SteaMRogue Installer Builder
cd /d "%~dp0"

:: Set environment variables
set "UV_SYSTEM_CERTS=1"
set "NODE_TLS_REJECT_UNAUTHORIZED=0"
set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\AppData\Local\Microsoft\WinGet\Packages\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.19.0-win-x64;%PATH%"

echo ==========================================
echo   1. BUILDING PYINSTALLER BACKEND
echo ==========================================
echo.
uv run --with pyinstaller --with-requirements requirements.txt pyinstaller --clean --onefile --noconsole --icon "icon.ico" --version-file "version_info.txt" --manifest "app.manifest" --add-data "web;web" --add-data "app_names_cache.json;." --add-data "steamtools_files;steamtools_files" --name "SteamTools_Auto_Backend" app.py
if %errorlevel% neq 0 (
    echo [x] Backend compilation failed!
    pause
    exit /b %errorlevel%
)

echo.
echo [2/3] Moving backend executable to root directory...
copy /Y "dist\SteamTools_Auto_Backend.exe" "SteamTools_Auto_Backend.exe"
if %errorlevel% neq 0 (
    echo [x] Failed to copy SteamTools_Auto_Backend.exe to root!
    pause
    exit /b %errorlevel%
)

echo.
echo ==========================================
echo   2. BUILDING SINGLE EXE INSTALLER (NSIS)
echo ==========================================
echo.
npx.cmd electron-builder --win --x64
if %errorlevel% neq 0 (
    echo [x] Installer compilation failed!
    pause
    exit /b %errorlevel%
)

echo.
echo ==========================================
echo   BUILD COMPLETED SUCCESSFULLY!
echo ==========================================
echo Single Setup Executable is located in the "dist" directory!
echo File: dist\SteaMRogue Setup 1.0.0.exe
echo.
pause
