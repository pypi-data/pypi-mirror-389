#!/bin/bash
# Register existing Docker runner with market_data_pipeline repository

set -euo pipefail

echo "🔧 Registering existing Docker runner with market_data_pipeline repository"

# Configuration
REPO_URL="https://github.com/mjdevaccount/market_data_pipeline"
RUNNER_NAME="infra-runner-docker"
RUNNER_LABELS="self-hosted,linux,x64,infra,docker"

# Get fresh registration token
echo "🔑 Getting fresh registration token..."
TOKEN=$(gh api repos/mjdevaccount/market_data_pipeline/actions/runners/registration-token --method POST | jq -r '.token')
echo "Token: $TOKEN"

echo "📋 Registration instructions for your existing Docker runner:"
echo ""
echo "1. SSH into your Docker runner host"
echo "2. Navigate to your runner directory"
echo "3. Run the following commands:"
echo ""
echo "   # Configure the runner"
echo "   ./config.sh \\"
echo "     --url $REPO_URL \\"
echo "     --token $TOKEN \\"
echo "     --name $RUNNER_NAME \\"
echo "     --labels $RUNNER_LABELS \\"
echo "     --work _work \\"
echo "     --replace"
echo ""
echo "   # Start the runner"
echo "   ./run.sh"
echo ""
echo "4. Verify in GitHub:"
echo "   https://github.com/mjdevaccount/market_data_pipeline/settings/actions/runners"
echo ""
echo "⚠️  Token expires: $(date -d '+1 hour' 2>/dev/null || echo 'in 1 hour')"
