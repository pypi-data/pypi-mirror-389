# Phase 4 Verification Checklist

**Purpose:** Ensure tick analytics infrastructure is healthy before Phase 5 (Replay & Backtesting)

---

## 1. Verify TimescaleDB Jobs

### Check Compression Policy for tick_data
```sql
-- Verify tick_data compression policy exists
SELECT 
    job_id,
    hypertable_name,
    config->>'compress_after' as compress_after,
    last_run_status,
    last_successful_finish
FROM timescaledb_information.jobs
WHERE hypertable_name = 'tick_data'
  AND proc_name = 'policy_compression';
```

**Expected Result:**
- `compress_after`: `"7 days"`
- `last_run_status`: `Success` (or NULL if not yet triggered)

### Check Continuous Aggregate Policies
```sql
-- Verify all 6 continuous aggregate refresh policies
SELECT 
    view_name,
    schedule_interval,
    last_run_status,
    last_successful_finish,
    next_start
FROM timescaledb_information.continuous_aggregate_stats
WHERE view_name IN (
    'tick_agg_1m',
    'tick_agg_5m',
    'tick_agg_1h',
    'tick_vwap_daily',
    'tick_spread_stats',
    'tick_rate_stats'
)
ORDER BY view_name;
```

**Expected Result:**
- All 6 views present
- `last_run_status`: `Success` or NULL (if not yet run)
- `next_start`: Should show upcoming refresh times

### Check All Background Jobs
```sql
-- Overview of all TimescaleDB jobs
SELECT 
    job_id,
    proc_name,
    hypertable_name,
    config,
    scheduled,
    last_run_status
FROM timescaledb_information.jobs
ORDER BY job_id;
```

---

## 2. Verify Aggregates Are Populating

### Test 1: Recent tick data exists
```sql
-- Verify ticks are flowing into tick_data
SELECT 
    provider,
    symbol,
    COUNT(*) as tick_count,
    MAX(ts) as latest_tick,
    NOW() - MAX(ts) as lag
FROM tick_data
WHERE ts > NOW() - INTERVAL '10 minutes'
GROUP BY provider, symbol
ORDER BY tick_count DESC;
```

**Expected Result:**
- At least some rows if live ticks are flowing
- `lag` should be < 5 minutes for active symbols

**If Empty:**
- No ticks have been ingested yet (this is OK for initial setup)
- Start TickConsumer to begin ingestion

### Test 2: tick_agg_1m populating
```sql
-- Verify 1-minute aggregates are being created
SELECT 
    provider,
    symbol,
    COUNT(*) as bar_count,
    MAX(bucket) as latest_bucket,
    NOW() - MAX(bucket) as bucket_lag
FROM tick_agg_1m
WHERE bucket > NOW() - INTERVAL '1 hour'
GROUP BY provider, symbol
ORDER BY bar_count DESC
LIMIT 10;
```

**Expected Result:**
- If ticks are flowing: bars appearing within ~1-2 minutes of ticks
- `bucket_lag` should be < 2 minutes

**If Empty but ticks exist:**
```sql
-- Manual refresh to populate
CALL refresh_continuous_aggregate('tick_agg_1m', NULL, NULL);
```

### Test 3: All aggregate views have data
```sql
-- Check row counts for all aggregate views
SELECT 
    'tick_agg_1m' as view,
    COUNT(*) as row_count,
    MAX(bucket) as latest_data
FROM tick_agg_1m
UNION ALL
SELECT 
    'tick_agg_5m' as view,
    COUNT(*) as row_count,
    MAX(bucket) as latest_data
FROM tick_agg_5m
UNION ALL
SELECT 
    'tick_agg_1h' as view,
    COUNT(*) as row_count,
    MAX(bucket) as latest_data
FROM tick_agg_1h
UNION ALL
SELECT 
    'tick_vwap_daily' as view,
    COUNT(*) as row_count,
    MAX(day) as latest_data
FROM tick_vwap_daily
UNION ALL
SELECT 
    'tick_spread_stats' as view,
    COUNT(*) as row_count,
    MAX(bucket) as latest_data
FROM tick_spread_stats
UNION ALL
SELECT 
    'tick_rate_stats' as view,
    COUNT(*) as row_count,
    MAX(bucket) as latest_data
FROM tick_rate_stats
ORDER BY view;
```

