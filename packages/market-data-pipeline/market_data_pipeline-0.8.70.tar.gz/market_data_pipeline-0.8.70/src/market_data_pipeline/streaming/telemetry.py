"""
Streaming telemetry for market_data_pipeline.

Provides Prometheus metrics for stream processing.
"""

import logging
import time
from prometheus_client import Counter, Gauge, Histogram, start_http_server

logger = logging.getLogger(__name__)

# Stream metrics
STREAM_EVENTS_INGESTED_TOTAL = Counter(
    "stream_events_ingested_total",
    "Total number of events ingested",
    ["bus", "topic", "provider"]
)

STREAM_CONSUMER_LAG_MS = Gauge(
    "stream_consumer_lag_ms",
    "Consumer lag in milliseconds",
    ["topic", "group", "consumer"]
)

# Micro-batch metrics
MICROBATCH_FLUSH_TOTAL = Counter(
    "microbatch_flush_total",
    "Total number of micro-batch flushes",
    ["window_ms", "symbol"]
)

MICROBATCH_FLUSH_ROWS = Counter(
    "microbatch_flush_rows",
    "Total number of rows flushed",
    ["window_ms"]
)

MICROBATCH_WINDOW_LATENCY_MS = Histogram(
    "microbatch_window_latency_ms",
    "Window processing latency in milliseconds",
    ["window_ms"],
    buckets=[10, 50, 100, 200, 500, 1000, 2000, 5000]
)

