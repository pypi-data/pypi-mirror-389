# Setup GitHub Actions self-hosted runner for organization (all repos)

Write-Host "🏢 Setting up GitHub Actions self-hosted runner for organization (all repos)" -ForegroundColor Green

# Configuration
$OrgUrl = "https://github.com/mjdevaccount"  # Organization URL
$RunnerName = "infra-runner-$(hostname)"
$RunnerLabels = "self-hosted,linux,x64,infra,org-runner"

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

# Get organization registration token
Write-Host "🔑 Getting organization registration token..." -ForegroundColor Yellow
$Token = (gh api orgs/mjdevaccount/actions/runners/registration-token --method POST | ConvertFrom-Json).token
Write-Host "Token: $Token" -ForegroundColor Cyan

Write-Host "✅ Organization runner setup script created!" -ForegroundColor Green
Write-Host ""
Write-Host "🔧 To complete setup on Linux server:" -ForegroundColor Cyan
Write-Host "   1. Copy this script to your Linux server" -ForegroundColor White
Write-Host "   2. Run: bash scripts/setup_org_runner.sh" -ForegroundColor White
Write-Host "   3. Start runner: cd actions-runner && ./run.sh" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Check runner status:" -ForegroundColor Cyan
Write-Host "   https://github.com/orgs/mjdevaccount/settings/actions/runners" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  IMPORTANT: This runner will be available to ALL repositories in the mjdevaccount organization!" -ForegroundColor Red
