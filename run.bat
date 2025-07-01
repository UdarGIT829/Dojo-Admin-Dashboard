@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

:: Create virtual environment if it doesn't exist
IF NOT EXIST ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

:: Activate the virtual environment
call .venv\Scripts\activate.bat

:: Install dependencies
echo Installing Python packages...
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

:: Run the application
echo Launching Attendance Manager...
python ui_test.py

pause
