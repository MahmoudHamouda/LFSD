$ErrorActionPreference = "Stop"

$BackendUrl = "https://lfsd-backend-692544481281.us-central1.run.app"

function Seed-Goals {
    param (
        [string]$Username,
        [string]$Type
    )

    Write-Host "`n=== Seeding Goals for $Username ==="
    
    # Bypass Auth0 Login -> Use Dev Header
    $Headers = @{ 
        "X-Test-User-Id" = $Username 
        "Content-Type"   = "application/json"
    }

    $Goals = @()

    if ($Type -eq "finance" -or $Type -eq "super") {
        $Goals += @{
            title         = "Emergency Fund"
            target_amount = 10000.0
            saved_amount  = 2500.0
            target_date   = (Get-Date).AddMonths(6).ToString("yyyy-MM-dd")
            type          = "emergency_fund"
            pillar        = "finance"
            priority      = "high"
        }
        $Goals += @{
            title         = "New Car"
            target_amount = 35000.0
            saved_amount  = 5000.0
            target_date   = (Get-Date).AddMonths(12).ToString("yyyy-MM-dd")
            type          = "car"
            pillar        = "finance"
            priority      = "medium"
        }
    }

    if ($Type -eq "health" -or $Type -eq "super") {
        $Goals += @{
            title         = "Run a Marathon"
            target_amount = 42.0 # km
            saved_amount  = 5.0
            target_date   = (Get-Date).AddMonths(4).ToString("yyyy-MM-dd")
            type          = "fitness"
            pillar        = "health"
            priority      = "high"
        }
    }

    if ($Type -eq "time" -or $Type -eq "super") {
        $Goals += @{
            title         = "Reduce Meetings"
            target_amount = 10.0 # hours/week
            saved_amount  = 15.0 # currently at
            target_date   = (Get-Date).AddMonths(1).ToString("yyyy-MM-dd")
            type          = "productivity"
            pillar        = "time"
            priority      = "medium"
        }
    }

    foreach ($G in $Goals) {
        try {
            # POST /api/finance/goals
            $Uri = "$BackendUrl/api/finance/goals" 
            # Note: The endpoint might be /api/goals or /api/finance/goals depending on router mount
            # In app.py: app.include_router(api_routes_goals.router, prefix="/api")
            # In api_routes_goals.py path is likely /goals or /finance/goals
            # Let's assume /api/goals based on standard REST, but wait...
            # The frontend calls /api/finance/goals.
            # If app.py mounts it at /api, and the router has prefix /finance/goals, then it matches.
            # If router has prefix /goals, then it's /api/goals.
            # frontend logs showed 200 OK for /api/finance/goals. So that path is valid.
            
            Invoke-RestMethod -Uri "$BackendUrl/api/finance/goals" -Method Post -Headers $Headers -Body ($G | ConvertTo-Json)
            Write-Host "  + Goal seeded: $($G.title)" -ForegroundColor Green
        }
        catch {
            Write-Warning "  Failed to seed goal $($G.title): $_"
        }
    }
}

Seed-Goals "finance@helm.com" "finance"
Seed-Goals "health@helm.com" "health"
Seed-Goals "time@helm.com"   "time"
