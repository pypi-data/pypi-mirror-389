# Self-Hosted Runner Setup Instructions

## Problem
The `md-runner` is currently only registered with `market_data_infra`, but other repositories need it for their release workflows.

## Solution
Register the same `md-runner` with all repositories that need it.

## Quick Start

### 1. Get Registration Commands
The registration commands are ready in: `scripts/runner_registration_commands.txt`

### 2. Register Runner
SSH into your Docker runner host and run each command:

```bash
# Navigate to your runner directory
cd /path/to/your/runner/directory

# Run each registration command from the file
./config.sh --url https://github.com/mjdevaccount/market_data_pipeline --token BE3WCOLPHF4N5MOLKPDBMDLI7P4JW --name md-runner --labels self-hosted,Linux,X64,mdnet --work _work --replace

./config.sh --url https://github.com/mjdevaccount/market_data_ibkr --token BE3WCOO2RIJROKA5DQJDPJLI7P4PA --name md-runner --labels self-hosted,Linux,X64,mdnet --work _work --replace

./config.sh --url https://github.com/mjdevaccount/market_data_orchestrator --token BE3WCOOAIVE27UVCPWNPQTDI7P4PK --name md-runner --labels self-hosted,Linux,X64,mdnet --work _work --replace
```

### 3. Verify Registration
Check each repository's runner page:
- **market_data_pipeline**: https://github.com/mjdevaccount/market_data_pipeline/settings/actions/runners
- **market_data_ibkr**: https://github.com/mjdevaccount/market_data_ibkr/settings/actions/runners  
- **market_data_orchestrator**: https://github.com/mjdevaccount/market_data_orchestrator/settings/actions/runners
- **market_data_infra**: https://github.com/mjdevaccount/market_data_infra/settings/actions/runners (already registered)

All should show `md-runner` as online.

## What This Fixes

### Immediate Issues
- ✅ **Stuck workflows**: The `notify-infra` jobs will start running immediately
- ✅ **Release webhooks**: All repositories can now send webhooks to `localhost:8000`

### Repository Status
| Repository | Status | Token | Expires |
|------------|--------|-------|---------|
| `market_data_pipeline` | ❌ Not registered | `BE3WCOLPHF4N5MOLKPDBMDLI7P4JW` | 2025-10-24T17:07:23.410-05:00 |
| `market_data_ibkr` | ❌ Not registered | `BE3WCOO2RIJROKA5DQJDPJLI7P4PA` | 2025-10-24T17:08:48.868-05:00 |
| `market_data_orchestrator` | ❌ Not registered | `BE3WCOOAIVE27UVCPWNPQTDI7P4PK` | 2025-10-24T17:08:53.748-05:00 |
| `market_data_infra` | ✅ Already registered | N/A | N/A |
| `market_data_store` | ❌ Repository not found | N/A | N/A |

## Token Expiry
⚠️ **Important**: All tokens expire in about 1 hour. If they expire, get new ones:

```bash
# For each repository
gh api repos/mjdevaccount/[REPO]/actions/runners/registration-token --method POST
```

## After Registration

### Test the Fix
1. **Check stuck workflow**: The current stuck `notify-infra` job should start running
2. **Create test release**: Verify webhook integration works
3. **Monitor logs**: Check runner logs for any issues

### Expected Results
- All repositories will have `md-runner` online
- Release workflows will complete successfully
- Webhooks will be sent to `localhost:8000/runtime/webhook`
- No more stuck `notify-infra` jobs

## Troubleshooting

### Runner Not Appearing
1. Check if registration token expired
2. Verify runner is online in `market_data_infra`
3. Check network connectivity from runner to GitHub

### Workflows Still Stuck
1. Verify runner appears in repository settings
2. Check runner labels match workflow requirements (`self-hosted`)
3. Ensure runner is not busy with other jobs

### Webhook Failures
1. Test connectivity: `curl http://localhost:8000/runtime/webhook`
2. Check infrastructure portal is running
3. Verify webhook secret is correct

## Next Steps

After completing registration:

1. **Monitor the stuck workflow**: It should start running immediately
2. **Test release workflows**: Create a test release to verify integration
3. **Update team documentation**: Share this setup with team members
4. **Consider automation**: Set up monitoring for runner health
