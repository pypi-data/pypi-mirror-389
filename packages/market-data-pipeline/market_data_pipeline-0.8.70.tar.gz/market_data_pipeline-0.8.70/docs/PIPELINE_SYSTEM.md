# Market Data Pipeline System

## Overview

The Market Data Pipeline System is a production-grade job execution engine that provides:

- **Live and backfill job execution** based on core configuration
- **Lifecycle tracking** with real-time heartbeats and audit trails
- **Telemetry and metrics** for monitoring and alerting
- **Retry and pacing policies** for provider compliance
- **Storage integration** with idempotent upserts

## Architecture

```
┌──────────────────────────────────────────┐
│            market_data_core              │
│  AppConfig • ProviderRegistry • Bar      │
└────────────────────┬─────────────────────┘
                     │
   config + providers │
                     ▼
┌──────────────────────────────────────────┐
│           market_data_pipeline            │
│  runner.py  – executes jobs               │
│  policies.py – retry/pacing guards        │
│  telemetry.py – metrics + heartbeats      │
│  cli/main.py – run/backfill commands      │
└────────────────────┬─────────────────────┘
                     │
   writes + tracking │
                     ▼
┌──────────────────────────────────────────┐
│           market_data_store              │
│  StoreClient • JobRunTracker • tables    │
└──────────────────────────────────────────┘
```

## Components

### 1. Job Runner (`jobs/runner.py`)

The core job execution engine with lifecycle tracking:

```python
@contextmanager
def tracked_run(cfg, job_name: str, dry_run: bool = False):
    """Context manager for tracking job execution lifecycle."""
    tracker = JobRunTracker(cfg.storage.primary.uri)
    run_id = tracker.start_run(job_name=job_name, ...)
    try:
        yield tracker, run_id
        tracker.complete_run(run_id, status="success")
    except Exception as ex:
        tracker.complete_run(run_id, status="failure", error=str(ex))
        raise
```

**Features:**
- Automatic lifecycle management (start → progress → complete)
- Progress updates with batch counting
- Error handling and status tracking
- Dry run support for validation

### 2. Telemetry System (`telemetry.py`)

Prometheus metrics and heartbeat integration:

```python
class PipelineTelemetry:
    def __init__(self, port: int = 9090):
        self.job_runs_total = Counter('pipeline_job_runs_total', ...)
        self.rows_written_total = Counter('pipeline_rows_written_total', ...)
        self.provider_requests_total = Counter('pipeline_provider_requests_total', ...)
```

**Metrics:**
- `pipeline_job_runs_total{job,status}` - Job execution counts
- `pipeline_rows_written_total{job,provider}` - Data volume metrics
- `pipeline_batches_total{job,provider}` - Batch processing metrics
- `pipeline_provider_requests_total{provider,status}` - Provider interaction metrics
- `pipeline_active_jobs{job_name}` - Active job tracking

### 3. Retry & Pacing Policies (`jobs/policies.py`)

Provider compliance and error handling:

```python
@retry(max_attempts=3, backoff_seconds=5.0, jitter=True)
@respect_budget(provider_budget)
def execute_batch(...):
    """Execute with retry and rate limiting."""
```

**Features:**
- Token bucket rate limiting
- Exponential backoff with jitter
- Provider-specific pacing budgets
- Telemetry integration

### 4. CLI Interface (`cli/main.py`)

Unified entry points for job execution:

```bash
# Live job execution
mdp run --config configs/base.yaml --job live_us_equities --profile dev

# Backfill job execution
mdp backfill --config configs/base.yaml --job spy_1day_backfill

# Dry run validation
mdp run --config configs/base.yaml --job live_us_equities --dry-run

# Configuration validation
mdp validate --config configs/base.yaml --profile prod
```

## Usage Examples

### 1. Live Job Execution

```bash
# Execute live market data collection
mdp run --config configs/sample.yaml --job synthetic_live

# With profile override
mdp run --config configs/sample.yaml --job synthetic_live --profile prod

# Dry run to validate configuration
mdp run --config configs/sample.yaml --job synthetic_live --dry-run
```

### 2. Backfill Job Execution

```bash
# Execute historical backfill
mdp backfill --config configs/sample.yaml --job synthetic_backfill

# With specific profile
mdp backfill --config configs/sample.yaml --job synthetic_backfill --profile staging
```

### 3. Configuration Validation

```bash
# Validate configuration
mdp validate --config configs/sample.yaml

# Validate with specific profile
mdp validate --config configs/sample.yaml --profile prod
```

## Configuration

### Example Configuration

