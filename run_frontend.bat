@echo off
echo ===================================================
echo           Starting SwarmMind Frontend Client
echo ===================================================
cd /d "%~dp0frontend"
echo [INFO] Launching Vite Dev Server on http://localhost:5173
npm run dev
pause
