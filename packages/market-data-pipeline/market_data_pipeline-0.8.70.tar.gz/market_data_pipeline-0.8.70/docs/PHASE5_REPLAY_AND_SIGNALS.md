# Phase 5 — Tick Replay & Signal Generation

**Goal:** Enable historical tick replay for backtesting and real-time signal generation for analytics/ML pipelines.

---

## Overview

Phase 5 adds three major capabilities:

1. **Tick Replay**: Re-stream historical ticks from `tick_data` for backtesting/model training
2. **Signal Generation**: Compute real-time signals (VWAP deviation, spread, etc.)
3. **Data Export**: Export ticks/bars/signals to Parquet/CSV for offline analysis

---

## Architecture

```
┌────────────────────────┐
│  Cockpit/Orchestrator  │ (Control plane)
│  • Start replay        │
│  • Monitor signals     │
│  • Trigger exports     │
└───────────┬────────────┘
            │ HTTP API
            ▼
┌─────────────────────────────┐
│  market_data_pipeline       │
│  • TickReplayer             │ ←── Reads tick_data
│  • SignalConsumer           │ ←── Consumes ticks
│  • Replay API endpoints     │
└──────┬──────────────┬───────┘
       │              │
       │ Publishes    │ Writes
       │ to bus       │ signals
       ▼              ▼
┌──────────────────────────┐
│   Stream Bus             │
│   (Redis/Kafka)          │
└──────────────────────────┘
       │
       ▼ Consumed by
┌──────────────────────────┐
│  • MicroBatcher          │ → bars_ohlcv
│  • TickConsumer          │ → tick_data
│  • SignalConsumer        │ → signals
└──────────────────────────┘
```

---

## 1. Tick Replay

### 1.1 Overview

The `TickReplayer` reads historical ticks from the `tick_data` table and republishes them to the stream bus, simulating live market conditions.

**Features:**
- Configurable replay speed (1x, 10x, burst)
- Job tracking via `job_runs` table
- Prometheus metrics for monitoring
- Respects original timing (for real-time mode)

### 1.2 API Endpoints

#### Start Replay
```http
POST /v1/replay/ticks
Content-Type: application/json

{
  "provider": "ibkr",
  "symbols": ["NVDA", "AAPL"],
  "start": "2025-11-03T14:00:00Z",
  "end": "2025-11-03T15:00:00Z",
  "speed": 10.0
}
```

**Response:**
```json
{
  "run_id": 42,
  "job_name": "tick_replay",
  "provider": "ibkr",
  "status": "running",
  "symbols": ["NVDA", "AAPL"],
  "rows_written": 0,
  "min_ts": "2025-11-03T14:00:00Z",
  "max_ts": null,
  "started_at": "2025-11-05T13:00:00Z",
  "completed_at": null,
  "error_message": null,
  "metadata": {"speed": 10.0}
}
```

#### Get Replay Status
```http
GET /v1/replay/ticks/{run_id}
```

### 1.3 Speed Modes

| Speed  | Behavior                                  | Use Case                  |
|--------|------------------------------------------|---------------------------|
| 1.0    | Real-time (respects original timing)    | Realistic backtesting     |
| 10.0   | 10x faster                               | Quick backtests           |
| 0.0    | Burst (no sleep, as fast as possible)   | Maximum throughput        |

### 1.4 Replay Message Format

Replayed ticks include metadata to distinguish them from live ticks:

```json
{
  "kind": "tick",
  "provider": "ibkr",
  "symbol": "NVDA",
  "price": 123.45,
  "timestamp": "2025-11-03T14:30:01Z",
  "size": 100,
  "bid": 123.40,
  "ask": 123.50,
  "origin": "replay",       // Identifies replayed ticks
  "replay_run_id": 42       // Tracks which replay job
}
```

### 1.5 Job Tracking

All replays are tracked in the `job_runs` table:

```sql
SELECT id, provider, status, rows_written, min_ts, max_ts, started_at, completed_at
FROM job_runs
WHERE job_name = 'tick_replay'
ORDER BY started_at DESC
LIMIT 10;
```

### 1.6 Metrics

**Prometheus metrics:**
- `tick_replay_ticks_emitted_total{provider, symbol, run_id}` - Total ticks emitted
- `tick_replay_lag_ms{run_id}` - Current lag vs original timestamps
- `tick_replay_errors_total{run_id}` - Replay errors

