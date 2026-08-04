@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [1/3] Creating virtual environment...
  where py >nul 2>&1 && (
    py -3 -m venv .venv
  ) || (
    python -m venv .venv
  )
  if errorlevel 1 (
    echo Failed to create venv. Please install Python 3.10+ and retry.
    pause
    exit /b 1
  )
  echo [2/3] Installing dependencies...
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

if not exist ".env" copy /Y ".env.example" ".env" >nul

echo [3/3] Starting CorpLens...
".venv\Scripts\python.exe" -m streamlit run app.py --client.toolbarMode=minimal
pause
