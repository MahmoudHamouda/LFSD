$token = (Invoke-RestMethod -Uri "https://lfsd-backend-692544481281.us-central1.run.app/api/auth/login" -Method Post -ContentType "application/json" -Body '{"username": "finance@helm.com", "email": "finance@helm.com", "password": "P@ssword123"}').access_token

Write-Host "=== CHECKING DATABASE DIRECTLY ===" -ForegroundColor Cyan

# Check transaction count in database
$query = @"
SELECT COUNT(*) as tx_count FROM transactions WHERE user_id = (SELECT id FROM users WHERE email = 'finance@helm.com');
"@

Write-Host "Transaction count query: $query"
