#!/bin/bash
# Register the same runner with multiple repositories

set -euo pipefail

echo "🔄 Registering runner with multiple repositories"

# List of repositories to register with
REPOS=(
    "mjdevaccount/market_data_pipeline"
    "mjdevaccount/market_data_ibkr"
    "mjdevaccount/market_data_infra"
    # Add more repositories as needed
)

RUNNER_NAME="infra-runner-$(hostname)"
RUNNER_LABELS="self-hosted,linux,x64,infra"

# Create runner directory
echo "📁 Creating runner directory..."
mkdir -p actions-runner
cd actions-runner

# Download the latest runner package
echo "⬇️ Downloading GitHub Actions runner..."
curl -o actions-runner-linux-x64-2.329.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.329.0/actions-runner-linux-x64-2.329.0.tar.gz

# Validate the hash
echo "🔍 Validating download hash..."
echo "194f1e1e4bd02f80b7e9633fc546084d8d4e19f3928a324d512ea53430102e1d  actions-runner-linux-x64-2.329.0.tar.gz" | shasum -a 256 -c

# Extract the installer
echo "📦 Extracting runner package..."
tar xzf ./actions-runner-linux-x64-2.329.0.tar.gz

echo "🔧 Registering runner with repositories..."

for repo in "${REPOS[@]}"; do
    echo "📋 Registering with $repo..."
    
    # Get registration token for this repository
    TOKEN=$(gh api repos/$repo/actions/runners/registration-token --method POST | jq -r '.token')
    
    # Configure the runner for this repository
    ./config.sh \
      --url "https://github.com/$repo" \
      --token "$TOKEN" \
      --name "$RUNNER_NAME" \
      --labels "$RUNNER_LABELS" \
      --work "_work" \
      --replace
    
    echo "✅ Registered with $repo"
done

echo ""
echo "✅ Runner registration complete for all repositories!"
echo ""
echo "🔧 To start the runner:"
echo "   cd actions-runner"
echo "   ./run.sh"
echo ""
echo "🔧 To run as a service:"
echo "   sudo ./svc.sh install"
echo "   sudo ./svc.sh start"
echo ""
echo "🌐 Check runner status in each repository:"
for repo in "${REPOS[@]}"; do
    echo "   https://github.com/$repo/settings/actions/runners"
done
