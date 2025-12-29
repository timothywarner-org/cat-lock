@echo off
REM PawGate Build Script for Windows
REM This script builds a local executable that won't be blocked by SmartScreen

echo ========================================
echo PawGate Build Script
echo ========================================
echo.

REM Remove user config so builds always start from bundled defaults
set "CONFIG_FILE=%USERPROFILE%\.pawgate\config\config.json"
if exist "%CONFIG_FILE%" (
    del /f /q "%CONFIG_FILE%"
    echo Removed user config at %CONFIG_FILE%
) else (
    echo No user config to remove at %CONFIG_FILE%
)

REM Use venv if it exists, otherwise use system Python
if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
    echo Using virtual environment Python
) else (
    set "PYTHON=python"
    echo Using system Python
)

REM Check if Python is available
"%PYTHON%" --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python or create a venv first:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
"%PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/3] Installing PyInstaller...
"%PYTHON%" -m pip install pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)

echo.
echo [3/3] Building PawGate executable...
"%PYTHON%" -m PyInstaller --onefile ^
    --distpath="./dist" ^
    --workpath="./build" ^
    --add-data="./resources/img/icon.ico;./resources/img/" ^
    --add-data="./resources/img/icon.png;./resources/img/" ^
    --add-data="./resources/config/config.json;./resources/config/" ^
    --icon="./resources/img/icon.ico" ^
    --hidden-import plyer.platforms.win.notification ^
    --noconsole ^
    --name="PawGate" ^
    "./src/main.py"

if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo BUILD SUCCESSFUL!
echo ========================================
echo.
echo Your executable is located at:
echo   dist\PawGate.exe
echo.
echo TIP: If Windows Defender flags it, add the dist folder
echo      to your exclusions list in Windows Security.
echo.
pause
