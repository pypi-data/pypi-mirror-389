# Phase 13.0 - Stream Processing Success Checklist

## 🧪 Testing Checklist

| Test | Repo | Goal | Status |
|------|------|------|--------|
| `test_signals_roundtrip` | store | Verify upsert + readback | ✅ |
| `test_stream_pipeline_roundtrip` | pipeline | Verify synthetic event flows through bus → store | ✅ |
| `test_window_assigner` | pipeline | Verify window bucket alignment | ✅ |
| CI workflows run | infra / GitHub | Redis + Postgres integration test | ✅ |
| Prometheus scrape success | infra | Metrics visible | ✅ |

## 🏁 Deliverable Status

| Repo | Tag | Deliverables | Status |
|------|-----|-------------|--------|
| market_data_pipeline | v0.4.0 | Streaming bus + microbatch + telemetry + tests | ✅ |
| market_data_store | v0.2.1 | Signals table + client + migration + tests | ✅ |
| market_data_infra | v1.2.0 | Docker Compose + Prometheus + Grafana + CI | ✅ |
| market_data_core | (unchanged) | Config contracts validated for streaming layer | ✅ |

## ✅ Outcome

After completing Phase 13.0 Part 2:

🚀 **End-to-end event → micro-batch → store → signal pipeline is operational.**

📊 **Prometheus exposes full telemetry for Grafana dashboards.**

🔁 **CI verifies round-trip ingestion and DB consistency.**

🧩 **All repos stay modular: Pipeline (process) ⇢ Store (persist).**

## 🔧 Quick Start

### 1. Start Observability Stack
```bash
docker-compose -f docker-compose.observability.yml up -d
```

### 2. Run Tests
```bash
# Unit tests
pytest tests/unit/test_window_assigner.py -v

# Integration tests
pytest tests/integration/test_stream_to_store_roundtrip.py -v
pytest tests/integration/test_signals_roundtrip.py -v
```

### 3. Start Streaming Pipeline
```bash
# Start synthetic producer
mdp stream produce --config configs/streaming.yaml --provider synthetic

# Start micro-batcher
mdp stream micro-batch --config configs/streaming.yaml --window 2s

# Start inference
mdp stream infer --config configs/streaming.yaml --adapter rules
```

### 4. Monitor Performance
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Pipeline Metrics**: http://localhost:9101/metrics

## 📊 Key Metrics to Monitor

- **Event Ingestion Rate**: `rate(stream_events_ingested_total[5m])`
- **Consumer Lag**: `stream_consumer_lag_ms`
- **Window Latency**: `histogram_quantile(0.95, microbatch_window_latency_ms_bucket)`
- **Store Write Duration**: `histogram_quantile(0.95, store_write_duration_seconds_bucket)`
- **Signal Generation**: `rate(signals_emitted_total[5m])`
- **Error Rate**: `rate(errors_total[5m])`

## 🎯 SLA Targets

- **Latency**: P95 window processing ≤ 1.5× window size
- **Throughput**: ≥ 50k events/min sustained
- **Reliability**: 99.9% uptime, zero data loss
- **Observability**: All metrics visible in Grafana
- **Automation**: CI/CD passes all tests
