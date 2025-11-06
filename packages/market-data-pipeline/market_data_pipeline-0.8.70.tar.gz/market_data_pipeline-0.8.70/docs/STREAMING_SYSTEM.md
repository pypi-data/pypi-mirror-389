# Market Data Pipeline – Stream Processing & Micro-Batch Inference System (Phase 13.0)

## 0️⃣ Objective

Introduce a streaming ingestion tier and a micro-batch inference path that augment the current batch job engine. Target outcomes:

- **Sub-second event capture** (ticks/bars) via a durable queue
- **Micro-batches** (0.5–5s windows) → ordered, deduped, idempotent writes to `bars_ohlcv`
- **Real-time feature windows** (VWAP, rolling OHLCV, returns) for downstream analytics/ML
- **Pluggable inference evaluators** (rules/ML) that emit signals to a new signals topic + signals table
- **Backpressure-safe, horizontally scalable workers** with pacing + SLA telemetry

## 1️⃣ Architecture Overview

```
Providers (IBKR, Synthetic)
        │  (tick/bar events)
        ▼
   Producers (async) ──►  Stream Bus (Redis Streams / Kafka)
        │                      │
        │                      ├─► Micro-Batcher (N-sec windows → ordered → dedup)
        │                      │       ├─► StoreClient (bars_ohlcv upsert)
        │                      │       └─► Feature Windows Cache (per symbol)
        │                      │
        │                      └─► Inference Engine (rules/ML on features)
        │                              ├─► signals topic
        │                              └─► Signals Store (timeseries table)
        │
        └─► Backfill replayer (reads historical → re-enqueue)  [optional]
```

## 2️⃣ Technology Choices

- **Default bus**: Redis Streams (fast start, simple ops, supports consumer groups, persistence)
- **Fallback/scale-up**: Kafka (pluggable via same interface)
- **Windowing**: Tumbling windows (configurable 1s/2s/5s). Optional grace for late events (e.g., 500ms)
- **Serialization**: Compact JSON line (v1 schema) or msgpack; include msg_id, src_ts, ingest_ts
- **Idempotency**: Producer: deterministic event_id (provider+symbol+src_ts+seq). Store: ON CONFLICT + "IS DISTINCT FROM" update guard

## 3️⃣ Data Contracts

### 3.1 Stream Event (v1)
```json
{
  "ver": 1,
  "provider": "ibkr_primary",
  "symbol": "SPY",
  "kind": "tick",
  "interval": "1s",
  "src_ts": "2025-10-24T14:02:01.234567Z",
  "ingest_ts": "2025-10-24T14:02:01.300000Z",
  "o": 425.1, "h": 425.2, "l": 425.0, "c": 425.15, "v": 1200,
  "seq": 183,
  "event_id": "ibkr_primary|SPY|2025-10-24T14:02:01.234567Z|183"
}
```

### 3.2 Signal Event (v1)
```json
{
  "ver": 1,
  "provider": "ibkr_primary",
  "symbol": "SPY",
  "ts": "2025-10-24T14:02:02Z",
  "name": "vwap_cross_up",
  "value": 1.0,
  "score": 0.82,
  "meta": { "window": "1m", "price": 425.15 }
}
```

## 4️⃣ Components & Files

### 4.1 Core Streaming Components

```
market_data_pipeline/
  └─ streaming/
       bus.py                # Redis/Kafka abstraction
       redis_bus.py          # Redis Streams impl
       kafka_bus.py          # Kafka impl (optional)
       producers/
         ibkr_ticks.py       # provider → event
         synthetic_ticks.py
       consumers/
         micro_batcher.py    # windowing + flush
         inference_consumer.py
       features/
         rolling.py          # VWAP/returns/vol windows (deque/state)
       inference/
         engine.py
         adapters/
           rules.py
           sklearn.py        # stubs; load model; predict()
       cli.py                # mdp stream ...
       telemetry.py          # Prom exporter
```

### 4.2 Configuration

**File**: `configs/streaming.yaml`

