@echo off
title Electron Build Automator
cd /d "%~dp0"

:: Set environment variables
set "UV_SYSTEM_CERTS=true"
set "NODE_TLS_REJECT_UNAUTHORIZED=0"
set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\AppData\Local\Microsoft\WinGet\Packages\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.19.0-win-x64;%PATH%"

echo ==========================================
echo   ELECTRON STANDALONE BUILD SCRIPT
echo ==========================================
echo.

echo [1/3] Compiling Python Flask backend with PyInstaller...
echo [!] (This bundles the web assets directly inside the executable to prevent 404 errors)
echo.
uv run --with pyinstaller --with-requirements requirements.txt pyinstaller --clean --onefile --noconsole --add-data "web;web" --name "SteamTools_Auto_Backend" app.py
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
echo [3/3] Packaging Electron standalone application...
npx.cmd electron-packager . SteaMRogue --platform=win32 --arch=x64 --overwrite --extra-resource=SteamTools_Auto_Backend.exe
if %errorlevel% neq 0 (
    echo [x] Electron packaging failed!
    pause
    exit /b %errorlevel%
)

echo.
echo ==========================================
echo   BUILD COMPLETED SUCCESSFULLY!
echo ==========================================
echo Standalone folder: SteaMRogue-win32-x64
echo.
pause