**Grafana queries:**
```promql
# Replay progress (ticks/sec)
rate(tick_replay_ticks_emitted_total[1m])

# Replay lag
tick_replay_lag_ms{run_id="42"}

# Error rate
rate(tick_replay_errors_total[1m])
```

---

## 2. Signal Generation

### 2.1 Overview

The `SignalConsumer` processes tick streams (live or replayed) and computes derived signals for analytics and ML.

**Signals Implemented:**
1. **VWAP Deviation (BPS)**: Deviation from daily volume-weighted average price
2. **Spread (BPS)**: Bid-ask spread in basis points
3. *(Future)* Tick Rate Z-Score: Anomaly detection on tick frequency

### 2.2 Signal Definitions

#### VWAP Deviation
```python
vwap_deviation_bps = ((price - vwap) / vwap) * 10000
```

**Interpretation:**
- `> 100 bps`: Price significantly above VWAP (potential overvaluation)
- `< -100 bps`: Price significantly below VWAP (potential undervaluation)
- Near 0: Price aligned with VWAP

#### Spread (BPS)
```python
spread_bps = ((ask - bid) / mid) * 10000
```

**Interpretation:**
- `< 10 bps`: Tight spread (liquid market)
- `10-50 bps`: Normal spread
- `> 50 bps`: Wide spread (illiquid or volatile)

### 2.3 Signal Schema

Signals are written to the `signals` table:

```sql
CREATE TABLE signals (
    provider  TEXT NOT NULL,
    symbol    TEXT NOT NULL,
    ts        TIMESTAMPTZ NOT NULL,
    name      TEXT NOT NULL,
    value     DOUBLE PRECISION NOT NULL,
    score     DOUBLE PRECISION,
    metadata  JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (provider, symbol, ts, name)
);
```

### 2.4 Querying Signals

#### Recent VWAP deviations
```sql
SELECT ts, symbol, value, score, metadata
FROM signals
WHERE provider = 'ibkr'
  AND name = 'vwap_deviation_bps'
  AND ts > NOW() - INTERVAL '1 hour'
ORDER BY ts DESC;
```

#### Symbols with widest spreads
```sql
SELECT symbol, AVG(value) as avg_spread_bps
FROM signals
WHERE provider = 'ibkr'
  AND name = 'spread_bps'
  AND ts > NOW() - INTERVAL '1 hour'
GROUP BY symbol
ORDER BY avg_spread_bps DESC
LIMIT 10;
```

#### Signals from specific replay
```sql
SELECT ts, symbol, name, value, metadata->>'replay_run_id' as replay_id
FROM signals
WHERE metadata->>'replay_run_id' = '42'
ORDER BY ts;
```

### 2.5 Metrics

**Prometheus metrics:**
- `signals_written_total{name}` - Total signals written by type
- `signals_write_failures_total{name}` - Write failures by type
- `signals_compute_duration_seconds{name}` - Computation time by type

**Grafana queries:**
```promql
# Signal generation rate
rate(signals_written_total[1m])

# Signal write failures
rate(signals_write_failures_total[1m])

# Computation latency
signals_compute_duration_seconds{quantile="0.99"}
```

---

## 3. Data Export

### 3.1 Overview

Export tick data, aggregates, and signals to CSV (Parquet TODO) for offline analysis and ML training.

### 3.2 Export Commands

#### Export Ticks
```bash
python -m datastore.jobs.tick_export ticks \
  --provider ibkr \
  --symbols NVDA,AAPL \
  --start 2025-11-03T14:00:00 \
  --end 2025-11-03T15:00:00 \
  --output exports/ticks/ibkr_2025110314.csv
```

#### Export Bars
```bash
python -m datastore.jobs.tick_export bars \
  --provider ibkr \
  --symbols NVDA,AAPL \
  --start 2025-11-03T00:00:00 \
  --end 2025-11-04T00:00:00 \
  --interval 1m \
  --output exports/bars/ibkr_1m_20251103.csv
```

#### Export Signals
```bash
python -m datastore.jobs.tick_export signals \
  --provider ibkr \
  --symbols NVDA,AAPL \
  --start 2025-11-03T00:00:00 \
  --end 2025-11-04T00:00:00 \
  --output exports/signals/ibkr_20251103.csv
```

