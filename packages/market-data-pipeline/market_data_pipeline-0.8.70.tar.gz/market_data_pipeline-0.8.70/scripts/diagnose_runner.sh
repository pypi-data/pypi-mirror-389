#!/bin/bash
# Diagnose self-hosted runner issues

set -euo pipefail

echo "🔍 Diagnosing self-hosted runner issues for market_data_pipeline"

echo ""
echo "📊 Current repository runners:"
gh api repos/mjdevaccount/market_data_pipeline/actions/runners

echo ""
echo "📋 Current workflow runs:"
gh run list --limit 5

echo ""
echo "🔍 Checking for stuck jobs..."
STUCK_RUN=$(gh run list --limit 1 --json databaseId,status,conclusion | jq -r '.[0] | select(.status == "in_progress") | .databaseId')
if [ "$STUCK_RUN" != "null" ] && [ -n "$STUCK_RUN" ]; then
    echo "⚠️  Found stuck run: $STUCK_RUN"
    echo "📋 Job details:"
    gh run view $STUCK_RUN
    echo ""
    echo "🔍 Job logs:"
    gh run view $STUCK_RUN --log || echo "Logs not available yet"
else
    echo "✅ No stuck runs found"
fi

echo ""
echo "🔑 Current registration token:"
TOKEN=$(gh api repos/mjdevaccount/market_data_pipeline/actions/runners/registration-token --method POST | jq -r '.token')
echo "Token: $TOKEN"

echo ""
echo "🌐 GitHub runners page:"
echo "https://github.com/mjdevaccount/market_data_pipeline/settings/actions/runners"
