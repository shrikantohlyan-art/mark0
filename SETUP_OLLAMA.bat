@echo off
chcp 65001 >nul
echo ==========================================
echo JARVIS Business Edition Setup
echo For Cyber Cafe + Meesho Store
echo ==========================================
echo.

REM Check if Ollama is installed
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    echo Ollama not found. Installing...
    powershell -Command "Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile '%TEMP%\OllamaSetup.exe'"
    start /wait %TEMP%\OllamaSetup.exe
    echo Please restart this script after Ollama installation completes.
    pause
    exit /b
)

echo [1/4] Starting Ollama...
start /b ollama serve >nul 2>nul

REM Wait for Ollama to start
timeout /t 3 /nobreak >nul

echo [2/4] Pulling optimized models...
echo This may take 10-30 minutes depending on your internet...
echo.

REM Pull smaller, faster models for business use
echo Pulling phi3 model (small and fast)...
ollama pull phi3:latest

echo Pulling qwen2.5 model (good for tasks)...
ollama pull qwen2.5:7b

echo [3/4] Verifying models...
ollama list

echo.
echo [4/4] Models ready!
echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Available Models:
echo   - phi3:latest (Fast, good for quick tasks)
echo   - qwen2.5:7b (Balanced speed/quality)
echo.
echo Press any key to exit...
pause >nul
