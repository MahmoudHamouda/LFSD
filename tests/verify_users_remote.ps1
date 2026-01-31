
$BackendUrl = "https://lfsd-backend-wpvii577oq-uc.a.run.app"
$LoginUrl = "$BackendUrl/api/auth/login"
$SignupUrl = "$BackendUrl/api/auth/register"

$Users = @(
    @{ email = "finance@helm.com"; password = "P@ssword" },
    @{ email = "time@helm.com"; password = "P@ssword" },
    @{ email = "Health@helm.com"; password = "P@ssword" },
    @{ email = "Super@helm.com"; password = "P@ssword" }
)

$AllPassed = $true

Write-Host "Target Backend: $BackendUrl" -ForegroundColor Cyan

# Test Login
foreach ($u in $Users) {
    $email = $u.email
    $password = $u.password
    Write-Host "Testing Login for: $email" -NoNewline
    
    $body = @{
        email    = $email
        password = $password
    } | ConvertTo-Json

    try {
        $response = Invoke-RestMethod -Uri $LoginUrl -Method Post -Body $body -ContentType "application/json" -ErrorAction Stop
        
        if ($response.access_token) {
            Write-Host " [SUCCESS]" -ForegroundColor Green
        }
        else {
            Write-Host " [FAIL] No token received." -ForegroundColor Red
            $AllPassed = $false
        }
    }
    catch {
        Write-Host " [FAIL]" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Yellow
        $AllPassed = $false
    }
}

# Test Signup
$guid = [guid]::NewGuid().ToString().Substring(0, 8)
$newUser = "testuser_$guid@helm.com"
$newPass = "NewUserPass123!"
$newName = "Test User $guid"

Write-Host "`nTesting Signup for new user: $newUser" -NoNewline

$signupBody = @{
    email    = $newUser
    password = $newPass
    name     = $newName
} | ConvertTo-Json

try {
    $resp = Invoke-RestMethod -Uri $SignupUrl -Method Post -Body $signupBody -ContentType "application/json" -ErrorAction Stop
    Write-Host " [SUCCESS]" -ForegroundColor Green
    
    # Verify login for new user
    Write-Host "Verifying login for new user..." -NoNewline
    $loginBody = @{ email = $newUser; password = $newPass } | ConvertTo-Json
    $loginResp = Invoke-RestMethod -Uri $LoginUrl -Method Post -Body $loginBody -ContentType "application/json" -ErrorAction Stop
    
    if ($loginResp.access_token) {
        Write-Host " [SUCCESS]" -ForegroundColor Green
        
        # Verify DB content (Get Profile)
        Write-Host "Verifying DB content (GET /api/user/me)..." -NoNewline
        $headers = @{ Authorization = "Bearer $($loginResp.access_token)" }
        $profileUrl = "$BackendUrl/api/user/me"
        try {
            $profileResp = Invoke-RestMethod -Uri $profileUrl -Method Get -Headers $headers -ErrorAction Stop
            if ($profileResp.user.email -eq $newUser) {
                Write-Host " [SUCCESS] Retrieved profile for $($profileResp.user.email)" -ForegroundColor Green
            }
            else {
                Write-Host " [FAIL] Profile email mismatch." -ForegroundColor Red
                $AllPassed = $false
            }
        }
        catch {
            Write-Host " [FAIL] Failed to fetch profile: $_" -ForegroundColor Red
            $AllPassed = $false
        }
    }
    else {
        Write-Host " [FAIL] Login after signup failed." -ForegroundColor Red
        $AllPassed = $false
    }

}
catch {
    Write-Host " [FAIL]" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Yellow
    $AllPassed = $false
}

if ($AllPassed) {
    Write-Host "`nAll auth tests PASSED." -ForegroundColor Green
    exit 0
}
else {
    Write-Host "`nSome auth tests FAILED." -ForegroundColor Red
    exit 1
}
