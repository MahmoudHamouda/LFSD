$token = (Invoke-RestMethod -Uri "https://lfsd-backend-692544481281.us-central1.run.app/api/auth/login" -Method Post -ContentType "application/json" -Body '{"username": "finance@helm.com", "email": "finance@helm.com", "password": "P@ssword123"}').access_token

Write-Host "=== TESTING FINANCE BACKEND ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Checking Transactions Endpoint..." -ForegroundColor Yellow
$tx = Invoke-RestMethod -Uri "https://lfsd-backend-692544481281.us-central1.run.app/api/finance/transactions?limit=3" -Headers @{Authorization = ("Bearer " + $token) }
Write-Host "   Transactions returned: $($tx.data.Count)" -ForegroundColor Green
if ($tx.data.Count -gt 0) {
    $first = $tx.data[0]
    Write-Host "   First transaction:" -ForegroundColor Green
    Write-Host "     - Merchant: $($first.merchant)" -ForegroundColor White
    Write-Host "     - Date: $($first.date)" -ForegroundColor White
    Write-Host "     - Amount: $($first.amount)" -ForegroundColor White
}

Write-Host ""
Write-Host "2. Checking Coverage/Unlock Status..." -ForegroundColor Yellow
$cov = Invoke-RestMethod -Uri "https://lfsd-backend-692544481281.us-central1.run.app/api/finance/categories/cashflow_stability/coverage" -Headers @{Authorization = ("Bearer " + $token) }
Write-Host "   Days with data: $($cov.days_with_data)" -ForegroundColor Green
Write-Host "   Required days: $($cov.required_days)" -ForegroundColor Green
Write-Host "   Chart unlocked: $($cov.chart_unlocked)" -ForegroundColor $(if ($cov.chart_unlocked) { "Green" } else { "Red" })

Write-Host ""
Write-Host "=== VERIFICATION COMPLETE ===" -ForegroundColor Cyan