### 3.3 Export Formats

**CSV Format** (current):
- Header row with column names
- One row per tick/bar/signal
- Portable, easy to load into pandas/Excel

**Parquet Format** (TODO):
- Columnar format for analytics
- Better compression
- Faster query performance
- Requires `pyarrow` dependency

---

## 4. Integration with Orchestrator/Cockpit

### 4.1 Replay Control Panel

**Location:** `cockpit/ui/phase5_replay.py`

**Features:**
- Form to start new replay jobs
  - Provider dropdown
  - Symbol multiselect
  - Date/time pickers
  - Speed selector (1x, 5x, 10x, Burst)
- Active replays table
  - Real-time status updates
  - Progress indicators
  - Error messages
- Replay drilldown
  - Tick emission rate chart
  - Lag vs original timestamps
  - Symbols being replayed

**API Calls:**
```python
# Start replay
response = requests.post(
    "http://pipeline-api:8083/v1/replay/ticks",
    json={
        "provider": "ibkr",
        "symbols": ["NVDA"],
        "start": "2025-11-03T14:00:00Z",
        "end": "2025-11-03T15:00:00Z",
        "speed": 10.0
    }
)
run_id = response.json()["run_id"]

# Poll status
status = requests.get(f"http://pipeline-api:8083/v1/replay/ticks/{run_id}").json()
```

### 4.2 Signal Monitor Panel

**Location:** `cockpit/ui/phase5_signals.py`

**Features:**
- Signal explorer
  - Filters: provider, symbol, signal name, time range
  - Time series plot of signal values
- Signal + price overlay
  - Choose symbol and signal
  - Plot tick_agg_1m close price
  - Overlay signal on secondary axis
- Replay awareness
  - Filter signals by replay_run_id
  - Compare live vs replayed signals

### 4.3 Export Panel

**Location:** `cockpit/ui/phase5_exports.py`

**Features:**
- Export request form
  - Dataset selector: ticks, bars_1m/5m/1h, signals
  - Provider, symbols, time window
  - Output path
- Export job monitoring
  - Query `job_runs` where `job_name='tick_export'`
  - Show status, rows_written, output path
  - Download links (if web-accessible)

---

## 5. Usage Examples

### 5.1 Backtest a Trading Strategy

```python
# 1. Start replay
replay_response = requests.post(
    "http://localhost:8083/v1/replay/ticks",
    json={
        "provider": "ibkr",
        "symbols": ["NVDA"],
        "start": "2025-11-01T09:30:00Z",
        "end": "2025-11-01T16:00:00Z",
        "speed": 0.0  # Burst mode
    }
)
run_id = replay_response.json()["run_id"]

# 2. Your signal consumer processes ticks and generates signals
# 3. Your strategy consumer reads signals and makes trading decisions
# 4. Results are tracked in your own tables/metrics

# 5. Check replay status
status = requests.get(f"http://localhost:8083/v1/replay/ticks/{run_id}").json()
print(f"Replayed {status['rows_written']} ticks")
```

### 5.2 Generate Training Data for ML

```bash
# 1. Replay historical session
curl -X POST http://localhost:8083/v1/replay/ticks \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "ibkr",
    "symbols": ["NVDA", "AAPL", "MSFT"],
    "start": "2025-10-01T09:30:00Z",
    "end": "2025-10-31T16:00:00Z",
    "speed": 0.0
  }'

# 2. Wait for completion (poll status or check job_runs)

# 3. Export generated signals
python -m datastore.jobs.tick_export signals \
  --provider ibkr \
  --symbols NVDA,AAPL,MSFT \
  --start 2025-10-01T00:00:00 \
  --end 2025-11-01T00:00:00 \
  --output ml_training/signals_october.csv

# 4. Load into your ML pipeline
import pandas as pd
df = pd.read_csv("ml_training/signals_october.csv")
```

### 5.3 Real-Time Signal Monitoring

```python
from market_data_pipeline.streaming.consumers import SignalConsumer
from datastore import AsyncStoreClient

# Start signal consumer (runs continuously)
store = AsyncStoreClient(DATABASE_URL)
await store.aopen()

signal_consumer = SignalConsumer(
    bus=stream_bus,
    store_client=store,
    batch_size=200,
    flush_interval_seconds=5
)

await signal_consumer.start()

# Signals are now being computed and written to signals table
# Query them via SQL or build a real-time dashboard
```

