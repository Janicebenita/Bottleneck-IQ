@echo off
setlocal
cd /d "%~dp0"
title Bottleneck IQ
set "BOTTLENECK_IQ_OPEN_BROWSER=1"

if exist ".venv\Scripts\python.exe" goto run

where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 -m venv .venv
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python 3.11 or newer is required. Install Python, then run this launcher again.
    pause
    exit /b 1
  )
  python -m venv .venv
)

if errorlevel 1 (
  echo.
  echo Bottleneck IQ could not create its isolated Python environment.
  pause
  exit /b 1
)

:run
".venv\Scripts\python.exe" scripts\ensure_dependencies.py

if errorlevel 1 (
  echo.
  echo Bottleneck IQ could not start. Review the error above.
  pause
  exit /b 1
)