# Store metrics
STORE_WRITE_DURATION_SECONDS = Histogram(
    "store_write_duration_seconds",
    "Store write duration in seconds",
    ["table"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

STORE_WRITE_ROWS_TOTAL = Counter(
    "store_write_rows_total",
    "Total number of rows written to store",
    ["table", "operation"]
)

# Feature metrics
FEATURES_UPDATE_DURATION_SECONDS = Histogram(
    "features_update_duration_seconds",
    "Feature update duration in seconds",
    ["symbol", "window"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

FEATURES_ACTIVE_WINDOWS = Gauge(
    "features_active_windows",
    "Number of active feature windows",
    ["symbol"]
)

# Inference metrics
INFERENCE_EVAL_DURATION_SECONDS = Histogram(
    "inference_eval_duration_seconds",
    "Inference evaluation duration in seconds",
    ["adapter"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

SIGNALS_EMITTED_TOTAL = Counter(
    "signals_emitted_total",
    "Total number of signals emitted",
    ["name", "adapter"]
)

SIGNALS_STORE_WRITE_DURATION_SECONDS = Histogram(
    "signals_store_write_duration_seconds",
    "Signals store write duration in seconds",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# Error metrics
ERRORS_TOTAL = Counter(
    "errors_total",
    "Total number of errors",
    ["component", "reason"]
)

# SLA metrics
SLA_WINDOW_LATENCY_P95 = Gauge(
    "sla_window_latency_p95_ms",
    "95th percentile window latency in milliseconds",
    ["window_ms"]
)

SLA_CONSUMER_LAG_P95 = Gauge(
    "sla_consumer_lag_p95_ms",
    "95th percentile consumer lag in milliseconds",
    ["topic", "group"]
)

SLA_THROUGHPUT_EVENTS_PER_SECOND = Gauge(
    "sla_throughput_events_per_second",
    "Events per second throughput",
    ["topic"]
)


def start_metrics_server(port: int = 9101) -> None:
    """Start the Prometheus metrics server."""
    try:
        start_http_server(port)
        logger.info(f"Streaming metrics server started on port {port}")
    except Exception as e:
        logger.error(f"Failed to start streaming metrics server: {e}")
        raise


def record_event_ingested(bus: str, topic: str, provider: str) -> None:
    """Record an ingested event."""
    STREAM_EVENTS_INGESTED_TOTAL.labels(bus=bus, topic=topic, provider=provider).inc()


def record_consumer_lag(topic: str, group: str, consumer: str, lag_ms: float) -> None:
    """Record consumer lag."""
    STREAM_CONSUMER_LAG_MS.labels(topic=topic, group=group, consumer=consumer).set(lag_ms)


def record_microbatch_flush(symbol: str, window_ms: int) -> None:
    """Record a micro-batch flush."""
    MICROBATCH_FLUSH_TOTAL.labels(window_ms=window_ms, symbol=symbol).inc()


def record_microbatch_rows(window_ms: int, row_count: int) -> None:
    """Record micro-batch rows."""
    MICROBATCH_FLUSH_ROWS.labels(window_ms=window_ms).inc(row_count)


def record_microbatch_window_latency(window_ms: int, latency_ms: float) -> None:
    """Record window processing latency."""
    MICROBATCH_WINDOW_LATENCY_MS.labels(window_ms=window_ms).observe(latency_ms)


def record_stream_events_ingested(bus: str, topic: str, provider: str) -> None:
    """Record stream events ingested."""
    STREAM_EVENTS_INGESTED_TOTAL.labels(bus=bus, topic=topic, provider=provider).inc()


def record_consumer_lag(topic: str, group: str, consumer: str, lag_ms: float) -> None:
    """Record consumer lag."""
    STREAM_CONSUMER_LAG_MS.labels(topic=topic, group=group, consumer=consumer).set(lag_ms)


def record_store_write_duration(table: str, duration_seconds: float) -> None:
    """Record store write duration."""
    STORE_WRITE_DURATION_SECONDS.labels(table=table).observe(duration_seconds)


def record_store_write_rows(table: str, operation: str, row_count: int) -> None:
    """Record store write rows."""
    STORE_WRITE_ROWS_TOTAL.labels(table=table, operation=operation).inc(row_count)


def record_features_update_duration(symbol: str, window: str, duration_seconds: float) -> None:
    """Record feature update duration."""
    FEATURES_UPDATE_DURATION_SECONDS.labels(symbol=symbol, window=window).observe(duration_seconds)


def record_features_active_windows(symbol: str, window_count: int) -> None:
    """Record active feature windows."""
    FEATURES_ACTIVE_WINDOWS.labels(symbol=symbol).set(window_count)


def record_inference_eval_duration(adapter: str, duration_seconds: float) -> None:
    """Record inference evaluation duration."""
    INFERENCE_EVAL_DURATION_SECONDS.labels(adapter=adapter).observe(duration_seconds)


def record_signals_emitted(signal_name: str, adapter: str, count: int = 1) -> None:
    """Record emitted signals."""
    SIGNALS_EMITTED_TOTAL.labels(name=signal_name, adapter=adapter).inc(count)


def record_signals_store_write_duration(duration_seconds: float) -> None:
    """Record signals store write duration."""
    SIGNALS_STORE_WRITE_DURATION_SECONDS.observe(duration_seconds)


def record_error(component: str, reason: str) -> None:
    """Record an error."""
    ERRORS_TOTAL.labels(component=component, reason=reason).inc()


def record_sla_window_latency_p95(window_ms: int, latency_ms: float) -> None:
    """Record SLA window latency."""
    SLA_WINDOW_LATENCY_P95.labels(window_ms=window_ms).set(latency_ms)


def record_sla_consumer_lag_p95(topic: str, group: str, lag_ms: float) -> None:
    """Record SLA consumer lag."""
    SLA_CONSUMER_LAG_P95.labels(topic=topic, group=group).set(lag_ms)


def record_sla_throughput(topic: str, events_per_second: float) -> None:
    """Record SLA throughput."""
    SLA_THROUGHPUT_EVENTS_PER_SECOND.labels(topic=topic).set(events_per_second)


class StreamingMetrics:
    """Context manager for streaming metrics."""
    
    def __init__(self, component: str, operation: str):
        self.component = component
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            
            if exc_type:
                record_error(self.component, str(exc_type.__name__))
            else:
                # Record success metrics based on component
                if self.component == "microbatch":
                    record_microbatch_window_latency(2000, duration * 1000)
                elif self.component == "store":
                    record_store_write_duration(self.operation, duration)
                elif self.component == "features":
                    record_features_update_duration("unknown", self.operation, duration)
                elif self.component == "inference":
                    record_inference_eval_duration(self.operation, duration)
