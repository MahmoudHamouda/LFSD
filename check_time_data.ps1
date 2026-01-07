$token = (Invoke-RestMethod -Uri "https://lfsd-backend-692544481281.us-central1.run.app/api/auth/login" -Method Post -ContentType "application/json" -Body '{"username": "time@helm.com", "email": "time@helm.com", "password": "P@ssword123"}').access_token

Write-Host "=== CHECKING TIME USER DATA ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check scores endpoint
Write-Host "1. Checking /api/scores/current..." -ForegroundColor Yellow
try {
    $scores = Invoke-RestMethod -Uri "https://lfsd-backend-692544481281.us-central1.run.app/api/scores/current" -Headers @{Authorization = ("Bearer " + $token) }
    
    Write-Host "   Productivity Score: $($scores.productivity_score)" -ForegroundColor Green
    Write-Host "   Categories:" -ForegroundColor Yellow
    if ($scores.categories) {
        $scores.categories | ConvertTo-Json -Depth 3
    }
    else {
        Write-Host "   ❌ NO CATEGORIES" -ForegroundColor Red
    }
}
catch {
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red
}

Write-Host ""

# 2. Check calendar events
Write-Host "2. Checking /api/time/events..." -ForegroundColor Yellow
try {
    $events = Invoke-RestMethod -Uri "https://lfsd-backend-692544481281.us-central1.run.app/api/time/events" -Headers @{Authorization = ("Bearer " + $token) }
    
    Write-Host "   Events returned: $($events.data.Count)" -ForegroundColor Green
    if ($events.data.Count -gt 0) {
        Write-Host "   Sample events:" -ForegroundColor Green
        $events.data | Select-Object -First 3 | ForEach-Object {
            Write-Host "     - $($_.title): $($_.start_time)" -ForegroundColor White
        }
    }
    else {
        Write-Host "   ⚠️  No events returned" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== TEST COMPLETE ===" -ForegroundColor Cyan
