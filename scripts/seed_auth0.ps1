$ErrorActionPreference = "Stop"

# Configuration
$Auth0Domain = "dev-lmc05ou12e7ep05p.eu.auth0.com"
$ClientId = "IRJU5sZi2elmPMgqyC3cvYVSQvzFUzia"
# Fetch ClientSecret from environment variable
$ClientSecret = $env:AUTH0_CLIENT_SECRET
if (-not $ClientSecret) {
    Write-Host "Warning: AUTH0_CLIENT_SECRET environment variable is not set. Using dummy fallback."
    $ClientSecret = "dummy_secret"
}
$Connection = "Username-Password-Authentication"

# Users to seed
$Users = @(
    @{ Email = "finance@helm.com"; Password = "P@ssword"; Name = "Finance User" },
    @{ Email = "health@helm.com"; Password = "P@ssword"; Name = "Health User" },
    @{ Email = "time@helm.com"; Password = "P@ssword"; Name = "Time User" }
)

Write-Host "=== LFSD Auth0 Seeder (PowerShell) ==="

# 1. Get Management API Token
Write-Host "Getting Management API Token..."
$TokenUrl = "https://$Auth0Domain/oauth/token"
$TokenHeaders = @{ "Content-Type" = "application/json" }
$TokenBody = @{
    grant_type    = "client_credentials"
    client_id     = $ClientId
    client_secret = $ClientSecret
    audience      = "https://$Auth0Domain/api/v2/"
} | ConvertTo-Json

try {
    $TokenResponse = Invoke-RestMethod -Uri $TokenUrl -Method Post -Body $TokenBody -Headers $TokenHeaders
    $MgmtToken = $TokenResponse.access_token
    Write-Host "Token obtained." -ForegroundColor Green
}
catch {
    Write-Error "Failed to get token: $_"
    exit 1
}

# 2. Create Users
foreach ($User in $Users) {
    Write-Host "Processing $($User.Email)..."
    
    # Check if user exists
    $SearchUrl = "https://$Auth0Domain/api/v2/users-by-email?email=$($User.Email)"
    $Headers = @{ Authorization = "Bearer $MgmtToken" }
    
    try {
        $SearchResponse = Invoke-RestMethod -Uri $SearchUrl -Method Get -Headers $Headers
        if ($SearchResponse.Count -gt 0) {
            Write-Host "  User already exists. Updating password..." -ForegroundColor Yellow
            
            $Id = $SearchResponse[0].user_id
            $UpdateUrl = "https://$Auth0Domain/api/v2/users/$Id"
            $UpdateBody = @{ password = $User.Password; connection = $Connection } | ConvertTo-Json
            
            try {
                Invoke-RestMethod -Uri $UpdateUrl -Method Patch -Headers $Headers -Body $UpdateBody -ContentType "application/json"
                Write-Host "  Password updated." -ForegroundColor Green
            }
            catch {
                Write-Error "  Failed to update password: $_"
            }
            
            continue
        }
    }
    catch {
        Write-Warning "  Error searching/updating user: $_"
    }

    # Create User
    $CreateUrl = "https://$Auth0Domain/api/v2/users"
    $CreateBody = @{
        email          = $User.Email
        password       = $User.Password
        name           = $User.Name
        connection     = $Connection
        email_verified = $true
        verify_email   = $false
    } | ConvertTo-Json
    
    try {
        $CreateResponse = Invoke-RestMethod -Uri $CreateUrl -Method Post -Headers $Headers -Body $CreateBody -ContentType "application/json"
        Write-Host "  User created successfully." -ForegroundColor Green
    }
    catch {
        Write-Error "  Failed to create user: $_"
    }
}

Write-Host "Seeding completed."
