$ErrorActionPreference = "Continue"

Write-Host "=== COMPREHENSIVE FINANCE DASHBOARD TEST ===" -ForegroundColor Cyan
Write-Host ""

# 1. Test Login
Write-Host "1. Testing Login..." -ForegroundColor Yellow
try {
    $loginResponse = Invoke-RestMethod -Uri "https://lfsd-backend-692544481281.us-central1.run.app/api/auth/login" `
        -Method Post -ContentType "application/json" `
        -Body '{"username": "finance@helm.com", "email": "finance@helm.com", "password": "P@ssword123"}'
    
    $token = $loginResponse.access_token
    Write-Host "   ✅ Login successful" -ForegroundColor Green
    Write-Host "   Token: $($token.Substring(0, 20))..." -ForegroundColor Gray
}
catch {
    Write-Host "   ❌ Login failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 2. Test Scores Endpoint (what the dashboard uses)
Write-Host "2. Testing /api/scores/current..." -ForegroundColor Yellow
try {
    $scores = Invoke-RestMethod -Uri "https://lfsd-backend-692544481281.us-central1.run.app/api/scores/current" `
        -Headers @{Authorization = ("Bearer " + $token) }
    
    Write-Host "   Overall Score: $($scores.overall_score)" -ForegroundColor Green
    Write-Host "   Financial Score: $($scores.breakdown.financial.score)" -ForegroundColor Green
    Write-Host "   Financial Subscores:" -ForegroundColor Green
    if ($scores.breakdown.financial.subscores) {
        $scores.breakdown.financial.subscores.PSObject.Properties | ForEach-Object {
            Write-Host "     - $($_.Name): $($_.Value)" -ForegroundColor White
        }
    }
    else {
        Write-Host "     ⚠️  No subscores found" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "   ❌ Scores endpoint failed: $_" -ForegroundColor Red
}

Write-Host ""

# 3. Test Transactions Endpoint
Write-Host "3. Testing /api/finance/transactions..." -ForegroundColor Yellow
try {
    $tx = Invoke-RestMethod -Uri "https://lfsd-backend-692544481281.us-central1.run.app/api/finance/transactions?limit=5" `
        -Headers @{Authorization = ("Bearer " + $token) }
    
    Write-Host "   Transactions returned: $($tx.data.Count)" -ForegroundColor Green
    if ($tx.data.Count -gt 0) {
        Write-Host "   Sample transactions:" -ForegroundColor Green
        $tx.data | Select-Object -First 3 | ForEach-Object {
            Write-Host "     - $($_.merchant): `$$($_.amount) on $($_.date)" -ForegroundColor White
        }
    }
    else {
        Write-Host "   ⚠️  No transactions returned" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "   ❌ Transactions endpoint failed: $_" -ForegroundColor Red
}

Write-Host ""

# 4. Test Coverage Endpoint
Write-Host "4. Testing /api/finance/categories/cashflow_stability/coverage..." -ForegroundColor Yellow
try {
    $cov = Invoke-RestMethod -Uri "https://lfsd-backend-692544481281.us-central1.run.app/api/finance/categories/cashflow_stability/coverage" `
        -Headers @{Authorization = ("Bearer " + $token) }
    
    Write-Host "   Days with data: $($cov.days_with_data)" -ForegroundColor Green
    Write-Host "   Required days: $($cov.required_days)" -ForegroundColor Green
    Write-Host "   Chart unlocked: $($cov.chart_unlocked)" -ForegroundColor $(if ($cov.chart_unlocked) { "Green" } else { "Red" })
}
catch {
    Write-Host "   ❌ Coverage endpoint failed: $_" -ForegroundColor Red
}

Write-Host ""

# 5. Check Frontend Directly
Write-Host "5. Testing Frontend Page Load..." -ForegroundColor Yellow
try {
    $frontendResponse = Invoke-WebRequest -Uri "https://lfsd-frontend-692544481281.us-central1.run.app/finance" -UseBasicParsing
    Write-Host "   Frontend status: $($frontendResponse.StatusCode)" -ForegroundColor Green
    Write-Host "   Content length: $($frontendResponse.Content.Length) bytes" -ForegroundColor Green
}
catch {
    Write-Host "   ⚠️  Frontend request failed: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== TEST COMPLETE ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "DIAGNOSIS:" -ForegroundColor Yellow
Write-Host "If API endpoints return data but UI shows nothing, possible causes:" -ForegroundColor White
Write-Host "  1. Frontend caching - try hard refresh (Ctrl+Shift+R)" -ForegroundColor White
Write-Host "  2. Token not being sent from frontend" -ForegroundColor White
Write-Host "  3. Frontend expecting different field names" -ForegroundColor White
Write-Host "  4. CORS or authentication issues" -ForegroundColor White
