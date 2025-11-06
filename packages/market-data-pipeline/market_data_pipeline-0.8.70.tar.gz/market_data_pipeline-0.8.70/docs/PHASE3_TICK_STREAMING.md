# Phase 3 — Raw Tick Persistence (Pipeline → Store)

**Objective:** Enable end-to-end persistence of raw tick data from providers (IBKR, Synthetic) to TimescaleDB.

## Architecture

```
┌──────────────┐
│ IBKR/        │
│ Synthetic    │
│ Producers    │
└──────┬───────┘
       │ (tick events)
       ▼
┌──────────────────┐
│  Stream Bus      │
│  (Redis/Kafka)   │
│  topic: mdp.events
└──────┬───────────┘
       │
       ├─────────────────────┐
       │                     │
       ▼                     ▼
┌──────────────┐      ┌──────────────┐
│ MicroBatcher │      │ TickConsumer │
│ (aggregates) │      │ (raw ticks)  │
└──────┬───────┘      └──────┬───────┘
       │                     │
       │                     │ AsyncStoreClient
       │                     │ .upsert_ticks()
       ▼                     ▼
┌────────────────────────────────┐
│   market_data_store            │
│                                │
│   bars_ohlcv  |  tick_data     │
│   (aggregated)|  (raw ticks)   │
└────────────────────────────────┘
```

**Flow:**
1. IBKR/Synthetic producers emit tick events to stream bus
2. **MicroBatcher** consumes events → aggregates → writes bars to `bars_ohlcv`
3. **TickConsumer** consumes same events → forwards raw ticks → writes to `tick_data`
4. Both consumers run in parallel on the same event stream

## Implementation

### Pipeline (market_data_pipeline)

**Files:**
- `src/market_data_pipeline/streaming/consumers/tick_consumer.py` - Consumer implementation
- `tests/integration/test_tick_consumer_integration.py` - Integration tests

**Key Features:**
- Consumer group support for horizontal scaling
- Batch processing for efficiency
- Prometheus metrics (`tick_forward_total`, `tick_forward_failures_total`)
- Filters tick events from bar events
- Handles missing optional fields gracefully

**Usage:**
```python
from market_data_pipeline.streaming.consumers import TickConsumer
from datastore import AsyncStoreClient

# Create store client
store = AsyncStoreClient(db_uri=DATABASE_URL)

# Create consumer
consumer = TickConsumer(
    bus=stream_bus,
    store_client=store,
    batch_size=100,
    consumer_group="tick-consumer",
    consumer_name="tick-1"
)

# Start consuming
await consumer.start()
```

### Store (market_data_store)

**Files:**
- `docker/initdb.d/01_schema.sql` - Schema migration
- `src/datastore/writes.py` - `AsyncStoreClient.upsert_ticks()` method

**Schema:**
```sql
CREATE TABLE tick_data (
    provider     TEXT NOT NULL,
    symbol       TEXT NOT NULL CHECK (symbol = UPPER(symbol)),
    price        DOUBLE PRECISION NOT NULL,
    ts           TIMESTAMPTZ NOT NULL,
    size         DOUBLE PRECISION,
    bid          DOUBLE PRECISION,
    ask          DOUBLE PRECISION,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (provider, symbol, ts)
);
```

**Hypertable Configuration:**
- Chunk interval: 1 day
- Compression: After 7 days
- Segmented by: provider, symbol

**API:**
```python
await store_client.upsert_ticks([
    {
        "provider": "ibkr",
        "symbol": "NVDA",
        "price": 123.45,
        "ts": datetime(2025, 11, 3, 14, 30, 0, tzinfo=timezone.utc),
        "size": 100,
        "bid": 123.40,
        "ask": 123.50
    }
])
```

## Metrics

### Pipeline Metrics
- `tick_forward_total{provider="ibkr"}` - Total ticks forwarded to store
- `tick_forward_failures_total{provider="ibkr"}` - Failed forwards

### Store Metrics
Standard `store_bars_write_latency_seconds` also applies to tick writes.

**Grafana Queries:**
```promql
# Tick ingestion rate (ticks/sec)
rate(tick_forward_total[1m])

# Tick failure rate
rate(tick_forward_failures_total[1m])

# Tick ingestion by provider
sum(rate(tick_forward_total[5m])) by (provider)
```

## Validation

### 1. Run Integration Tests
```bash
# Pipeline tests
cd market_data_pipeline
pytest -v tests/integration/test_tick_consumer_integration.py

# Store tests
cd market_data_store
pytest -v tests/unit/test_store_client.py
```

