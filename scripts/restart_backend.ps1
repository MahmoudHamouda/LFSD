# Restart LFSD Backend - Simple Version

Write-Host "Stopping old backend on port 8002..." -ForegroundColor Yellow

# Find and kill process on port 8002
$connections = Get-NetTCPConnection -LocalPort 8002 -ErrorAction SilentlyContinue
if ($connections) {
    $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($pid in $pids) {
        Write-Host "Killing process $pid" -ForegroundColor Red
        Stop-Process -Id $pid -Force
    }
    Start-Sleep -Seconds 2
}

Write-Host "Starting new backend..." -ForegroundColor Green
Start-Sleep -Seconds 1

# Start backend in new window
$location = Get-Location
Start-Process powershell -ArgumentList "-NoExit -Command cd '$location'; python -m uvicorn app:create_app --factory --host 0.0.0.0 --port 8002"

Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

Write-Host "Testing endpoints..." -ForegroundColor Cyan
try {
    $result = Invoke-RestMethod -Uri "http://localhost:8002/mobility/providers"
    Write-Host "SUCCESS! Providers:" $result.providers -ForegroundColor Green
} catch {
    Write-Host "Backend still starting, try: python test_e2e_mobility.py" -ForegroundColor Yellow
}
