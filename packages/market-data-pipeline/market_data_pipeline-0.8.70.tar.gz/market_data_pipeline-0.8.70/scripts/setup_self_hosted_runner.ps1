# Setup script for GitHub Actions self-hosted runner
# This script sets up a self-hosted runner for the market_data_pipeline repository

Write-Host "🚀 Setting up GitHub Actions self-hosted runner for market_data_pipeline" -ForegroundColor Green

# Configuration
$RepoUrl = "https://github.com/mjdevaccount/market_data_pipeline"
$RunnerToken = "BE3WCOIAIHWCJUFNMHC5BKTI7P4EE"  # This should be rotated regularly
$RunnerName = "infra-runner-$(hostname)"
$RunnerLabels = "self-hosted,linux,x64,infra"

# Create runner directory
Write-Host "📁 Creating runner directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "actions-runner"
Set-Location "actions-runner"

# Download the latest runner package
Write-Host "⬇️ Downloading GitHub Actions runner..." -ForegroundColor Yellow
Invoke-WebRequest -Uri "https://github.com/actions/runner/releases/download/v2.329.0/actions-runner-linux-x64-2.329.0.tar.gz" -OutFile "actions-runner-linux-x64-2.329.0.tar.gz"

# Extract the installer (requires WSL or Linux subsystem)
Write-Host "📦 Extracting runner package..." -ForegroundColor Yellow
Write-Host "⚠️  Note: This requires WSL or Linux subsystem to run the Linux runner" -ForegroundColor Red

Write-Host "✅ Setup script created!" -ForegroundColor Green
Write-Host ""
Write-Host "🔧 To complete setup on Linux server:" -ForegroundColor Cyan
Write-Host "   1. Copy this script to your Linux server" -ForegroundColor White
Write-Host "   2. Run: bash scripts/setup_self_hosted_runner.sh" -ForegroundColor White
Write-Host "   3. Start runner: cd actions-runner && ./run.sh" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  IMPORTANT: The runner token expires and needs to be rotated regularly!" -ForegroundColor Red
Write-Host "   Get a new token from: https://github.com/mjdevaccount/market_data_pipeline/settings/actions/runners" -ForegroundColor Yellow
