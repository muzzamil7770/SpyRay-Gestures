@echo off
title SPyRaw Gestures Engine
cd /d "%~dp0"

REM ── Option 1: Launch compiled EXE (no Python needed, fastest) ──────────────
IF EXIST "dist\SPyRawGestures.exe" (
    echo [SPyRaw] Starting compiled executable...
    start "" "dist\SPyRawGestures.exe"
    exit /b 0
)

REM ── Option 2: Run from source using global Python 3.14 ────────────────────
echo [SPyRaw] EXE not found - launching from source...
IF EXIST "C:\Python314\python.exe" (
    C:\Python314\python.exe src\main.py 2>NUL
    goto :done
)

REM ── Option 3: Fallback to whatever 'python' resolves to ──────────────────
python src\main.py 2>NUL

:done
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] The application crashed. Please check the error above.
    pause
)