```yaml
version: 1
bus:
  type: "redis"
  redis:
    uri: ${REDIS_URI:-redis://redis:6379/0}
    stream: "mdp.events"
    signals_stream: "mdp.signals"
    consumer_group: "mdp-consumers"

producers:
  synthetic:
    enabled: true
    symbols: ["SPY", "AAPL", "MSFT"]
    tick_rate: 1.0
    price_volatility: 0.02

micro_batch:
  window_ms: 2000
  max_batch_size: 5000
  allow_late_ms: 500
  flush_timeout_ms: 1000

features:
  windows:
    - { name: "vwap_1m",  horizon: "60s" }
    - { name: "ret_30s",  horizon: "30s" }
    - { name: "vol_5m",   horizon: "300s" }

inference:
  adapters:
    rules:
      enabled: true
      file: "configs/rules.yaml"
    sklearn:
      enabled: false
      model_path: ""

telemetry:
  metrics_port: 9101
  log_level: INFO
```

## 5️⃣ Usage Examples

### 5.1 Start Producers

```bash
# Start synthetic producer
mdp stream produce --config configs/streaming.yaml --provider synthetic

# Start IBKR producer
mdp stream produce --config configs/streaming.yaml --provider ibkr
```

### 5.2 Start Micro-Batcher

```bash
# Start micro-batcher with 2-second windows
mdp stream micro-batch --config configs/streaming.yaml --window 2s
```

### 5.3 Start Inference

```bash
# Start inference with rules adapter
mdp stream infer --config configs/streaming.yaml --adapter rules

# Start inference with sklearn adapter
mdp stream infer --config configs/streaming.yaml --adapter sklearn
```

### 5.4 Inspect Streams

```bash
# Tail events stream
mdp stream tail --topic mdp.events --limit 50

# Tail signals stream
mdp stream tail --topic mdp.signals --limit 20
```

### 5.5 Replay Historical Data

```bash
# Replay a time range into bus
mdp stream replay --dataset spy_1day_history --from "2025-10-01" --to "2025-10-02"
```

## 6️⃣ Telemetry & Monitoring

### 6.1 Prometheus Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `stream_events_ingested_total{bus,topic,provider}` | Counter | Total events ingested |
| `stream_consumer_lag_ms{topic,group,consumer}` | Gauge | Consumer lag in milliseconds |
| `microbatch_flush_total{window_ms,symbol}` | Counter | Total micro-batch flushes |
| `microbatch_flush_rows{window_ms}` | Counter | Total rows flushed |
| `microbatch_window_latency_ms` | Histogram | Window processing latency |
| `store_write_duration_seconds{table}` | Histogram | Store write duration |
| `features_update_duration_seconds{symbol,window}` | Histogram | Feature update duration |
| `inference_eval_duration_seconds{adapter}` | Histogram | Inference evaluation duration |
| `signals_emitted_total{name,adapter}` | Counter | Total signals emitted |
| `errors_total{component,reason}` | Counter | Total errors |

### 6.2 SLA Targets

- **Latency**: p95 micro-batch end-to-end ≤ 1.5× window (e.g., ≤3s for 2s window)
- **Throughput**: ≥ 50k events/min on dev stack without loss
- **Idempotency**: replays produce 0 duplicate persisted rows
- **Signals**: rules engine emits signals with correct keys and stored successfully
- **Observability**: Prom metrics & Grafana panels show lag, throughput, latency
- **Resilience**: consumer crash/restart without data loss (ack+pending tested)

## 7️⃣ Feature Windows

### 7.1 Supported Features

- **VWAP** (Volume Weighted Average Price)
- **Returns** (price changes over time)
- **Volatility** (standard deviation of returns)
- **RSI** (Relative Strength Index)
- **Momentum** (price momentum over time)
- **Skewness** and **Kurtosis** (distribution moments)

### 7.2 Window Configuration

```yaml
features:
  windows:
    - name: "vwap_1m"
      horizon: "60s"      # 1 minute window
    - name: "ret_30s"
      horizon: "30s"      # 30 second window
    - name: "vol_5m"
      horizon: "300s"     # 5 minute window
```

## 8️⃣ Inference Adapters

### 8.1 Rules Adapter

```yaml
inference:
  adapters:
    rules:
      enabled: true
      file: "configs/rules.yaml"
```

