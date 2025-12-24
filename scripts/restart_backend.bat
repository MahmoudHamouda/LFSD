@echo off
echo ========================================
echo  Restarting LFSD Backend
echo ========================================
echo.

echo Step 1: Finding and stopping old backend process...
echo.

REM Kill any Python processes running uvicorn on port 8002
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8002 ^| findstr LISTENING') do (
    echo Found process using port 8002: %%a
    taskkill /F /PID %%a
)

echo.
echo Waiting 3 seconds for port to be released...
timeout /t 3 /nobreak >nul

echo.
echo Step 2: Starting backend with mobility routes...
echo.

REM Start the backend in a new window
start "LFSD Backend - Port 8002" cmd /k "cd /d %~dp0 && python -m uvicorn app:create_app --factory --host 0.0.0.0 --port 8002"

echo.
echo Waiting 5 seconds for backend to initialize...
timeout /t 5 /nobreak >nul

echo.
echo Step 3: Testing mobility endpoints...
echo.

curl http://localhost:8002/mobility/providers

echo.
echo.
echo ========================================
echo  Backend Restart Complete!
echo ========================================
echo.
echo The backend is now running with mobility routes.
echo.
echo Test it:
echo   python test_e2e_mobility.py
echo.
pause
