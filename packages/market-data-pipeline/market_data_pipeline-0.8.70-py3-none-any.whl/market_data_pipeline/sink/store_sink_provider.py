"""
Provider-based Store Sink (Phase 20.1)
Writes directly to bars_ohlcv via AsyncStoreClient.
Optimized for COPY-based upserts and high-throughput writes.
"""

from __future__ import annotations
import asyncio
import os
import time
from datetime import datetime, timezone
from typing import List, Optional

from loguru import logger
from prometheus_client import Counter, Histogram

from ..context import PipelineContext
from ..errors import SinkError
from ..sink.base import Sink
from ..sink.capabilities import SinkCapabilities, SinkHealth
from ..sink.telemetry import get_sink_telemetry
from ..types import Bar

try:
    from market_data_store.store_client import AsyncStoreClient
except ImportError:
    AsyncStoreClient = None


SINK_NAME = "provider_sink"

# Lazy metric initialization to avoid conflicts
_metrics_initialized = False
PROVIDER_WRITES = None
PROVIDER_FAILS = None
PROVIDER_LATENCY = None

def _get_metrics():
    global _metrics_initialized, PROVIDER_WRITES, PROVIDER_FAILS, PROVIDER_LATENCY
    if not _metrics_initialized:
        try:
            PROVIDER_WRITES = Counter(f"{SINK_NAME}_writes_total", "Total writes to bars_ohlcv", ["pipeline", "tenant"])
            PROVIDER_FAILS = Counter(f"{SINK_NAME}_fails_total", "Failed writes to bars_ohlcv", ["pipeline", "tenant"])
            PROVIDER_LATENCY = Histogram(f"{SINK_NAME}_latency_seconds", "Write latency", ["pipeline", "tenant"])
            _metrics_initialized = True
        except ValueError:
            # Metrics already registered, use existing ones
            pass
    return PROVIDER_WRITES, PROVIDER_FAILS, PROVIDER_LATENCY


class StoreSink(Sink):
    """AsyncStoreClient-backed sink for bars_ohlcv (provider-based)."""

    def __init__(
        self,
        db_uri: Optional[str] = None,
        workers: int = 2,
        queue_max: int = 100,
        default_timeframe: str = "1m",
        ctx: Optional[PipelineContext] = None,
    ):
        if AsyncStoreClient is None:
            raise RuntimeError("AsyncStoreClient not available. Install market_data_store.")

        self.ctx = ctx
        self.tenant = getattr(ctx, "tenant_id", "default")
        self.pipeline = getattr(ctx, "pipeline_id", "unknown")
        self.default_timeframe = default_timeframe

        self.client = AsyncStoreClient(db_uri or os.getenv("DATABASE_URL"))
        self.queue_max = queue_max
        self.workers = workers

        self._queue = asyncio.Queue(maxsize=queue_max)
        self._workers: List[asyncio.Task] = []
        self._closed = False
        self._started = False
        self.telemetry = get_sink_telemetry()
        self._last_commit_at = None
        self._last_error_at = None

    async def start(self):
        if self._started:
            return
        await self.client.aopen()
        for i in range(self.workers):
            self._workers.append(asyncio.create_task(self._worker(f"worker-{i}")))
        self._started = True
        logger.info(f"[ProviderSink] started with {self.workers} workers")

    async def close(self, drain: bool = True):
        self._closed = True
        if drain:
            for _ in range(self.workers):
                await self._queue.put(None)
        await asyncio.gather(*self._workers, return_exceptions=True)
        await self.client.aclose()

    async def write(self, batch: List[Bar]):
        if self._closed:
            raise SinkError("Sink is closed")
        if not batch:
            return
        if not self._started:
            await self.start()
        await self._queue.put(batch)

    async def flush(self) -> None:
        """Force a commit of queued work without closing."""
        if self._queue is None:
            return

        # Wait until queue drains
        while not self._queue.empty():
            await asyncio.sleep(0.01)

    async def _worker(self, worker_id: str):
        while True:
            batch = await self._queue.get()
            if batch is None:
                return
            try:
                await self._process(batch)
            except Exception as e:
                self._last_error_at = datetime.now(timezone.utc)
                PROVIDER_FAILS.labels(self.pipeline, self.tenant).inc()
                logger.error(f"[ProviderSink] worker {worker_id} failed: {e}")

    async def _process(self, batch: List[Bar]):
        start = time.perf_counter()
        try:
            bars = [
                {
                    "provider": bar.source,
                    "symbol": bar.symbol,
                    "interval": getattr(bar, "timeframe", self.default_timeframe),
                    "ts": bar.timestamp,
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": int(bar.volume or 0),
                }
                for bar in batch
            ]
            count = await self.client.upsert_bars(bars)
            writes, fails, latency = _get_metrics()
            if writes:
                writes.labels(self.pipeline, self.tenant).inc(count)
            duration = time.perf_counter() - start
            if latency:
                latency.labels(self.pipeline, self.tenant).observe(duration)
            self._last_commit_at = datetime.now(timezone.utc)
            logger.debug(f"[ProviderSink] wrote {count} bars in {duration:.3f}s")
        except Exception:
            writes, fails, latency = _get_metrics()
            if fails:
                fails.labels(self.pipeline, self.tenant).inc()
            raise

    @property
    def capabilities(self) -> SinkCapabilities:
        return SinkCapabilities.BATCH_WRITES

    async def health(self) -> SinkHealth:
        return SinkHealth(
            connected=self._started and not self._closed,
            queue_depth=self._queue.qsize(),
            in_flight_batches=len(self._workers),
            last_commit_at=self._last_commit_at,
            last_error_at=self._last_error_at,
            retry_count=0,
            detail=f"Provider sink to bars_ohlcv ({self.workers} workers)",
        )

    def get_metrics(self) -> dict:
        """Get sink metrics."""
        return {
            "workers": len(self._workers),
            "default_timeframe": self.default_timeframe,
            "queue_max": self.queue_max,
            "tenant": self.tenant,
            "pipeline": self.pipeline,
        }