**Expected Result:**
- All views have row_count > 0 (after ticks flow)
- `latest_data` should be recent

---

## 3. Verify Metrics Export

### Test Pipeline Metrics Endpoint

#### Check if metrics collection is enabled
```bash
# From your pipeline host
curl -s http://localhost:8083/metrics | grep tick_agg
curl -s http://localhost:8083/metrics | grep tick_rate_per_symbol
```

**Expected Output:**
```
# HELP tick_agg_rows_total Estimated number of rows in tick aggregate views
# TYPE tick_agg_rows_total gauge
tick_agg_rows_total{view="tick_agg_1m"} 1234.0
tick_agg_rows_total{view="tick_agg_5m"} 456.0
...
# HELP tick_rate_per_symbol Approximate ticks per minute...
# TYPE tick_rate_per_symbol gauge
tick_rate_per_symbol{provider="ibkr",symbol="NVDA"} 120.0
...
```

**If Missing:**
- Metrics collection task not running
- Add to pipeline startup (see integration steps below)

### Test Prometheus Scrape (if configured)
```bash
# Query Prometheus directly
curl 'http://prometheus:9090/api/v1/query?query=tick_agg_rows_total'
```

---

## 4. Integration Verification

### Is TickConsumer Running?
```bash
# Check pipeline logs for TickConsumer
docker logs mdp-api 2>&1 | grep "TickConsumer"
```

**Expected:**
```
[TickConsumer] Started: group=tick-consumer, name=tick-1, topic=mdp.events, batch_size=100
[TickConsumer] Forwarded 250 ticks: {'ibkr': 250}
```

### Are Ticks Being Forwarded?
```bash
# Check metrics
curl -s http://localhost:8083/metrics | grep tick_forward_total
```

**Expected:**
```
tick_forward_total{provider="ibkr"} 12345.0
```

### Database Connection from Pipeline
```bash
# Test connection to store from pipeline container
docker exec mdp-api psql $DATABASE_URL -c "SELECT COUNT(*) FROM tick_data;"
```

---

## 5. Enable Metrics Collection (If Not Running)

If `tick_agg_rows_total` metrics are missing, add this to your pipeline service:

### Option A: Add to FastAPI app (runners/api.py)
```python
from market_data_pipeline.metrics_tick_analytics import (
    collect_tick_analytics_metrics,
    close_pool
)
import asyncio

async def metrics_background_task():
    """Background task to collect tick analytics metrics."""
    while True:
        try:
            await collect_tick_analytics_metrics()
        except Exception as exc:
            logger.warning(f"Tick analytics metrics failed: {exc}")
        await asyncio.sleep(30)  # Collect every 30 seconds

@app.on_event("startup")
async def startup_event():
    # ... existing startup code ...
    
    # Start metrics collection
    asyncio.create_task(metrics_background_task())
    logger.info("Started tick analytics metrics collection")

@app.on_event("shutdown")
async def shutdown_event():
    # ... existing shutdown code ...
    
    # Close metrics pool
    await close_pool()
```

### Option B: Standalone Script
```python
# scripts/collect_metrics.py
import asyncio
from market_data_pipeline.metrics_tick_analytics import collect_tick_analytics_metrics

async def main():
    while True:
        await collect_tick_analytics_metrics()
        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 6. Quick Start: Initial Data Population

If you're starting fresh with no tick data:

### Step 1: Start TickConsumer
```python
from market_data_pipeline.streaming.consumers import TickConsumer
from datastore import AsyncStoreClient

store = AsyncStoreClient(DATABASE_URL)
await store.aopen()

