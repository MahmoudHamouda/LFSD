# Startup Script for LFSD (Windows)

Write-Host "Starting LFSD Environment..." -ForegroundColor Cyan

# 1. Start Backend
Write-Host "Launching Backend (Port 8003)..." -ForegroundColor Green
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "python backend/app.py" 

# 2. Start Frontend
Write-Host "Launching Frontend (Port 3000)..." -ForegroundColor Green
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "All services started!" -ForegroundColor Cyan
