@echo off
cd /d "%~dp0"
set PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  "%PY%" -m venv .venv
  if errorlevel 1 (
    echo Python not found. Install Python 3.12 first.
    pause
    exit /b 1
  )
  .venv\Scripts\python.exe -m pip install -r requirements.txt
)

echo Starting Expense Tracker at http://127.0.0.1:5000
start "" "http://127.0.0.1:5000"
.venv\Scripts\python.exe app.py
pause
