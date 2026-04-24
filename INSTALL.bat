@echo off
setlocal

echo ================================================
echo        JARVIS Mark-XXX - One Click Install
echo ================================================

python --version >nul 2>&1 || (
    echo [ERROR] Python install karo
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/7] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 exit /b 1
)

call .venv\Scripts\activate.bat

echo [2/7] Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 exit /b 1

echo [3/7] Installing Python dependencies...
python -m pip install -q -r requirements.txt
if errorlevel 1 exit /b 1

if not exist ".env" (
    echo [4/7] Creating local .env from template...
    copy .env.example .env >nul
) else (
    echo [4/7] .env already exists
)

echo [5/7] Running hardware scan...
python Core\hardware_scanner.py
if errorlevel 1 exit /b 1

echo [6/7] Installing frontend dependencies...
pushd Interface\web
call npm install
if errorlevel 1 (
    popd
    exit /b 1
)
popd

echo [7/7] Installing Playwright Chromium...
python -m playwright install chromium
if errorlevel 1 exit /b 1

echo.
echo [DONE] Setup complete! START_JARVIS.bat chalao.
pause