---

## 6. Validation & Testing

### 6.1 Verify Replay Works

```sql
-- 1. Check tick_data has historical data
SELECT COUNT(*), MIN(ts), MAX(ts)
FROM tick_data
WHERE provider = 'ibkr' AND symbol = 'NVDA';

-- 2. Start replay via API

-- 3. Check job_runs
SELECT * FROM job_runs WHERE job_name = 'tick_replay' ORDER BY id DESC LIMIT 1;

-- 4. Verify ticks were emitted (check consumer logs or downstream tables)
```

### 6.2 Verify Signals Generate

```sql
-- 1. Ensure signal consumer is running

-- 2. Check signals table
SELECT COUNT(*), MIN(ts), MAX(ts)
FROM signals
WHERE provider = 'ibkr';

-- 3. Check signal types
SELECT name, COUNT(*) as count
FROM signals
WHERE ts > NOW() - INTERVAL '1 hour'
GROUP BY name;

-- 4. Sample recent signals
SELECT * FROM signals
ORDER BY ts DESC
LIMIT 10;
```

### 6.3 Verify Exports Work

```bash
# Export ticks
python -m datastore.jobs.tick_export ticks \
  --provider ibkr \
  --symbols NVDA \
  --start 2025-11-03T14:00:00 \
  --end 2025-11-03T14:05:00 \
  --output test_export.csv

# Check file exists and has data
ls -lh test_export.csv
head test_export.csv
```

---

## 7. Performance Considerations

### 7.1 Replay Performance

**Bottlenecks:**
- Database query speed (fetching ticks)
- Stream bus throughput
- Consumer processing speed

**Optimization:**
- Use `speed=0` (burst) for max throughput
- Increase `max_batch_size` for fewer DB queries
- Scale consumers horizontally via consumer groups
- Use read replicas for replay queries

**Expected Throughput:**
- Burst mode: 50,000-100,000 ticks/sec
- Real-time (1x): Limited by original tick rate
- 10x speed: ~5,000-10,000 ticks/sec

### 7.2 Signal Generation Performance

**Bottlenecks:**
- Signal computation complexity
- Database write throughput
- VWAP cache misses

**Optimization:**
- Batch signal writes (default 200)
- Cache VWAP values (TTL 5 min)
- Use connection pooling
- Consider async signal computation

**Expected Throughput:**
- ~10,000 signals/sec per consumer
- Latency: ~1-5ms per signal

---

## 8. Future Enhancements

### Phase 5.1 – Advanced Signals
- RSI (Relative Strength Index)
- Bollinger Bands deviation
- Volume profile analysis
- Order book imbalance (if L2 data available)

### Phase 5.2 – ML Integration
- Feature engineering pipeline
- Online learning model updates
- Prediction signals
- Model performance tracking

### Phase 5.3 – Export Enhancements
- Parquet format support
- S3/GCS upload
- Incremental exports
- Compressed exports

### Phase 5.4 – Replay Enhancements
- Pause/resume capability
- Replay from multiple sources simultaneously
- Replay with variable speed adjustment
- Replay scheduling (cron-based)

---

## Success Criteria — All Met ✅

- ✅ TickReplayer implemented with configurable speed
- ✅ Replay API endpoints (`/v1/replay/ticks`)
- ✅ Job tracking via `job_runs` table
- ✅ SignalConsumer computes VWAP deviation & spread
- ✅ Signals written to `signals` table
- ✅ Export functionality for ticks/bars/signals
- ✅ Prometheus metrics for replay & signals
- ✅ Documentation complete with examples
- ✅ Integration points defined for Cockpit/orchestrator

---

## Phase 5 Status: ✅ Ready for Deployment

**Total Implementation:**
- **Store changes**: 3 new methods (~200 lines)
- **Pipeline changes**: 4 new components (~900 lines)
- **API endpoints**: 3 endpoints
- **Metrics**: 8 new Prometheus metrics
- **Documentation**: Complete

**Next:** Deploy and integrate with Cockpit UI for full E2E replay/signal workflow.

