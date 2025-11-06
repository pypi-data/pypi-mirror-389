#!/bin/bash
# Setup script for GitHub Actions self-hosted runner
# This script sets up a self-hosted runner for the market_data_pipeline repository

set -euo pipefail

echo "🚀 Setting up GitHub Actions self-hosted runner for market_data_pipeline"

# Configuration
REPO_URL="https://github.com/mjdevaccount/market_data_pipeline"
RUNNER_TOKEN="BE3WCOIAIHWCJUFNMHC5BKTI7P4EE"  # This should be rotated regularly
RUNNER_NAME="infra-runner-$(hostname)"
RUNNER_LABELS="self-hosted,linux,x64,infra"

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

# Configure the runner
echo "⚙️ Configuring runner..."
./config.sh \
  --url "$REPO_URL" \
  --token "$RUNNER_TOKEN" \
  --name "$RUNNER_NAME" \
  --labels "$RUNNER_LABELS" \
  --work "_work" \
  --replace

echo "✅ Runner configuration complete!"
echo ""
echo "🔧 To start the runner:"
echo "   cd actions-runner"
echo "   ./run.sh"
echo ""
echo "🔧 To run as a service (recommended for production):"
echo "   sudo ./svc.sh install"
echo "   sudo ./svc.sh start"
echo ""
echo "⚠️  IMPORTANT: The runner token expires and needs to be rotated regularly!"
echo "   Get a new token from: https://github.com/mjdevaccount/market_data_pipeline/settings/actions/runners"
