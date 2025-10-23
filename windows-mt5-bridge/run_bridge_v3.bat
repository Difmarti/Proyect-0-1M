@echo off
REM MT5 Bridge V3 Launcher
REM Run this script to start the modular trading bridge

echo ============================================================
echo MT5 Bridge V3 - Modular Architecture
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ and add to PATH
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Creating...
    python -m venv venv
    call venv\Scripts\activate
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

REM Check if .env exists
if not exist ".env" (
    echo ERROR: .env file not found
    echo Please copy .env.example to .env and configure
    pause
    exit /b 1
)

echo Starting MT5 Bridge V3...
echo.

REM Run the bridge
python -m bridge_v3.main

REM If it exits, pause to see error messages
pause
