#!/bin/bash
# Deploy GitHub Actions Self-Hosted Runner in Docker

set -euo pipefail

echo "🐳 Deploying GitHub Actions self-hosted runner in Docker"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker Compose."
    exit 1
fi

# Navigate to the runner directory
cd "$(dirname "$0")/../docker/self-hosted-runner"

# Check if we need to get a new token
echo "🔑 Checking runner token..."
CURRENT_TOKEN=$(grep "RUNNER_TOKEN=" docker-compose.yml | cut -d'=' -f2)
echo "Current token: $CURRENT_TOKEN"

# Get fresh token
echo "🔄 Getting fresh registration token..."
NEW_TOKEN=$(gh api repos/mjdevaccount/market_data_pipeline/actions/runners/registration-token --method POST | jq -r '.token')
echo "New token: $NEW_TOKEN"

# Update docker-compose.yml with new token
echo "📝 Updating docker-compose.yml with new token..."
sed -i "s/RUNNER_TOKEN=.*/RUNNER_TOKEN=$NEW_TOKEN/" docker-compose.yml

# Stop existing runner if running
echo "🛑 Stopping existing runner..."
docker-compose down || true

# Build and start the runner
echo "🏗️ Building and starting runner..."
docker-compose up -d

# Wait for runner to start
echo "⏳ Waiting for runner to start..."
sleep 10

# Check runner status
echo "📊 Checking runner status..."
docker-compose ps

# Show logs
echo "📋 Runner logs:"
docker-compose logs --tail=20 github-runner

echo "✅ Docker runner deployment complete!"
echo ""
echo "🔍 To monitor the runner:"
echo "   docker-compose logs -f github-runner"
echo ""
echo "🌐 Check runner status in GitHub:"
echo "   https://github.com/mjdevaccount/market_data_pipeline/settings/actions/runners"