```yaml
# configs/sample.yaml
version: 2
profile: dev

# Providers
providers:
  synthetic_1:
    type: synthetic
    enabled: true
    seed: 42
    pacing:
      requests_per_minute: 40
      burst: 10
      cooldown_seconds: 60

# Storage
storage:
  primary:
    type: timescaledb
    uri: "postgresql://user:pass@localhost:5432/marketdata"
    write:
      batch_size: 1000
      upsert_keys: ["provider", "symbol", "interval", "ts"]

# Jobs
jobs:
  synthetic_live:
    dataset: synthetic_smoke
    mode: live
    execution:
      concurrency: 1
      retry:
        max_attempts: 3
        backoff_seconds: 5

# Features
features:
  write_enabled: true
  export_enabled: false

# Telemetry
telemetry:
  log_level: INFO
  metrics:
    enabled: true
    port: 9090
```

## Monitoring & Observability

### Prometheus Metrics

The system exposes metrics on port 9090 (configurable):

- **Job Metrics**: Execution counts, duration, success rates
- **Data Metrics**: Rows processed, batches completed
- **Provider Metrics**: Request counts, rate limit violations
- **Storage Metrics**: Write duration, error counts

### Grafana Dashboard

Key metrics to monitor:

- `pipeline_job_runs_total` - Job execution success/failure rates
- `pipeline_rows_written_total` - Data throughput
- `pipeline_active_jobs` - Current job load
- `pipeline_provider_rate_limit_violations_total` - Provider compliance

### Health Checks

```bash
# Check metrics endpoint
curl http://localhost:9090/metrics

# Check job status
mdp status --job synthetic_live
```

## Error Handling & Recovery

### Common Failure Scenarios

1. **Provider Rate Limiting**
   - Automatic backoff and retry
   - Token bucket rate limiting
   - Metrics tracking for violations

2. **Storage Failures**
   - Retry with exponential backoff
   - Error classification and metrics
   - Graceful degradation

3. **Configuration Errors**
   - Validation before execution
   - Clear error messages
   - Dry run mode for testing

### Recovery Strategies

1. **Automatic Retry**: Built-in retry policies with backoff
2. **Progress Tracking**: Resume from last successful batch
3. **Error Classification**: Different handling for transient vs permanent errors
4. **Monitoring Alerts**: Prometheus alerts for critical failures

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Throughput | ≥ 10k bars/sec | StoreClient metrics |
| Reliability | 100% retry compliance | Provider pacing metrics |
| Observability | All metrics visible | Prometheus targets |
| Automation | CI/CD tag published | Build & test pass |

## Testing

### Unit Tests

```bash
# Run unit tests
pytest tests/unit/test_runner_lifecycle.py
pytest tests/unit/test_retry_policy.py
pytest tests/unit/test_rate_limiter.py
pytest tests/unit/test_metrics_exporter.py
```

### Integration Tests

```bash
# Run integration tests
pytest tests/integration/test_pipeline_to_store_roundtrip.py
pytest tests/integration/test_backfill_chunking.py
pytest tests/integration/test_failure_recovery.py
```

### Smoke Test

```bash
# Validate configuration
mdp validate --config configs/sample.yaml

# Execute synthetic job
mdp run --config configs/sample.yaml --job synthetic_live

# Verify results
# - 1+ rows in bars_ohlcv
# - Audit entry in job_runs
```

## Development

### Adding New Providers

1. Implement provider protocol in `market_data_core`
2. Add provider configuration in config files
3. Update provider registry in runner
4. Add provider-specific metrics

### Adding New Storage Targets

1. Implement storage client interface
2. Add storage configuration
3. Update write_results function
4. Add storage-specific metrics

### Custom Retry Policies

1. Define retry policy in configuration
2. Apply policy decorators to functions
3. Add policy-specific metrics
4. Test with failure scenarios

## Troubleshooting

### Common Issues

1. **Job fails to start**
   - Check configuration validation
   - Verify provider connectivity
   - Check storage availability

2. **Rate limit violations**
   - Adjust provider pacing settings
   - Check token bucket configuration
   - Monitor rate limit metrics

3. **Storage write failures**
   - Check database connectivity
   - Verify table schema
   - Check batch size settings

### Debug Commands

```bash
# Dry run to validate
mdp run --config configs/sample.yaml --job synthetic_live --dry-run

# Check metrics
curl http://localhost:9090/metrics | grep pipeline

# Validate configuration
mdp validate --config configs/sample.yaml --profile dev
```

## Future Enhancements

1. **Distributed Execution**: Multi-node job execution
2. **Advanced Scheduling**: Cron-based job scheduling
3. **Data Quality**: Schema validation and drift detection
4. **Cost Optimization**: Resource usage optimization
5. **Multi-tenant**: Tenant isolation and resource quotas
