#!/bin/bash

cd "$(dirname "$0")"  # Ensure script runs from its own folder

if [ -d ".git" ]; then
  echo "Checking for updates..."
  git pull --quiet
fi

# Create virtual environment if needed
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

# Activate the environment
source .venv/bin/activate

# Install requirements
echo "Installing Python packages..."
pip install -r requirements.txt

# Run the app
echo "Launching Attendance Manager..."
python ui_test.py
