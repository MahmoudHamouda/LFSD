$ErrorActionPreference = "Stop"

$Auth0Domain = "dev-lmc05ou12e7ep05p.eu.auth0.com"
$ClientId = "IRJU5sZi2elmPMgqyC3cvYVSQvzFUzia"
$ClientSecret = "xymjRYlEU5r0V37kws7PnOyhIBRhm2Nz_cCQTGL7NEjnuqNMBcZUDmbsmd6V96P8"
$Audience = "https://dev-lmc05ou12e7ep05p.eu.auth0.com/api/v2/"
$Username = "finance@helm.com"
$Password = "P@ssword"

Write-Host "Testing ROPG Login for $Username..."

$Url = "https://$Auth0Domain/oauth/token"
$Body = @{
    grant_type    = "http://auth0.com/oauth/grant-type/password-realm"
    realm         = "Username-Password-Authentication"
    username      = $Username
    password      = $Password
    client_id     = $ClientId
    client_secret = $ClientSecret
    audience      = $Audience
    scope         = "openid profile email offline_access"
}

try {
    $Response = Invoke-RestMethod -Uri $Url -Method Post -Body ($Body | ConvertTo-Json) -ContentType "application/json"
    Write-Host "Login Successful!" -ForegroundColor Green
    Write-Host "Access Token: $($Response.access_token.Substring(0, 20))..."
}
catch {
    Write-Error "Login Failed: $_"
    if ($_.Exception.Response) {
        $Reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        Write-Host "Details: $($Reader.ReadToEnd())" -ForegroundColor Red
    }
}
