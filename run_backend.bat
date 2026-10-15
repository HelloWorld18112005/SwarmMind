@echo off
echo ===================================================
echo           Starting SwarmMind Backend Server
echo ===================================================
cd /d "%~dp0backend"
if not exist ".env" (
    echo [INFO] No backend/.env found. Creating from .env.example...
    copy .env.example .env
)
echo [INFO] Launching FastAPI with Uvicorn on http://127.0.0.1:8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