**Rules Configuration** (`configs/rules.yaml`):
```yaml
- name: "price_momentum_up"
  condition: "momentum > 0.01"
  signal: 1.0
  score: 0.8

- name: "price_momentum_down"
  condition: "momentum < -0.01"
  signal: -1.0
  score: 0.8

- name: "high_volatility"
  condition: "volatility > 0.3"
  signal: 0.0
  score: 0.9

- name: "rsi_overbought"
  condition: "rsi > 70"
  signal: -1.0
  score: 0.7

- name: "rsi_oversold"
  condition: "rsi < 30"
  signal: 1.0
  score: 0.7
```

### 8.2 Sklearn Adapter

```yaml
inference:
  adapters:
    sklearn:
      enabled: true
      model_path: "models/signal_model.pkl"
```

## 9️⃣ Backpressure & Fault Tolerance

- **Consumer groups** (Redis/Kafka) → horizontal scale
- **Poison pill handling**: DLQ topic for malformed events
- **At-least-once semantics** with idempotent store upserts
- **Rebalancing**: on crash, another consumer claims pending messages
- **Replay**: pipeline CLI to re-enqueue historical ranges for recovery

## 🔟 Testing Plan

### 10.1 Unit Tests

- `test_window_assigner.py` — boundary cases, late allowance
- `test_feature_rolling.py` — VWAP/returns/vol windows with resets
- `test_inference_rules.py` — rules engine determinism

### 10.2 Integration Tests

- `test_stream_to_store_roundtrip.py` — synthetic → micro-batch → store (idempotent)
- `test_signals_emission.py` — features → inference → signals store + topic
- `test_consumer_recovery.py` — restart mid-window; no duplicates; no data loss

### 10.3 Performance Tests

- Ingest 50k events/min sustained; p95 window_latency under target
- Consumer lag < 2×window over rolling 1m
- No ack backlog growth over 5m window

## 1️⃣1️⃣ Common Failure Scenarios & Recovery

### 11.1 Event Time vs Processing Time Skew

**Mitigation**: `allow_late_ms` + watermarking; order within symbol

### 11.2 Hot Symbols Dominating Windows

**Mitigation**: Per-symbol sharding key; bounded batch size

### 11.3 Store Write Spikes

**Mitigation**: Batch size cap + async writer + COPY path

### 11.4 Queue Persistence Loss (Redis)

**Mitigation**: AOF enabled; snapshot schedule; Kafka option for HA

### 11.5 ML Model Latency

**Mitigation**: Async inference pool; circuit breaker → rules fallback

## 1️⃣2️⃣ Success Criteria

| Category | Goal | Metric |
|----------|------|--------|
| Functional | Run synthetic live → bars_ohlcv → job_runs success | ✅ All rows persisted + audit entry created |
| Performance | Throughput ≥ 50k events/min sustained | Measured via StoreClient metrics |
| Reliability | Retry & pacing compliance 100% | No provider throttling violations |
| Observability | Metrics and heartbeats visible in Grafana | ✅ Prometheus targets healthy |
| Automation | CI/CD tag v0.4.0-pipeline published | ✅ Build & test pass |

## 1️⃣3️⃣ Timeline

| Task | ETA |
|------|-----|
| Bus abstraction + Redis impl + CLI | 1 day |
| Producers (synthetic + IBKR hook) | 1 day |
| Micro-batcher + store writes | 1–2 days |
| Features + inference (rules) | 1 day |
| Signals table + writer | 0.5 day |
| Telemetry + dashboards + docs | 1 day |
| **Total** | **~5–6 days** |

## 1️⃣4️⃣ Monitoring and Testing

### 1️⃣4️⃣1️⃣ Prometheus Metrics

The streaming system exposes comprehensive metrics on port 9101:

- **Stream Events**: `stream_events_ingested_total{bus,topic,provider}`
- **Consumer Lag**: `stream_consumer_lag_ms{topic,group,consumer}`
- **Micro-batch Processing**: `microbatch_flush_total{window_ms,symbol}`
- **Window Latency**: `microbatch_window_latency_ms` (histogram)
- **Store Performance**: `store_write_duration_seconds{table}`
- **Feature Computation**: `features_update_duration_seconds{symbol,window}`
- **Inference Performance**: `inference_eval_duration_seconds{adapter}`
- **Signal Generation**: `signals_emitted_total{name,adapter}`
- **Error Tracking**: `errors_total{component,reason}`