consumer = TickConsumer(
    bus=stream_bus,
    store_client=store,
    batch_size=100
)

await consumer.start()
```

### Step 2: Generate Test Ticks
```python
# Using synthetic producer
from market_data_pipeline.streaming.producers.synthetic_ticks import SyntheticTickProducer

producer = SyntheticTickProducer(
    bus=stream_bus,
    symbols=["NVDA", "AAPL", "MSFT"],
    rate_per_symbol=10  # 10 ticks/sec per symbol
)

await producer.start()
```

### Step 3: Wait and Verify
```bash
# Wait 5 minutes for ticks and aggregates to populate
sleep 300

# Check results
psql -d market_data -c "SELECT COUNT(*) FROM tick_data;"
psql -d market_data -c "SELECT COUNT(*) FROM tick_agg_1m;"
```

---

## ✅ Pre-Phase 5 Checklist

Mark each as complete before proceeding:

- [ ] **Jobs Running**: All 6 continuous aggregate policies show `Success` or NULL
- [ ] **Compression Configured**: tick_data compression policy exists (7 days)
- [ ] **Ticks Flowing**: tick_data has recent rows (< 5 min lag)
- [ ] **Aggregates Populating**: tick_agg_1m has rows from last hour
- [ ] **All Views Working**: All 6 views have row_count > 0
- [ ] **Metrics Exposed**: `tick_agg_rows_total` appears in /metrics
- [ ] **Tick Rates Tracked**: `tick_rate_per_symbol` shows active symbols
- [ ] **TickConsumer Active**: Logs show forwarding activity
- [ ] **No Errors**: No failures in `tick_forward_failures_total`

---

## 🐛 Troubleshooting

### Issue: Aggregates not populating

**Cause:** Background jobs not running or delayed

**Solution:**
```sql
-- Check job status
SELECT * FROM timescaledb_information.job_stats
WHERE job_id IN (
    SELECT job_id FROM timescaledb_information.jobs
    WHERE proc_name = 'policy_refresh_continuous_aggregate'
);

-- Manual refresh
CALL refresh_continuous_aggregate('tick_agg_1m', NULL, NULL);
```

### Issue: Metrics returning 0

**Cause:** No data in views yet or metrics collection not running

**Solution:**
1. Verify ticks exist: `SELECT COUNT(*) FROM tick_data;`
2. Manual refresh: `python -m datastore.jobs.tick_analytics`
3. Check metrics task is running in logs

### Issue: High lag in aggregates

**Cause:** Insufficient resources or policy intervals too large

**Solution:**
```sql
-- Reduce policy interval for faster updates
SELECT alter_job(
    (SELECT job_id FROM timescaledb_information.jobs 
     WHERE hypertable_name = 'tick_agg_1m' 
       AND proc_name = 'policy_refresh_continuous_aggregate'),
    schedule_interval => INTERVAL '30 seconds'
);
```

---

## 📊 Sample Healthy Output

```sql
-- Query: SELECT COUNT(*) FROM tick_data WHERE ts > NOW() - INTERVAL '1 hour';
  count  
---------
  36000
(1 row)

-- Query: SELECT view_name, schedule_interval, last_run_status FROM continuous_aggregate_stats;
    view_name      | schedule_interval | last_run_status 
-------------------+-------------------+-----------------
 tick_agg_1m       | 00:01:00          | Success
 tick_agg_5m       | 00:05:00          | Success
 tick_agg_1h       | 01:00:00          | Success
 tick_vwap_daily   | 1 day             | Success
 tick_spread_stats | 00:05:00          | Success
 tick_rate_stats   | 00:01:00          | Success
(6 rows)

-- Metrics:
tick_agg_rows_total{view="tick_agg_1m"} 1440.0
tick_agg_rows_total{view="tick_agg_5m"} 288.0
tick_rate_per_symbol{provider="ibkr",symbol="NVDA"} 120.0
```

---

Once all checks pass, you're ready for **Phase 5: Tick Replay & Backtesting**! 🚀

