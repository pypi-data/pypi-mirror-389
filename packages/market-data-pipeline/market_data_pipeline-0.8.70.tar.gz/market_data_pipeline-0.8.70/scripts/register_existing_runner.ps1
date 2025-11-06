# Register existing Docker runner with market_data_pipeline repository

Write-Host "🔧 Registering existing Docker runner with market_data_pipeline repository" -ForegroundColor Green

# Configuration
$RepoUrl = "https://github.com/mjdevaccount/market_data_pipeline"
$RunnerName = "infra-runner-docker"
$RunnerLabels = "self-hosted,linux,x64,infra,docker"

# Get fresh registration token
Write-Host "🔑 Getting fresh registration token..." -ForegroundColor Yellow
$Token = (gh api repos/mjdevaccount/market_data_pipeline/actions/runners/registration-token --method POST | ConvertFrom-Json).token
Write-Host "Token: $Token" -ForegroundColor Cyan

Write-Host "📋 Registration instructions for your existing Docker runner:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. SSH into your Docker runner host" -ForegroundColor White
Write-Host "2. Navigate to your runner directory" -ForegroundColor White
Write-Host "3. Run the following commands:" -ForegroundColor White
Write-Host ""
Write-Host "   # Configure the runner" -ForegroundColor Cyan
Write-Host "   ./config.sh \" -ForegroundColor White
Write-Host "     --url $RepoUrl \" -ForegroundColor White
Write-Host "     --token $Token \" -ForegroundColor White
Write-Host "     --name $RunnerName \" -ForegroundColor White
Write-Host "     --labels $RunnerLabels \" -ForegroundColor White
Write-Host "     --work _work \" -ForegroundColor White
Write-Host "     --replace" -ForegroundColor White
Write-Host ""
Write-Host "   # Start the runner" -ForegroundColor Cyan
Write-Host "   ./run.sh" -ForegroundColor White
Write-Host ""
Write-Host "4. Verify in GitHub:" -ForegroundColor White
Write-Host "   https://github.com/mjdevaccount/market_data_pipeline/settings/actions/runners" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  Token expires in 1 hour" -ForegroundColor Red
