# Self-Hosted Runner Setup for market_data_pipeline

This directory contains scripts to set up a self-hosted GitHub Actions runner for the `market_data_pipeline` repository.

## Why Self-Hosted Runners?

The `notify-infra` jobs in our release workflows need to run on self-hosted runners because they:

1. **Hit localhost:8000** - They need to be on the same network as your infrastructure portal
2. **Send webhooks** - They notify your infra portal about new releases
3. **Access internal services** - They can reach services that aren't publicly accessible

## Current Status

❌ **No self-hosted runners are currently configured**
- The `notify-infra` jobs are stuck waiting for runners
- Workflows are failing because they can't find `self-hosted` runners

## Setup Instructions

### Option 1: Linux Server Setup (Recommended)

1. **Copy the setup script to your Linux server:**
   ```bash
   scp scripts/setup_self_hosted_runner.sh user@your-server:/tmp/
   ```

2. **SSH into your server and run the setup:**
   ```bash
   ssh user@your-server
   cd /tmp
   chmod +x setup_self_hosted_runner.sh
   ./setup_self_hosted_runner.sh
   ```

3. **Start the runner:**
   ```bash
   cd actions-runner
   ./run.sh
   ```

### Option 2: Windows with WSL

1. **Run the PowerShell script locally:**
   ```powershell
   .\scripts\setup_self_hosted_runner.ps1
   ```

2. **Follow the Linux instructions in WSL**

## Token Management

⚠️ **IMPORTANT**: The registration token expires and needs to be rotated regularly!

- **Current Token**: `BE3WCOIAIHWCJUFNMHC5BKTI7P4EE`
- **Expires**: 2025-10-24T17:05:54.889-05:00
- **Get New Token**: https://github.com/mjdevaccount/market_data_pipeline/settings/actions/runners

## Runner Configuration

- **Name**: `infra-runner-{hostname}`
- **Labels**: `self-hosted,linux,x64,infra`
- **Repository**: `mjdevaccount/market_data_pipeline`
- **Work Directory**: `_work`

## Verification

After setup, you should see:

1. **Runner appears in GitHub**: https://github.com/mjdevaccount/market_data_pipeline/settings/actions/runners
2. **Workflows can run**: The `notify-infra` jobs will no longer be stuck
3. **Webhooks work**: Release notifications will be sent to `localhost:8000/runtime/webhook`

## Troubleshooting

### Runner Not Appearing
- Check the token hasn't expired
- Verify network connectivity to GitHub
- Check runner logs in the `actions-runner` directory

### Workflows Still Stuck
- Ensure the runner has the `self-hosted` label
- Check that the runner is online in GitHub settings
- Verify the runner can reach `localhost:8000`

### Webhook Failures
- Test connectivity: `curl http://localhost:8000/runtime/webhook`
- Check the infra portal is running
- Verify the webhook secret is correct
