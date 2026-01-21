# Check GitHub Actions workflow runs
$headers = @{
    "Accept" = "application/vnd.github+json"
    "Authorization" = "Bearer $env:GITHUB_TOKEN"
}

$repo = "MahmoudHamouda/LFSD"
$url = "https://api.github.com/repos/$repo/actions/runs?per_page=10"

try {
    $response = Invoke-RestMethod -Uri $url -Headers $headers
    
    Write-Host "="*70
    Write-Host "GITHUB ACTIONS - RECENT RUNS"
    Write-Host "="*70
    
    foreach ($run in $response.workflow_runs) {
        $status_icon = if ($run.conclusion -eq "success") { "✅" } elseif ($run.conclusion -eq "failure") { "❌" } else { "⏳" }
        Write-Host("")
        Write-Host "$status_icon $($run.name) - $($run.head_commit.message.Split("`n")[0])"
        Write-Host "   Status: $($run.status) / Conclusion: $($run.conclusion)"
        Write-Host "   Started: $($run.created_at)"
        Write-Host "   URL: $($run.html_url)"
    }
    
    Write-Host("")
    Write-Host "="*70
    Write-Host "To view details, visit: https://github.com/$repo/actions"
    Write-Host "="*70
    
} catch {
    Write-Host "❌ Error: Unable to fetch GitHub Actions runs"
    Write-Host "   Make sure GITHUB_TOKEN environment variable is set"
    Write-Host "   Or visit https://github.com/$repo/actions manually"
}