### 1️⃣4️⃣2️⃣ Grafana Dashboards

Pre-configured dashboards provide real-time monitoring:

- **Streaming Overview**: Event rates, consumer lag, throughput
- **Micro-batch Performance**: Window latency, flush rates, batch sizes
- **Store Operations**: Write duration, row counts, error rates
- **Feature Computation**: Update duration, active windows
- **Inference Engine**: Evaluation time, signal generation
- **Error Monitoring**: Component failures, retry rates

### 1️⃣4️⃣3️⃣ Integration Tests

Comprehensive test suite validates the complete pipeline:

```bash
# Unit tests for window assignment
pytest tests/unit/test_window_assigner.py -v

# Integration tests for stream processing
pytest tests/integration/test_stream_to_store_roundtrip.py -v

# Signals storage tests
pytest tests/integration/test_signals_roundtrip.py -v

# Full CI/CD pipeline with Redis + PostgreSQL
pytest -m "not slow" --maxfail=1 --disable-warnings -q
```

### 1️⃣4️⃣4️⃣ Docker Compose Stack

Complete observability stack with:

```bash
# Start full stack
docker-compose -f docker-compose.observability.yml up -d

# Services included:
# - Redis (streaming backend)
# - PostgreSQL + TimescaleDB (storage)
# - Prometheus (metrics collection)
# - Grafana (dashboards)
# - Market Data Pipeline (streaming services)
```

### 1️⃣4️⃣5️⃣ CI/CD Integration

Automated testing with GitHub Actions:

- **Stream Tests**: Redis + PostgreSQL integration
- **Unit Tests**: Window assignment, aggregation logic
- **Integration Tests**: End-to-end pipeline validation
- **Smoke Tests**: Basic component functionality
- **Performance Tests**: Latency and throughput validation

## 1️⃣4️⃣ Core Separation Philosophy

| Layer | Role | Lives In | Description |
|-------|------|----------|-------------|
| **Core** | Contracts, runtime protocols, config system | `market_data_core` | Defines how data should look and flow (Bar, Signal, StorageConfig, Provider, etc.) |
| **Pipeline** | Execution, orchestration, runtime logic | `market_data_pipeline` | Does the work — reads from streams, batches, aggregates, calls store clients |
| **Store** | Data persistence, schema, migration, read/write APIs | `market_data_store` | Owns the database — tables, migrations, insert/update/delete logic |
| **Cockpit** | UI + APIs + agents | `market_data_cockpit` | Observes and controls everything (reads from Store, triggers Pipeline) |

### 1️⃣4️⃣1️⃣ What belongs in `market_data_pipeline`

The processing machinery and streaming logic:

| File | Purpose |
|------|--------|
| `streaming/bus.py`, `redis_bus.py` | Queue interfaces & drivers |
| `streaming/micro_batcher.py` | Window aggregation and flush orchestration |
| `features/rolling.py` | Rolling-window computations |
| `inference/engine.py`, `adapters/rules.py` | Signal generation logic |
| `telemetry.py` | Prometheus metrics for ingestion performance |
| `cli.py` | Commands like `mdp stream produce` / `mdp stream micro-batch` |
| `config/streaming.yaml` | Stream runtime config |

**The pipeline never knows SQL, never declares tables, and never runs migrations — it just calls StoreClient.**

### 1️⃣4️⃣2️⃣ What belongs in `market_data_store`

The data schema, persistence logic, and auditing:

| File | Purpose |
|------|--------|
| `migrations/versions/0003_add_signals_table.py` | Adds the new signals hypertable |
| `src/datastore/writes_signals.py` | SignalsStoreClient — upsert signals efficiently |
| `src/datastore/models.py` | ORM or record models (if using SQLAlchemy) |
| `src/datastore/queries_signals.py` | Simple queries to fetch signals, metrics, etc. |
| `src/datastore/__init__.py` | Export clients (StoreClient, SignalsStoreClient, JobRunTracker) |
| `tests/integration/test_signals_roundtrip.py` | Verify writes + reads |
| `docker/initdb.d/02_signals.sql` | Optional bootstrap SQL for Docker |

**So: Pipeline → StoreClient, never directly into Postgres.**
