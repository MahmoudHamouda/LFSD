$token = (Invoke-RestMethod -Uri "https://lfsd-backend-692544481281.us-central1.run.app/api/auth/login" -Method Post -ContentType "application/json" -Body '{"username": "finance@helm.com", "email": "finance@helm.com", "password": "P@ssword123"}').access_token

Write-Host "--- Checking Transactions Payload ---"
$tx = Invoke-RestMethod -Uri "https://lfsd-backend-692544481281.us-central1.run.app/api/finance/transactions?limit=1" -Headers @{Authorization = ("Bearer " + $token) }
Write-Host ($tx | ConvertTo-Json -Depth 5)

Write-Host "`n--- Checking Coverage Logic ---"
# Check coverage for 'cashflow_stability'
$cov = Invoke-RestMethod -Uri "https://lfsd-backend-692544481281.us-central1.run.app/api/finance/categories/cashflow_stability/coverage" -Headers @{Authorization = ("Bearer " + $token) }
Write-Host ($cov | ConvertTo-Json -Depth 5)
