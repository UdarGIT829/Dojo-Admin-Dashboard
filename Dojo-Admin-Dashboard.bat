@echo off
SETLOCAL ENABLEDELAYEDEXPANSION
cd /d %~dp0

:: Git update
IF EXIST ".git" (
    echo Checking for updates...
    git pull >nul 2>&1
)
:: Create virtual environment if it doesn't exist
IF NOT EXIST ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

:: Activate the virtual environment
call .venv\Scripts\activate.bat

:: Install dependencies
echo Installing Python packages...
pip install -r requirements.txt

:: Run the application
echo Launching Attendance Manager...
python ui_test.py

pause
