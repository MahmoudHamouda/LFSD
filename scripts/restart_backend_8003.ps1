# Restart LFSD Backend on 8003 with Reload
$port = 8003
Write-Host "Stopping backend on port $port..." -ForegroundColor Yellow

$connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($connections) {
    $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($proc_id in $pids) {
        Write-Host "Killing process $proc_id" -ForegroundColor Red
        Stop-Process -Id $proc_id -Force
    }
    Start-Sleep -Seconds 2
}

Write-Host "Starting backend on port $port with --reload..." -ForegroundColor Green
$location = Get-Location
$command = "python -m uvicorn backend.app:create_app --factory --host 0.0.0.0 --port $port --reload"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$location'; $command"

Write-Host "Restart complete. Waiting for startup..."
Start-Sleep -Seconds 5
