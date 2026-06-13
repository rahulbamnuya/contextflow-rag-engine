@echo off
:: ==============================================================================
:: Windows Development & Setup Automation Script for ContextFlow RAG Engine v2.0
:: ==============================================================================
title ContextFlow RAG Engine Setup Tool

:menu
cls
echo =====================================================================
echo           ContextFlow RAG Engine v2.0 - Automation Tool
echo =====================================================================
echo [1] Setup environment (Create venv and install dependencies)
echo [2] Run Pytest suite
echo [3] Start RAG FastAPI Backend (Port 8000)
echo [4] Start RAG Streamlit Frontend (Port 8501)
echo [5] Start entire stack via Docker Compose
echo [6] Stop Docker Compose services
echo [7] Exit
echo =====================================================================
set /p choice="Enter choice [1-7]: "

if "%choice%"=="1" goto setup
if "%choice%"=="2" goto test
if "%choice%"=="3" goto backend
if "%choice%"=="4" goto frontend
if "%choice%"=="5" goto docker_up
if "%choice%"=="6" goto docker_down
if "%choice%"=="7" goto end
goto menu

:setup
echo.
echo [1/3] Creating virtual environment (.venv)...
python -m venv .venv
if errorlevel 1 (
    echo Error creating virtual environment. Make sure python is installed.
    pause
    goto menu
)
echo [2/3] Activating virtual environment...
call .venv\Scripts\activate.bat
echo [3/3] Installing dependencies from requirements.txt...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo Setup completed successfully!
pause
goto menu

:test
echo.
echo Running unit and integration tests using PyTest...
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)
pytest
pause
goto menu

:backend
echo.
echo Starting FastAPI Backend on http://localhost:8000 ...
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
pause
goto menu

:frontend
echo.
echo Starting Streamlit Frontend on http://localhost:8501 ...
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)
streamlit run streamlit_app/home.py
pause
goto menu

:docker_up
echo.
echo Running docker compose up --build...
docker compose up --build -d
echo Services started in background.
echo Backend: http://localhost:8000/docs
echo Frontend: http://localhost:8501
pause
goto menu

:docker_down
echo.
echo Running docker compose down...
docker compose down
pause
goto menu

:end
echo Goodbye!
exit
