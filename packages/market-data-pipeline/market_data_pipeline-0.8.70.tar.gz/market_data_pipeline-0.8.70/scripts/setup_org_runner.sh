#!/bin/bash
# Setup GitHub Actions self-hosted runner for organization (all repos)

set -euo pipefail

echo "🏢 Setting up GitHub Actions self-hosted runner for organization (all repos)"

# Configuration
ORG_URL="https://github.com/mjdevaccount"  # Organization URL
RUNNER_NAME="infra-runner-$(hostname)"
RUNNER_LABELS="self-hosted,linux,x64,infra,org-runner"

# Create runner directory
echo "📁 Creating runner directory..."
mkdir -p actions-runner
cd actions-runner

# Download the latest runner package
echo "⬇️ Downloading GitHub Actions runner..."
curl -o actions-runner-linux-x64-2.329.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.329.0/actions-runner-linux-x64-2.329.0.tar.gz

# Validate the hash (optional but recommended)
echo "🔍 Validating download hash..."
echo "194f1e1e4bd02f80b7e9633fc546084d8d4e19f3928a324d512ea53430102e1d  actions-runner-linux-x64-2.329.0.tar.gz" | shasum -a 256 -c

# Extract the installer
echo "📦 Extracting runner package..."
tar xzf ./actions-runner-linux-x64-2.329.0.tar.gz

# Get organization registration token
echo "🔑 Getting organization registration token..."
TOKEN=$(gh api orgs/mjdevaccount/actions/runners/registration-token --method POST | jq -r '.token')
echo "Token: $TOKEN"

# Configure the runner for organization
echo "⚙️ Configuring runner for organization..."
./config.sh \
  --url "$ORG_URL" \
  --token "$TOKEN" \
  --name "$RUNNER_NAME" \
  --labels "$RUNNER_LABELS" \
  --work "_work" \
  --replace

echo "✅ Organization runner configuration complete!"
echo ""
echo "🔧 To start the runner:"
echo "   cd actions-runner"
echo "   ./run.sh"
echo ""
echo "🔧 To run as a service (recommended for production):"
echo "   sudo ./svc.sh install"
echo "   sudo ./svc.sh start"
echo ""
echo "🌐 Check runner status:"
echo "   https://github.com/orgs/mjdevaccount/settings/actions/runners"
echo ""
echo "⚠️  IMPORTANT: This runner will be available to ALL repositories in the mjdevaccount organization!"
