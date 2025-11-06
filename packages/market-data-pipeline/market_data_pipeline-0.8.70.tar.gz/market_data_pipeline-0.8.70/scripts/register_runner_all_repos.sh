#!/bin/bash
# Register md-runner with all repositories in the organization

set -euo pipefail

echo "🔄 Registering md-runner with all repositories"

# List of all repositories that need the runner
REPOS=(
    "mjdevaccount/market_data_pipeline"
    "mjdevaccount/market_data_ibkr" 
    "mjdevaccount/market_data_infra"
    "mjdevaccount/market_data_store"
    "mjdevaccount/market_data_orchestrator"
    # Add more repositories as needed
)

RUNNER_NAME="md-runner"
RUNNER_LABELS="self-hosted,Linux,X64,mdnet"

echo "📋 Repositories to register with:"
for repo in "${REPOS[@]}"; do
    echo "   - $repo"
done

echo ""
echo "🔧 Registration commands for your Docker runner host:"
echo ""

for repo in "${REPOS[@]}"; do
    echo "# Register with $repo"
    
    # Get registration token for this repository
    TOKEN=$(gh api repos/$repo/actions/runners/registration-token --method POST | jq -r '.token')
    
    echo "./config.sh \\"
    echo "  --url https://github.com/$repo \\"
    echo "  --token $TOKEN \\"
    echo "  --name $RUNNER_NAME \\"
    echo "  --labels $RUNNER_LABELS \\"
    echo "  --work _work \\"
    echo "  --replace"
    echo ""
done

echo "✅ All registration commands generated!"
echo ""
echo "📋 Instructions:"
echo "1. SSH into your Docker runner host"
echo "2. Navigate to your runner directory"
echo "3. Run each registration command above"
echo "4. Verify in GitHub: https://github.com/mjdevaccount/[repo]/settings/actions/runners"
