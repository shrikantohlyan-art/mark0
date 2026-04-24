@echo off
chcp 65001 >nul
title JARVIS Business Edition - Cyber Cafe + Meesho Store
cls

echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║     🤖 JARVIS Business Edition                               ║
echo ║        Cyber Cafe + Meesho Store Assistant                   ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Check virtual environment
if not exist ".venv\Scripts\python.exe" (
    echo ❌ Virtual environment not found!
    echo Please run INSTALL.bat first.
    pause
    exit /b 1
)

echo [1/5] ✅ Virtual environment found

REM Check Ollama
python -c "import requests; requests.get('http://localhost:11434/api/tags', timeout=2)" >nul 2>nul
if %errorlevel% neq 0 (
    echo [2/5] ⚠️  Ollama not running. Starting Ollama...
    start /b ollama serve >nul 2>nul
    timeout /t 3 /nobreak >nul
) else (
    echo [2/5] ✅ Ollama is running
)

echo [3/5] 🔄 Loading business tools...
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8

echo [4/5] 🚀 Starting JARVIS Business Edition...
echo.
echo 💡 Features loaded:
echo    • WhatsApp Automation
echo    • Social Media Manager
echo    • Cyber Cafe Booking System
echo    • Meesho Store Inventory
echo    • Invoice Generator
echo    • Customer Database
echo.
echo ===========================================
echo JARVIS will open in your browser shortly...
echo ===========================================
echo.

REM Start JARVIS with business configuration
.venv\Scripts\python.exe launcher_bootstrap.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Failed to start JARVIS
    echo Check logs/runtime/launcher_bootstrap.log for details
    pause
)
