# Self-Hosted Runner Setup for All Repositories

This document provides comprehensive instructions for setting up the `md-runner` self-hosted runner across all repositories in the organization.

## Current Status

- ✅ **Runner exists**: `md-runner` is online and registered with `market_data_infra`
- ❌ **Missing registrations**: Runner needs to be registered with other repositories
- 🔄 **Stuck workflows**: Some repositories have workflows waiting for self-hosted runners

## Repositories That Need Runner Registration

| Repository | Status | Runner Needed For |
|------------|--------|-------------------|
| `market_data_infra` | ✅ Registered | Infrastructure management |
| `market_data_pipeline` | ❌ Not registered | Release webhooks |
| `market_data_ibkr` | ❌ Not registered | Release webhooks |
| `market_data_store` | ❌ Not registered | Release webhooks |
| `market_data_orchestrator` | ❌ Not registered | Release webhooks |

## Quick Setup

### Option 1: Automated Script

Run the PowerShell script to generate all registration commands:

```powershell
.\scripts\register_runner_all_repos.ps1
```

This will output all the registration commands you need to run on your Docker runner host.

### Option 2: Manual Registration

For each repository, get a registration token and register the runner:

```bash
# Get token for market_data_pipeline
gh api repos/mjdevaccount/market_data_pipeline/actions/runners/registration-token --method POST

# Register runner (run on your Docker host)
./config.sh \
  --url https://github.com/mjdevaccount/market_data_pipeline \
  --token [TOKEN_FROM_ABOVE] \
  --name md-runner \
  --labels self-hosted,Linux,X64,mdnet \
  --work _work \
  --replace
```

## Step-by-Step Instructions

### 1. Generate Registration Commands

On your local machine (where you have `gh` CLI):

```powershell
# Run the script to generate all commands
.\scripts\register_runner_all_repos.ps1
```

This will output registration commands for all repositories.

### 2. Register Runner with All Repositories

SSH into your Docker runner host and run each registration command:

```bash
# Navigate to your runner directory
cd /path/to/your/runner/directory

# Run each registration command from the script output
./config.sh --url https://github.com/mjdevaccount/market_data_pipeline --token [TOKEN] --name md-runner --labels self-hosted,Linux,X64,mdnet --work _work --replace
./config.sh --url https://github.com/mjdevaccount/market_data_ibkr --token [TOKEN] --name md-runner --labels self-hosted,Linux,X64,mdnet --work _work --replace
# ... and so on for each repository
```

### 3. Verify Registration

Check each repository's runner page:

- **market_data_pipeline**: https://github.com/mjdevaccount/market_data_pipeline/settings/actions/runners
- **market_data_ibkr**: https://github.com/mjdevaccount/market_data_ibkr/settings/actions/runners
- **market_data_infra**: https://github.com/mjdevaccount/market_data_infra/settings/actions/runners
- **market_data_store**: https://github.com/mjdevaccount/market_data_store/settings/actions/runners
- **market_data_orchestrator**: https://github.com/mjdevaccount/market_data_orchestrator/settings/actions/runners

All should show `md-runner` as online.

## What This Fixes

### Immediate Issues
- ✅ **Stuck workflows**: The `notify-infra` jobs will start running immediately
- ✅ **Release webhooks**: All repositories can now send webhooks to `localhost:8000`

### Future Benefits
- ✅ **Consistent infrastructure**: All repos use the same runner
- ✅ **Resource efficiency**: One runner handles all repositories
- ✅ **Centralized management**: Easy to monitor and maintain

## Workflow Integration

Once registered, the following workflows will work:

### Release Workflows
- **Auto-release**: When dependencies update
- **Manual release**: When creating GitHub releases
- **Webhook notifications**: Sent to infrastructure portal

### Webhook Payloads
All repositories will send consistent webhook payloads:
```json
{
  "repository": {
    "name": "market_data_pipeline"
  },
  "release": {
    "tag_name": "v1.2.3"
  }
}
```

## Troubleshooting

### Runner Not Appearing
1. Check if the registration token expired
2. Verify the runner is online in `market_data_infra`
3. Check network connectivity from runner to GitHub

### Workflows Still Stuck
1. Verify runner appears in repository settings
2. Check runner labels match workflow requirements
3. Ensure runner is not busy with other jobs

### Webhook Failures
1. Test connectivity: `curl http://localhost:8000/runtime/webhook`
2. Check infrastructure portal is running
3. Verify webhook secret is correct

## Token Management

⚠️ **Important**: Registration tokens expire after 1 hour.

### Getting Fresh Tokens
```bash
# For each repository
gh api repos/mjdevaccount/[REPO]/actions/runners/registration-token --method POST
```

### Automatic Token Refresh
Consider setting up a script to refresh tokens automatically or use organization-level runners if available.

## Security Considerations

- Runner has access to all registered repositories
- Monitor runner logs for security issues
- Rotate webhook secrets regularly
- Consider firewall rules for production environments

## Next Steps

After completing registration:

1. **Test workflows**: Create a test release to verify webhook integration
2. **Monitor logs**: Check runner logs for any issues
3. **Update documentation**: Document the runner setup for team members
4. **Consider automation**: Set up monitoring and alerting for runner health
