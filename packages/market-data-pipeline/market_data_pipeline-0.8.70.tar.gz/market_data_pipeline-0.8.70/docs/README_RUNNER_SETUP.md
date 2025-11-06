# Self-Hosted Runner Setup - Final Instructions

## Current Status
- ✅ **Runner exists**: `md-runner` is online in `market_data_infra`
- ❌ **Missing registration**: Runner needs to be registered with other repositories
- 🔄 **Stuck workflow**: `notify-infra` job is stuck waiting for runner

## Immediate Action Required

SSH into your Docker runner host and run these commands:

```bash
# Navigate to your runner directory
cd /path/to/your/runner/directory

# Register with market_data_pipeline (FIXES STUCK WORKFLOW)
./config.sh \
  --url https://github.com/mjdevaccount/market_data_pipeline \
  --token BE3WCOLPHF4N5MOLKPDBMDLI7P4JW \
  --name md-runner \
  --labels self-hosted,Linux,X64,mdnet \
  --work _work \
  --replace

# Register with market_data_ibkr
./config.sh \
  --url https://github.com/mjdevaccount/market_data_ibkr \
  --token BE3WCOO2RIJROKA5DQJDPJLI7P4PA \
  --name md-runner \
  --labels self-hosted,Linux,X64,mdnet \
  --work _work \
  --replace

# Register with market_data_orchestrator
./config.sh \
  --url https://github.com/mjdevaccount/market_data_orchestrator \
  --token BE3WCOOAIVE27UVCPWNPQTDI7P4PK \
  --name md-runner \
  --labels self-hosted,Linux,X64,mdnet \
  --work _work \
  --replace
```

## Verification

After registration, check these URLs:
- **market_data_pipeline**: https://github.com/mjdevaccount/market_data_pipeline/settings/actions/runners
- **market_data_ibkr**: https://github.com/mjdevaccount/market_data_ibkr/settings/actions/runners
- **market_data_orchestrator**: https://github.com/mjdevaccount/market_data_orchestrator/settings/actions/runners

All should show `md-runner` as online.

## Expected Results

1. **Stuck workflow will start**: The current `notify-infra` job will run immediately
2. **Webhook integration works**: All repositories can send notifications to `localhost:8000`
3. **Future releases work**: No more stuck workflows

## Token Expiry
⚠️ **Tokens expire in ~1 hour**. If they expire, get new ones:
```bash
gh api repos/mjdevaccount/[REPO]/actions/runners/registration-token --method POST
```

## Files Created
- `docs/RUNNER_SETUP_INSTRUCTIONS.md` - Complete setup guide
- `docs/SELF_HOSTED_RUNNER_SETUP.md` - Comprehensive documentation  
- `scripts/runner_registration_commands.txt` - Ready-to-use commands
- `scripts/register_runner_all_repos.ps1` - PowerShell script
- `scripts/register_runner_all_repos.sh` - Bash script
- `docker/self-hosted-runner/` - Docker setup (if needed)
