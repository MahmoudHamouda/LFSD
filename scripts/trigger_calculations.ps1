$ErrorActionPreference = "Stop"

$Auth0Domain = "dev-lmc05ou12e7ep05p.eu.auth0.com"
$ClientId = "IRJU5sZi2elmPMgqyC3cvYVSQvzFUzia"
$ClientSecret = "xymjRYlEU5r0V37kws7PnOyhIBRhm2Nz_cCQTGL7NEjnuqNMBcZUDmbsmd6V96P8"
$Audience = "https://dev-lmc05ou12e7ep05p.eu.auth0.com/api/v2/"
$BackendUrl = "https://lfsd-backend-692544481281.us-central1.run.app"

function Trigger-Calc {
    param (
        [string]$Username,
        [string]$Password
    )

    Write-Host "`n=== Triggering Calculation for $Username ==="

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

    $Headers = @{ 
        "X-Test-User-Id" = $Username 
    }

    # 2. Call Trigger Endpoint
    $CalcUrl = "$BackendUrl/api/scores/debug/trigger_calc"
    Write-Host "  Calling POST $CalcUrl..."
    try {
        $Resp = Invoke-RestMethod -Uri $CalcUrl -Method Post -Headers $Headers -ContentType "application/json"
        Write-Host "  Calculation Success!" -ForegroundColor Green
        # Write-Host "  Result: $($Resp | ConvertTo-Json -Depth 5)" -ForegroundColor Gray
    }
    catch {
        Write-Error "  Calculation Failed: $_"
        if ($_.Exception.Response) {
            # $Reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            # Write-Host "  Details: $($Reader.ReadToEnd())" -ForegroundColor Red
        }
    }
}

Trigger-Calc "finance@helm.com" "P@ssword"
Trigger-Calc "health@helm.com" "P@ssword"
Trigger-Calc "time@helm.com" "P@ssword"
