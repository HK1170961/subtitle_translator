@echo off
title Subtitle Translator

echo ========================================
echo    Subtitle Translator
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found, please install Python 3.8+
    pause
    exit /b 1
)

REM Install dependencies
echo Checking dependencies...
pip install -q PyQt6 requests chardet faster-whisper 2>nul

REM Start application
echo Starting Subtitle Translator...
python -m subtitle_translator.main

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to start
    pause
)
