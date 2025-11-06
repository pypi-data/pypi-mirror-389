# Register md-runner with all repositories in the organization

Write-Host "🔄 Registering md-runner with all repositories" -ForegroundColor Green

# List of all repositories that need the runner
$Repos = @(
    "mjdevaccount/market_data_pipeline",
    "mjdevaccount/market_data_ibkr", 
    "mjdevaccount/market_data_infra",
    "mjdevaccount/market_data_store",
    "mjdevaccount/market_data_orchestrator"
)

$RunnerName = "md-runner"
$RunnerLabels = "self-hosted,Linux,X64,mdnet"

Write-Host "📋 Repositories to register with:" -ForegroundColor Yellow
foreach ($repo in $Repos) {
    Write-Host "   - $repo" -ForegroundColor White
}

Write-Host ""
Write-Host "🔧 Registration commands for your Docker runner host:" -ForegroundColor Yellow
Write-Host ""

foreach ($repo in $Repos) {
    Write-Host "# Register with $repo" -ForegroundColor Cyan
    
    # Get registration token for this repository
    $Token = (gh api repos/$repo/actions/runners/registration-token --method POST | ConvertFrom-Json).token
    
    Write-Host "./config.sh \" -ForegroundColor White
    Write-Host "  --url https://github.com/$repo \" -ForegroundColor White
    Write-Host "  --token $Token \" -ForegroundColor White
    Write-Host "  --name $RunnerName \" -ForegroundColor White
    Write-Host "  --labels $RunnerLabels \" -ForegroundColor White
    Write-Host "  --work _work \" -ForegroundColor White
    Write-Host "  --replace" -ForegroundColor White
    Write-Host ""
}

Write-Host "✅ All registration commands generated!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Instructions:" -ForegroundColor Yellow
Write-Host "1. SSH into your Docker runner host" -ForegroundColor White
Write-Host "2. Navigate to your runner directory" -ForegroundColor White
Write-Host "3. Run each registration command above" -ForegroundColor White
Write-Host "4. Verify in GitHub settings for each repository" -ForegroundColor White