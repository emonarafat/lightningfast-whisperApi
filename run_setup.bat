@echo off
title Python Env Setup Launcher

:MENU
cls
echo =============================================
echo         Python Env Setup Launcher
echo =============================================
echo.
echo   [1] Run setup_env.py
echo   [2] Activate virtual environment (PowerShell)
echo   [3] Activate venv and start Whisper API server
echo   [0] Exit
echo.
set /p choice=Enter your choice (0-3): 

if "%choice%"=="1" goto RUN_SETUP
if "%choice%"=="2" goto ACTIVATE_POWERSHELL
if "%choice%"=="3" goto RUN_API_SERVER
if "%choice%"=="0" exit
goto MENU

:RUN_SETUP
echo.
echo Running setup_env.py...
python setup_env.py
pause
goto MENU

:ACTIVATE_POWERSHELL
echo.
echo Activating virtual environment using PowerShell...
start powershell -NoExit -ExecutionPolicy Bypass -Command ".\activate_venv.ps1"
goto MENU

:RUN_API_SERVER
echo.
echo Activating venv and starting Whisper API...
start powershell -NoExit -ExecutionPolicy Bypass -Command ".\activate_venv.ps1; python -m uvicorn main:app -reload --host 0.0.0.0 --port 8000 --lifespan off; Start-Process http://localhost:8000/docs"
goto MENU
