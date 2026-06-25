$ErrorActionPreference = "Stop"

$Auth0Domain = "dev-lmc05ou12e7ep05p.eu.auth0.com"
$ClientId = "IRJU5sZi2elmPMgqyC3cvYVSQvzFUzia"
# Fetch ClientSecret from environment variable
$ClientSecret = $env:AUTH0_CLIENT_SECRET
if (-not $ClientSecret) {
    Write-Host "Warning: AUTH0_CLIENT_SECRET environment variable is not set. Using dummy fallback."
    $ClientSecret = "dummy_secret"
}
$Audience = "https://dev-lmc05ou12e7ep05p.eu.auth0.com/api/v2/"
$BackendUrl = "https://lfsd-backend-692544481281.us-central1.run.app"

function Seed-Persona {
    param (
        [string]$Username,
        [string]$Password,
        [string]$Type
    )

    Write-Host "`n=== Seeding $Username ($Type) ==="

    Start-Sleep -Seconds 1

    # 1. Login
    $TokenUrl = "https://$Auth0Domain/oauth/token"
    $Body = @{
        grant_type    = "http://auth0.com/oauth/grant-type/password-realm"
        realm         = "Username-Password-Authentication"
        username      = $Username
        password      = $Password
        client_id     = $ClientId
        client_secret = $ClientSecret
        audience      = $Audience
        scope         = "openid profile email"
    }

    try {
        $LoginResp = Invoke-RestMethod -Uri $TokenUrl -Method Post -Body ($Body | ConvertTo-Json) -ContentType "application/json"
        $Token = $LoginResp.access_token 
        Write-Host "  Login successful" -ForegroundColor Green
    }
    catch {
        Write-Error "  Login failed for $Username : $_"
        return
    }

    $Headers = @{ Authorization = "Bearer $Token" }

    # 2. Seed Based on Type
    if ($Type -eq "finance" -or $Type -eq "super") {
        Write-Host "  Seeding Finance Data..."
        
        $Today = Get-Date
        for ($i = 0; $i -lt 6; $i++) {
            $MonthDate = $Today.AddDays( - ($i * 30))
            
            for ($w = 0; $w -lt 2; $w++) {
                $Date = $MonthDate.AddDays( - ($w * 14))
                $Tx = @{
                    amount      = 2500.0
                    category    = "income"
                    description = "Salary"
                    date        = $Date.ToString("yyyy-MM-dd")
                }
                Invoke-RestMethod -Uri "$BackendUrl/api/finance/transactions" -Method Post -Headers $Headers -Body ($Tx | ConvertTo-Json) -ContentType "application/json"
            }
            
            $Tx = @{
                amount      = -2000.0
                category    = "housing"
                description = "Rent"
                date        = $MonthDate.ToString("yyyy-MM-dd")
            }
            Invoke-RestMethod -Uri "$BackendUrl/api/finance/transactions" -Method Post -Headers $Headers -Body ($Tx | ConvertTo-Json) -ContentType "application/json"

            for ($d = 0; $d -lt 5; $d++) {
                $Date = $MonthDate.AddDays( - ($d * 5))
                $Tx = @{
                    amount      = -45.50
                    category    = "food"
                    description = "Grocery Store"
                    date        = $Date.ToString("yyyy-MM-dd")
                }
                Invoke-RestMethod -Uri "$BackendUrl/api/finance/transactions" -Method Post -Headers $Headers -Body ($Tx | ConvertTo-Json) -ContentType "application/json"
            }
        }
        Write-Host "  Finance data seeded" -ForegroundColor Green
    }
    
    if ($Type -eq "health" -or $Type -eq "super") {
        Write-Host "  Seeding Health Data..."
        for ($i = 0; $i -lt 7; $i++) {
            $Date = (Get-Date).AddDays(-$i).ToString("yyyy-MM-dd")
            $Health = @{
                date        = $Date
                steps       = 8500 + ($i * 100)
                calories    = 2100
                sleep_hours = 7.5
            }
            try {
                Invoke-RestMethod -Uri "$BackendUrl/api/health/daily-summary" -Method Post -Headers $Headers -Body ($Health | ConvertTo-Json) -ContentType "application/json"
            }
            catch {
                Write-Warning "Health seed failed: $_"
            }
        }
        Write-Host "  Health data seeded" -ForegroundColor Green
    }

    if ($Type -eq "time" -or $Type -eq "super") {
        Write-Host "  Seeding Time Data..."
        $Date = (Get-Date).ToString("yyyy-MM-dd")
        $Event = @{
            title      = "Project Sync"
            start_time = "${Date}T10:00:00"
            end_time   = "${Date}T11:00:00"
            category   = "meeting"
        }
        try {
            Invoke-RestMethod -Uri "$BackendUrl/api/calendar/events" -Method Post -Headers $Headers -Body ($Event | ConvertTo-Json) -ContentType "application/json"
        }
        catch {
            Write-Warning "Time seed failed: $_"
        }
        Write-Host "  Time data seeded" -ForegroundColor Green
    }
}

Seed-Persona "finance@helm.com" "P@ssword" "finance"
Seed-Persona "health@helm.com" "P@ssword" "health"
Seed-Persona "time@helm.com" "P@ssword" "time"
