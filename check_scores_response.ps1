$token = (Invoke-RestMethod -Uri "https://lfsd-backend-692544481281.us-central1.run.app/api/auth/login" -Method Post -ContentType "application/json" -Body '{"username": "finance@helm.com", "email": "finance@helm.com", "password": "P@ssword123"}').access_token

Write-Host "=== CHECKING SCORES ENDPOINT RESPONSE ===" -ForegroundColor Cyan
Write-Host ""

$scores = Invoke-RestMethod -Uri "https://lfsd-backend-692544481281.us-central1.run.app/api/scores/current" -Headers @{Authorization = ("Bearer " + $token) }

Write-Host "Full Response:" -ForegroundColor Yellow
$scores | ConvertTo-Json -Depth 10

Write-Host "`n=== BREAKDOWN.FINANCIAL ===" -ForegroundColor Cyan
if ($scores.breakdown.financial) {
    Write-Host "Financial Score: $($scores.breakdown.financial.score)" -ForegroundColor Green
    Write-Host "Subscores:" -ForegroundColor Yellow
    if ($scores.breakdown.financial.subscores) {
        $scores.breakdown.financial.subscores | ConvertTo-Json -Depth 5
    }
    else {
        Write-Host "  ❌ NO SUBSCORES FOUND" -ForegroundColor Red
    }
}
else {
    Write-Host "❌ NO FINANCIAL BREAKDOWN" -ForegroundColor Red
}
