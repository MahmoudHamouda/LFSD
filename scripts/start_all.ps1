# LFSD Application Startup Script
# Run this script to start all services (Redis, Backend, Frontend)

$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot
$ProjectRoot = Resolve-Path "$ScriptDir\.."

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "   LFSD Application Startup       " -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

# 1. Check Docker & Start Redis
Write-Host "`n[1/3] Checking Docker and Redis..." -ForegroundColor Yellow
try {
    $dockerInfo = docker info 2>&1 | Out-Null
    Write-Host "Docker is running." -ForegroundColor Green
    
    Write-Host "Starting Redis container..."
    Set-Location $ProjectRoot
    docker compose up -d redis
    Write-Host "Redis started." -ForegroundColor Green
} catch {
    Write-Host "WARNING: Docker is not running or not accessible." -ForegroundColor Red
    Write-Host "Skipping Redis startup. Check Docker Desktop if you need Redis." -ForegroundColor Gray
}

# 2. Start Backend
Write-Host "`n[2/3] Starting Backend Service..." -ForegroundColor Yellow
$BackendPath = "$ProjectRoot"
$BackendCommand = "cd '$BackendPath'; .\.venv\Scripts\activate; python -m uvicorn backend.app:create_app --factory --host 0.0.0.0 --port 8003 --reload"

try {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { $BackendCommand }"
    Write-Host "Backend launched in new window (Port 8003)." -ForegroundColor Green
} catch {
    Write-Host "Failed to start Backend: $_" -ForegroundColor Red
}

# 3. Start Frontend
Write-Host "`n[3/3] Starting Frontend Service..." -ForegroundColor Yellow
$FrontendPath = "$ProjectRoot\frontend"
$FrontendCommand = "cd '$FrontendPath'; npm run dev"

try {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { $FrontendCommand }"
    Write-Host "Frontend launched in new window (Port 3000)." -ForegroundColor Green
} catch {
    Write-Host "Failed to start Frontend: $_" -ForegroundColor Red
}

Write-Host "`n==================================" -ForegroundColor Cyan
Write-Host "   Startup Sequence Complete      " -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Backend URL: http://localhost:8003" -ForegroundColor Gray
Write-Host "Frontend URL: http://localhost:3000" -ForegroundColor Gray
Write-Host "`nPress any key to exit this launcher..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
