@echo off
setlocal enabledelayedexpansion
title JARVIS Mark-XXX Launcher
cd /d "%~dp0"

REM Find Python executable
if exist ".venv\Scripts\python.exe" (
    set PY=.venv\Scripts\python.exe
) else (
    REM Use python.exe explicitly (not the Store app alias)
    set PY=python.exe
)

echo [INFO] JARVIS Mark-XXX Launcher
echo [INFO] ========================================
echo.

REM Create logs directory
if not exist "logs" mkdir logs
if not exist "logs\runtime" mkdir logs\runtime

REM Check Ollama
echo [1/3] Checking Ollama...
ollama list >nul 2>&1
if errorlevel 1 (
    echo [WARN] Ollama not found or not running
    echo [INFO] Install from: https://ollama.ai
    echo [INFO] Or start it manually with: ollama serve
    echo.
) else (
    echo [OK] Ollama is running
)

REM Install/update Python packages
echo [2/3] Installing Python dependencies...
%PY% -m pip install -q fastapi uvicorn pydantic python-dotenv requests aiohttp pyautogui pillow psutil pyttsx3 google-genai playwright ddgs pyperclip mss feedparser wikipedia-api
if errorlevel 1 (
    echo [ERROR] Failed to install Python packages - re-running without -q to show errors:
    %PY% -m pip install fastapi uvicorn pydantic python-dotenv requests aiohttp pyautogui pillow psutil pyttsx3 google-genai playwright ddgs pyperclip mss feedparser wikipedia-api
    goto error
)
echo [OK] Dependencies installed

REM Install Playwright browsers
echo [3/3] Setting up Playwright...
%PY% -m playwright install chromium >nul 2>&1

echo.
echo [INFO] ========================================
echo [INFO] Starting JARVIS through launcher_bootstrap.py...
echo.
echo Open in browser:  http://127.0.0.1:8001/
echo API docs:         http://127.0.0.1:8001/docs
echo.

REM Launch through the bootstrapper so port reclaim, health checks,
REM and the shared backend-served UI follow the canonical startup path.
%PY% launcher_bootstrap.py
if errorlevel 1 (
    echo [ERROR] Backend failed to start
    echo [INFO] Check logs\runtime\
    pause
    exit /b 1
)

exit /b 0

:error
echo [ERROR] Setup failed
pause
exit /b 1
