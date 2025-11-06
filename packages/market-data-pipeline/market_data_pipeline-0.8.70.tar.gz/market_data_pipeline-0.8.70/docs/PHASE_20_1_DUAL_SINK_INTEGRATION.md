# Phase 20.1: Dual-Sink Store Integration

## 🎯 Overview

Phase 20.1 introduces a comprehensive dual-sink system that supports both legacy and provider-based store integrations, enabling runtime switching between different storage backends with full verification capabilities.

## 🏗️ Architecture

### Dual Sink System
- **Legacy Sink**: Uses `mds_client.aclient.AMDS` → writes to `bars` table
- **Provider Sink**: Uses `market_data_store.store_client.AsyncStoreClient` → writes to `bars_ohlcv` table

### Key Components

```
src/market_data_pipeline/sink/
├── store.py                    # Legacy AMDS-based sink
├── store_sink_provider.py     # Provider AsyncStoreClient sink  
└── sink_registry.py           # Factory for dynamic sink selection

configs/
└── ingestion_policy.yaml      # Configuration with store_mode

scripts/
├── verify_dual_sink.py        # Full verification harness
└── test_dual_sink_imports.py  # Import and basic functionality test
```

## 🚀 Usage

### 1. Environment Setup

```bash
# Required environment variables
export DATABASE_URL="postgresql://user:pass@host:5432/marketdata"
export STORE_MODE="provider"  # or "legacy"
export STORE_WORKERS="2"
export STORE_QUEUE_MAX="100"
export STORE_TIMEFRAME="1m"
```

### 2. Configuration

```yaml
# configs/ingestion_policy.yaml
ingestion:
  store_mode: provider             # "legacy" | "provider"
  default_timeframe: "1m"
  workers: 2
  queue_max: 100
```

### 3. Programmatic Usage

```python
from market_data_pipeline.sink.sink_registry import create_store_sink
from market_data_pipeline.context import PipelineContext

# Create context
ctx = PipelineContext(tenant_id="demo", pipeline_id="test")

# Create legacy sink (bars table)
legacy_sink = create_store_sink("legacy", ctx=ctx)

# Create provider sink (bars_ohlcv table)  
provider_sink = create_store_sink("provider", ctx=ctx)

# Create from environment
sink = create_store_sink_from_env(ctx=ctx)
```

### 4. Factory Methods

```python
from market_data_pipeline.sink.sink_registry import (
    create_store_sink,
    create_store_sink_from_env,
    get_sink_info,
    list_available_modes
)

# List available modes
modes = list_available_modes()  # ['legacy', 'provider']

# Get mode information
info = get_sink_info("provider")
print(info['table'])  # 'bars_ohlcv'
```

## 📊 Prometheus Metrics

### Legacy Sink Metrics
- `pipeline_store_sink_batches_in_total` - Total accepted batches
- `store_bars_written_total` - Rows written to bars table
- `store_sink_queue_depth` - Current queue depth

### Provider Sink Metrics  
- `provider_sink_writes_total` - Total writes to bars_ohlcv
- `provider_sink_latency_seconds` - Write latency per batch
- `provider_sink_fails_total` - Failed writes to bars_ohlcv

## 🧪 Verification

### Quick Import Test
```bash
python scripts/test_dual_sink_imports.py
```

### Full Verification Test
```bash
# Set up database connection
export DATABASE_URL="postgresql://user:pass@localhost:5432/marketdata"

# Run verification
python scripts/verify_dual_sink.py
```

### Expected Results
- ✅ Both sinks write identical data
- ✅ Latency < 0.3s for 4000 bars (4 symbols × 1000 bars)
- ✅ No failed writes or retries
- ✅ Counts in `bars` ≈ `bars_ohlcv`

## 🔧 Sink Comparison

| Feature | Legacy Sink | Provider Sink |
|---------|-------------|---------------|
| **Table** | `bars` | `bars_ohlcv` |
| **Client** | `mds_client.aclient.AMDS` | `market_data_store.store_client.AsyncStoreClient` |
| **Tenant Support** | ✅ Full tenant_id | ✅ Context-based |
| **Retry Logic** | ✅ Exponential backoff | ✅ Built-in |
| **Batch Splitting** | ✅ Configurable limits | ✅ High-throughput |
| **Telemetry** | ✅ Full telemetry | ✅ Prometheus metrics |
| **Worker Pools** | ✅ Configurable | ✅ Configurable |
| **Backpressure** | ✅ Block/Drop policies | ✅ Queue-based |

## 🎛️ Configuration Options

### Legacy Sink
```python
StoreSink(
    amds=amds_instance,           # Optional AMDS instance
    db_uri="postgresql://...",   # Database URI
    workers=2,                   # Worker threads
    queue_max=100,               # Queue size
    backpressure_policy="block", # "block" | "drop_oldest" | "drop_newest"
    default_timeframe="1m",      # Default timeframe
    max_batch_size=1000,         # Batch size limit
    table_name="bars",           # Target table
    ctx=pipeline_context         # Pipeline context
)
```

### Provider Sink
```python
StoreSink(
    db_uri="postgresql://...",   # Database URI
    workers=2,                   # Worker threads
    queue_max=100,               # Queue size
    default_timeframe="1m",      # Default timeframe
    ctx=pipeline_context        # Pipeline context
)
```

## 🔄 Migration Strategy

### Phase 1: Dual Operation
- Run both sinks simultaneously
- Verify data parity via Prometheus metrics
- Monitor performance characteristics

### Phase 2: Gradual Migration
- Switch default `store_mode` to `provider`
- Monitor for any issues
- Keep legacy sink as fallback

### Phase 3: Legacy Deprecation
- Remove legacy sink after full migration
- Update documentation and examples

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Install required packages
   pip install mds_client market_data_store
   ```

2. **Database Connection**
   ```bash
   # Verify DATABASE_URL
   echo $DATABASE_URL
   ```

3. **Permission Issues**
   ```bash
   # Check database permissions
   psql $DATABASE_URL -c "SELECT 1;"
   ```

4. **Metrics Not Appearing**
   - Verify Prometheus is running on port 9090
   - Check metric names match expected patterns
   - Ensure sinks are actually writing data

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run verification with debug output
python scripts/verify_dual_sink.py
```

## 📈 Performance Expectations

### Throughput
- **Legacy Sink**: ~5K bars/sec (with retry logic)
- **Provider Sink**: ~10K bars/sec (optimized for high-throughput)

### Latency
- **Target**: < 0.3s for 4K bars
- **P95**: < 0.5s for batch processing
- **P99**: < 1.0s for large batches

### Resource Usage
- **Memory**: ~50MB per sink instance
- **CPU**: ~10% per worker thread
- **Network**: Minimal (local database)

## 🔮 Future Enhancements

- [ ] Automatic failover between sinks
- [ ] Real-time metrics comparison dashboard
- [ ] A/B testing framework for sink performance
- [ ] Dynamic sink selection based on load
- [ ] Cross-sink data validation
- [ ] Automated migration tools

---

**Phase 20.1 Status**: ✅ Complete and Ready for Production
