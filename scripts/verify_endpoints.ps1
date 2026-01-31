$ErrorActionPreference = "Stop"
$BackendUrl = "https://lfsd-backend-692544481281.us-central1.run.app"
$User = "finance@helm.com"

# Bypass Auth0 Login -> Use Dev Header
$Headers = @{ 
    "X-Test-User-Id" = $User
    "Content-Type"   = "application/json"
}

Write-Host "Verifying Endpoints for $User..."

# 1. Recommendations
try {
    Write-Host "Checking /api/home/recommendations..."
    $Recs = Invoke-RestMethod -Uri "$BackendUrl/api/home/recommendations" -Method Get -Headers $Headers
    Write-Host "  Success: Retrieved $($Recs.items.Count) recommendations." -ForegroundColor Green
}
catch {
    Write-Warning "  Detailed Error for Recommendations: $_"
    try { $e = $_.Exception.Response.GetResponseStream(); $r = [System.IO.StreamReader]::new($e).ReadToEnd(); Write-Host "  Response: $r" } catch {}
}

# 2. Entitlements
try {
    Write-Host "Checking /api/growth/entitlements..."
    $Ent = Invoke-RestMethod -Uri "$BackendUrl/api/growth/entitlements" -Method Get -Headers $Headers
    Write-Host "  Success: Retrieved entitlements for tier $($Ent.tier)." -ForegroundColor Green
}
catch {
    Write-Warning "  Detailed Error for Entitlements: $_"
}

# 3. Goals
try {
    Write-Host "Checking /api/finance/goals..."
    $Goals = Invoke-RestMethod -Uri "$BackendUrl/api/finance/goals" -Method Get -Headers $Headers
    Write-Host "  Success: Retrieved $($Goals.Count) goals." -ForegroundColor Green
}
catch {
    Write-Warning "  Detailed Error for Goals: $_"
}
