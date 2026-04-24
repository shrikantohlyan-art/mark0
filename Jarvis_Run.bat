@echo off
cd /d "%~dp0"
setlocal

if exist "%CD%\.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%CD%\.venv\Scripts\python.exe"
) else (
    set "PYTHON_CMD=python"
)

echo Starting Jarvis through launcher_bootstrap.py...
"%PYTHON_CMD%" launcher_bootstrap.py
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo Launcher failed with exit code %EXIT_CODE%.
    pause
)

exit /b %EXIT_CODE%
