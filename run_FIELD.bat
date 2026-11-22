@echo off
cd /d "%~dp0"
python main.py
if errorlevel 1 (
  echo.
  echo FIELD exited with an error. Check the Python output above.
  pause
)
