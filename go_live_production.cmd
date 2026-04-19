@echo off
setlocal

REM Production go-live launcher for 100-Day Execution Dashboard
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo ERROR: Python virtual environment not found at .venv\Scripts\python.exe
  echo Create it first and install requirements.
  exit /b 1
)

echo Running production preflight checks...
".venv\Scripts\python.exe" go_live_preflight.py
if errorlevel 1 (
  echo.
  echo GO-LIVE BLOCKED: Fix the FAILED checks above before production launch.
  exit /b 1
)

echo.
echo Starting production dashboard...
".venv\Scripts\python.exe" -m streamlit run streamlit_app.py --server.headless true --browser.gatherUsageStats false

endlocal
