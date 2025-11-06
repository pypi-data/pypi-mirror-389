# Deploy GitHub Actions Self-Hosted Runner in Docker

Write-Host "🐳 Deploying GitHub Actions self-hosted runner in Docker" -ForegroundColor Green

# Check if docker-compose is available
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ docker-compose not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Navigate to the runner directory
$RunnerDir = Join-Path $PSScriptRoot "..\docker\self-hosted-runner"
Set-Location $RunnerDir

# Check current token
Write-Host "🔑 Checking runner token..." -ForegroundColor Yellow
$CurrentToken = (Select-String "RUNNER_TOKEN=" docker-compose.yml).Line.Split('=')[1]
Write-Host "Current token: $CurrentToken" -ForegroundColor Cyan

# Get fresh token
Write-Host "🔄 Getting fresh registration token..." -ForegroundColor Yellow
$NewToken = (gh api repos/mjdevaccount/market_data_pipeline/actions/runners/registration-token --method POST | ConvertFrom-Json).token
Write-Host "New token: $NewToken" -ForegroundColor Cyan

# Update docker-compose.yml with new token
Write-Host "📝 Updating docker-compose.yml with new token..." -ForegroundColor Yellow
(Get-Content docker-compose.yml) -replace "RUNNER_TOKEN=.*", "RUNNER_TOKEN=$NewToken" | Set-Content docker-compose.yml

# Stop existing runner if running
Write-Host "🛑 Stopping existing runner..." -ForegroundColor Yellow
docker-compose down

# Build and start the runner
Write-Host "🏗️ Building and starting runner..." -ForegroundColor Yellow
docker-compose up -d

# Wait for runner to start
Write-Host "⏳ Waiting for runner to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check runner status
Write-Host "📊 Checking runner status..." -ForegroundColor Yellow
docker-compose ps

# Show logs
Write-Host "📋 Runner logs:" -ForegroundColor Yellow
docker-compose logs --tail=20 github-runner

Write-Host "✅ Docker runner deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🔍 To monitor the runner:" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f github-runner" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Check runner status in GitHub:" -ForegroundColor Cyan
Write-Host "   https://github.com/mjdevaccount/market_data_pipeline/settings/actions/runners" -ForegroundColor White
