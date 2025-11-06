# Register Existing Runner with market_data_pipeline

Your `md-runner` is currently only registered with `market_data_infra`. To fix the stuck workflows, you need to register it with `market_data_pipeline` as well.

## Current Status
- ✅ Runner `md-runner` is online and registered with `market_data_infra`
- ❌ Runner is NOT registered with `market_data_pipeline` (causing stuck workflows)

## Solution

SSH into your Docker runner host and run:

```bash
# Navigate to your runner directory
cd /path/to/your/runner/directory

# Register the same runner with market_data_pipeline
./config.sh \
  --url https://github.com/mjdevaccount/market_data_pipeline \
  --token BE3WCOLPHF4N5MOLKPDBMDLI7P4JW \
  --name md-runner \
  --labels self-hosted,Linux,X64,mdnet \
  --work _work \
  --replace
```

## Verification

After registration, check:
1. **market_data_infra runners**: https://github.com/mjdevaccount/market_data_infra/settings/actions/runners
2. **market_data_pipeline runners**: https://github.com/mjdevaccount/market_data_pipeline/settings/actions/runners

Both should show `md-runner` as online.

## Token Expiry

⚠️ **Token expires**: 2025-10-24T17:07:23.410-05:00

If the token expires, get a new one:
```bash
gh api repos/mjdevaccount/market_data_pipeline/actions/runners/registration-token --method POST
```

## Result

Once registered, the stuck `notify-infra` job should start running immediately, and future releases will work properly.
