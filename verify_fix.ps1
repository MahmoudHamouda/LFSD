$token = (Invoke-RestMethod -Uri "https://lfsd-backend-692544481281.us-central1.run.app/api/auth/login" -Method Post -ContentType "application/json" -Body '{"username": "finance@helm.com", "email": "finance@helm.com", "password": "P@ssword123"}').access_token

Write-Host "--- Checking Scores ---"
$scores = Invoke-RestMethod -Uri "https://lfsd-backend-692544481281.us-central1.run.app/api/scores/current" -Headers @{Authorization=("Bearer " + $token)}
if ($scores.breakdown.financial.subscores) {
    Write-Host "SUCCESS: Subscores found."
    Write-Host "Cashflow: $($scores.breakdown.financial.subscores.cashflow_stability)"
} else {
    Write-Host "FAILURE: Subscores missing."
}

Write-Host "`n--- Checking Transactions ---"
$tx = Invoke-RestMethod -Uri "https://lfsd-backend-692544481281.us-central1.run.app/api/finance/transactions?limit=5" -Headers @{Authorization=("Bearer " + $token)}
if ($tx.data -and $tx.data.Count -gt 0) {
    $first = $tx.data[0]
    Write-Host "First Transaction Merchant: $($first.merchant)"
    if ($first.merchant -ne "Unknown" -and $first.merchant) {
        Write-Host "SUCCESS: Merchant field populated."
    } else {
        Write-Host "FAILURE: Merchant field is Unknown or missing."
    }
} else {
    Write-Host "FAILURE: No transactions found."
}
