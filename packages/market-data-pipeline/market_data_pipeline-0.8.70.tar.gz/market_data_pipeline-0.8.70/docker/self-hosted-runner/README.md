# Self-Hosted Runner Docker Setup

This directory contains Docker configuration for running a GitHub Actions self-hosted runner in a container.

## Why Docker?

- **Isolation**: Runner runs in its own container
- **Consistency**: Same environment every time
- **Easy Management**: Start/stop with docker-compose
- **Network Access**: Can reach localhost:8000 for webhooks

## Quick Start

1. **Build and start the runner:**
   ```bash
   cd docker/self-hosted-runner
   docker-compose up -d
   ```

2. **Check runner status:**
   ```bash
   docker-compose logs -f github-runner
   ```

3. **Verify in GitHub:**
   - Go to: https://github.com/mjdevaccount/market_data_pipeline/settings/actions/runners
   - You should see `infra-runner-docker` online

## Configuration

### Environment Variables

- `RUNNER_TOKEN`: GitHub registration token (expires regularly)
- `RUNNER_NAME`: Name of the runner in GitHub
- `RUNNER_LABELS`: Labels for job targeting

### Network Access

The runner uses `network_mode: host` to access:
- `localhost:8000` - Your infrastructure portal
- GitHub APIs for runner communication

## Token Management

⚠️ **IMPORTANT**: The registration token expires and needs to be rotated regularly!

**Current Token**: `BE3WCOIAIHWCJUFNMHC5BKTI7P4EE`
**Expires**: 2025-10-24T17:05:54.889-05:00

### Rotating the Token

1. **Get new token:**
   ```bash
   gh api repos/mjdevaccount/market_data_pipeline/actions/runners/registration-token --method POST
   ```

2. **Update docker-compose.yml:**
   ```yaml
   environment:
     - RUNNER_TOKEN=NEW_TOKEN_HERE
   ```

3. **Restart the runner:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## Troubleshooting

### Runner Not Appearing in GitHub
```bash
# Check logs
docker-compose logs github-runner

# Check if runner is running
docker-compose ps

# Restart if needed
docker-compose restart github-runner
```

### Webhook Failures
```bash
# Test connectivity from inside container
docker-compose exec github-runner curl http://localhost:8000/runtime/webhook

# Check if infra portal is running
curl http://localhost:8000/health
```

### Runner Offline
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs github-runner

# Restart if needed
docker-compose restart github-runner
```

## Production Considerations

1. **Persistent Storage**: Runner state is persisted in `runner_data` volume
2. **Health Checks**: Container includes health check endpoint
3. **Restart Policy**: `unless-stopped` ensures runner restarts on failure
4. **Network Access**: Uses host network for localhost access

## Security Notes

- Runner has access to host network
- Consider firewall rules for production
- Rotate tokens regularly
- Monitor runner logs for security issues
