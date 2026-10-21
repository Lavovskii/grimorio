@echo off
cd /d "%~dp0"
title Tibia Questski

rem Python if installed (python or the py launcher), otherwise the PowerShell server that comes with Windows
python --version >nul 2>&1
if not errorlevel 1 (
  start "" http://localhost:8080
  python serve.py 8080
  goto :eof
)
py -3 --version >nul 2>&1
if not errorlevel 1 (
  start "" http://localhost:8080
  py -3 serve.py 8080
  goto :eof
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0serve.ps1" -Port 8080
pause
