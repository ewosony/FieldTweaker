@echo off
setlocal
cd /d "%~dp0"

echo [FIELD 1.2] Checking source files...
python -m py_compile main.py personal_lite\field_ui.py personal_lite\app_installer.py personal_lite\advanced_settings.py personal_lite\advanced_core.py personal_lite\dashboard_page.py personal_lite\cleaner_core.py personal_lite\cleaner_page.py personal_lite\power_core.py personal_lite\power_page.py
if errorlevel 1 (
  echo [ERROR] Python syntax check failed.
  pause
  exit /b 1
)

if not exist "assets\field.ico" (
  echo [ERROR] assets\field.ico is missing.
  pause
  exit /b 1
)

echo [FIELD 1.2] Preparing app logos (downloads remaining icons, internet optional)...
python download_app_icons.py --bundle
if errorlevel 1 (
  echo [WARN] Some logos could not be downloaded. Included icon fallbacks will be used.
)

echo [FIELD 1.2] Building a portable one-file EXE...
python -m PyInstaller --noconfirm --clean --onefile --windowed --noupx --name "FIELD 1.2" --icon "%CD%\assets\field.ico" --add-data "%CD%\assets;assets" main.py
if errorlevel 1 (
  echo [ERROR] Build failed. Scroll up to see the error.
  pause
  exit /b 1
)

echo.
echo [OK] Build finished: dist\FIELD 1.2.exe
pause