### 2. Verify Schema
```bash
# Connect to database
psql -d market_data -U postgres

# Check table exists and is hypertable
\d+ tick_data

# Verify hypertable configuration
SELECT * FROM timescaledb_information.hypertables 
WHERE hypertable_name = 'tick_data';

# Check compression policy
SELECT * FROM timescaledb_information.jobs 
WHERE proc_name = 'policy_compression';
```

### 3. Query Tick Data
```sql
-- Count ticks
SELECT COUNT(*) FROM tick_data;

-- Recent ticks
SELECT provider, symbol, price, ts 
FROM tick_data 
ORDER BY ts DESC 
LIMIT 10;

-- Ticks per symbol (last hour)
SELECT symbol, COUNT(*) as tick_count
FROM tick_data
WHERE ts > NOW() - INTERVAL '1 hour'
GROUP BY symbol
ORDER BY tick_count DESC;

-- Price range by symbol (last day)
SELECT 
    symbol,
    MIN(price) as low,
    MAX(price) as high,
    AVG(price) as avg,
    COUNT(*) as ticks
FROM tick_data
WHERE ts > NOW() - INTERVAL '1 day'
GROUP BY symbol
ORDER BY ticks DESC;
```

## Running the System

### Docker Compose
Both services should be on the same network:

```yaml
# docker-compose.yaml
services:
  mdp-api:
    environment:
      DATABASE_URL: postgres://postgres:postgres@md_postgres:5432/market_data
    depends_on:
      - md_postgres
    networks:
      - market_data_net

  md_postgres:
    image: timescale/timescaledb:2.20.3-pg15-oss
    networks:
      - market_data_net

networks:
  market_data_net:
```

### Starting Consumers
```python
# Start both consumers in parallel
async def main():
    # Setup
    bus = await create_stream_bus()
    store = AsyncStoreClient(DATABASE_URL)
    await store.aopen()
    
    # Create consumers
    batcher = MicroBatcher(bus, store, window_seconds=2)
    tick_consumer = TickConsumer(bus, store, batch_size=100)
    
    # Start both
    await asyncio.gather(
        batcher.start(),
        tick_consumer.start()
    )

asyncio.run(main())
```

## Performance Considerations

### Write Throughput
- **Tick rate**: Up to 10,000 ticks/sec per consumer
- **Batch size**: Default 100 ticks per batch
- **Latency**: ~10-50ms per batch write

### Storage Estimates
- **Raw tick**: ~100 bytes/tick
- **1M ticks/day**: ~100 MB/day (~3 GB/month)
- **After compression**: ~20-30% of original size

### Horizontal Scaling
Multiple TickConsumer instances can run in parallel using consumer groups:

```python
# Consumer 1
TickConsumer(bus, store, consumer_group="ticks", consumer_name="tick-1")

# Consumer 2
TickConsumer(bus, store, consumer_group="ticks", consumer_name="tick-2")
```

Events are distributed across consumers in the same group.

## Troubleshooting

### No ticks in database
1. Check producer is emitting events:
   ```bash
   redis-cli XLEN mdp.events
   ```

2. Check consumer is running:
   ```bash
   # Check logs for TickConsumer
   grep "TickConsumer" pipeline.log
   ```

3. Verify metrics:
   ```promql
   tick_forward_total
   tick_forward_failures_total
   ```

### High failure rate
1. Check database connectivity:
   ```bash
   psql -d market_data -c "SELECT 1"
   ```

2. Check for constraint violations:
   ```sql
   -- Recent errors in logs
   SELECT * FROM pg_stat_database WHERE datname = 'market_data';
   ```

3. Review consumer logs for exceptions

### Consumer lag
1. Check message backlog:
   ```bash
   redis-cli XPENDING mdp.events tick-consumer
   ```

2. Increase batch size or add more consumers
3. Check store write latency metrics

## Success Criteria

- ✅ `tick_data` table created as hypertable
- ✅ `AsyncStoreClient.upsert_ticks()` implemented
- ✅ `TickConsumer` registered and running
- ✅ Ticks appear in database: `SELECT COUNT(*) FROM tick_data`
- ✅ Metrics increment: `tick_forward_total > 0`
- ✅ No errors: `tick_forward_failures_total == 0`
- ✅ Integration tests pass

## Next Steps

### Phase 4 – Tick Analytics
- Time-bucketed tick aggregations
- VWAP calculations
- Spread analysis
- Volume profiling

### Phase 5 – Tick Replay
- Historical tick replay for backtesting
- Tick data export to S3/GCS
- Tick data retention policies

