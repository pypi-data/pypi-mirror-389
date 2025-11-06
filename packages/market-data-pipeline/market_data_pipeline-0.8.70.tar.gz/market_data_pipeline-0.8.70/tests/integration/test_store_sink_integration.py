"""
Integration tests for StoreSink with market-data-store.

Tests the integration between Pipeline's StoreSink and market-data-store's
AsyncBatchProcessor for persisting market data.

These tests verify:
- Batch processing and persistence
- Backpressure handling
- Error recovery and retries
- Idempotency
"""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from market_data_pipeline.context import PipelineContext
from market_data_pipeline.sink.store import StoreSink
from market_data_pipeline.types import Bar


class MockAsyncBatchProcessor:
    """Mock AsyncBatchProcessor for testing."""
    
    def __init__(self, fail_count: int = 0):
        self.upsert_calls: list[list[dict]] = []
        self.fail_count = fail_count
        self._call_count = 0
    
    async def upsert_bars(self, records: list[dict]) -> None:
        """Mock upsert_bars that can fail N times."""
        self._call_count += 1
        if self._call_count <= self.fail_count:
            raise Exception(f"Simulated failure {self._call_count}")
        self.upsert_calls.append(records)
    
    async def close(self) -> None:
        """Mock close."""
        pass


@pytest.fixture
def mock_batch_processor():
    """Create a mock batch processor."""
    return MockAsyncBatchProcessor()


@pytest.fixture
def sample_bars():
    """Create sample bars for testing."""
    now = datetime.now(timezone.utc)
    return [
        Bar(
            symbol="AAPL",
            timestamp=now,
            open=Decimal("150.00"),
            high=Decimal("151.00"),
            low=Decimal("149.50"),
            close=Decimal("150.50"),
            volume=Decimal("1000000"),
            source="test",
        ),
        Bar(
            symbol="MSFT",
            timestamp=now,
            open=Decimal("300.00"),
            high=Decimal("301.00"),
            low=Decimal("299.50"),
            close=Decimal("300.50"),
            volume=Decimal("500000"),
            source="test",
        ),
    ]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_store_sink_write_batch(mock_batch_processor, sample_bars):
    """
    Test StoreSink can write batches to AsyncBatchProcessor.
    
    This verifies basic integration with market-data-store.
    """
    ctx = PipelineContext(tenant_id="test", pipeline_id="test_pipeline")
    sink = StoreSink(
        batch_processor=mock_batch_processor,
        workers=1,
        queue_max=10,
        ctx=ctx
    )
    
    # Start sink
    await sink.start()
    
    # Write batch
    await sink.write(sample_bars)
    
    # Flush and close
    await sink.flush()
    await sink.close()
    
    # Verify batch was processed
    assert len(mock_batch_processor.upsert_calls) == 1
    assert len(mock_batch_processor.upsert_calls[0]) == 2
    
    # Verify record structure
    record = mock_batch_processor.upsert_calls[0][0]
    assert record["symbol"] == "AAPL"
    assert record["open"] == 150.00
    assert record["high"] == 151.00
    assert record["low"] == 149.50
    assert record["close"] == 150.50
    assert record["volume"] == 1000000.0
    assert record["source"] == "test"
    assert "idempotency_key" in record


@pytest.mark.asyncio
@pytest.mark.integration
async def test_store_sink_backpressure_block(mock_batch_processor, sample_bars):
    """
    Test StoreSink backpressure with block policy.
    
    This verifies that the sink properly handles backpressure
    by blocking when the queue is full.
    """
    sink = StoreSink(
        batch_processor=mock_batch_processor,
        workers=1,
        queue_max=2,  # Small queue
        backpressure_policy="block"
    )
    
    await sink.start()
    
    # Fill queue
    await sink.write(sample_bars)
    await sink.write(sample_bars)
    
    # Next write should block briefly until worker processes queue
    await sink.write(sample_bars)
    
    await sink.flush()
    await sink.close()
    
    # All batches should be processed
    assert len(mock_batch_processor.upsert_calls) == 3


@pytest.mark.asyncio
@pytest.mark.integration
async def test_store_sink_backpressure_drop_oldest(mock_batch_processor, sample_bars):
    """
    Test StoreSink backpressure with drop_oldest policy.
    
    This verifies that the sink drops oldest batches when queue is full.
    Note: Even with workers=1, the sink will process batches. The drop_oldest
    policy means that if the queue fills up, the oldest batch is dropped.
    """
    sink = StoreSink(
        batch_processor=mock_batch_processor,
        workers=1,
        queue_max=2,
        backpressure_policy="drop_oldest"
    )
    
    await sink.start()
    
    # Write batches - with small queue, may drop some
    await sink.write(sample_bars)
    await sink.write(sample_bars)
    await sink.write(sample_bars)
    
    # Flush and close to process remaining
    await sink.flush()
    await sink.close()
    
    # At least some batches should be processed (exact number depends on timing)
    assert len(mock_batch_processor.upsert_calls) >= 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_store_sink_retry_on_failure():
    """
    Test StoreSink retries on transient failures.
    
    This verifies that the sink properly retries failed writes
    with exponential backoff.
    """
    # Create processor that fails twice then succeeds
    failing_processor = MockAsyncBatchProcessor(fail_count=2)
    
    ctx = PipelineContext(tenant_id="test", pipeline_id="test_retry")
    sink = StoreSink(
        batch_processor=failing_processor,
        workers=1,
        queue_max=10,
        ctx=ctx
    )
    
    now = datetime.now(timezone.utc)
    bars = [Bar(
        symbol="TEST",
        timestamp=now,
        open=Decimal("100.00"),
        high=Decimal("100.00"),
        low=Decimal("100.00"),
        close=Decimal("100.00"),
        volume=Decimal("100"),
        source="test",
    )]
    
    await sink.start()
    await sink.write(bars)
    
    # Give time for retries
    await asyncio.sleep(0.5)
    
    await sink.flush()
    await sink.close()
    
    # Should eventually succeed after retries
    assert len(failing_processor.upsert_calls) == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_store_sink_idempotency_keys(mock_batch_processor):
    """
    Test StoreSink generates idempotency keys.
    
    This verifies that the sink properly generates idempotency keys
    for deduplication in the store.
    """
    ctx = PipelineContext(tenant_id="test_tenant", pipeline_id="test_pipe")
    sink = StoreSink(
        batch_processor=mock_batch_processor,
        workers=1,
        queue_max=10,
        ctx=ctx
    )
    
    now = datetime.now(timezone.utc)
    bars = [Bar(
        symbol="IDEMPOTENT",
        timestamp=now,
        open=Decimal("100.00"),
        high=Decimal("100.00"),
        low=Decimal("100.00"),
        close=Decimal("100.00"),
        volume=Decimal("100"),
        source="test",
    )]
    
    await sink.start()
    await sink.write(bars)
    await sink.flush()
    await sink.close()
    
    # Verify idempotency key was generated
    record = mock_batch_processor.upsert_calls[0][0]
    assert "idempotency_key" in record
    
    # Key should contain tenant, pipeline, symbol, and timestamp
    key = record["idempotency_key"]
    assert "test_tenant" in key
    assert "test_pipe" in key
    assert "IDEMPOTENT" in key


@pytest.mark.asyncio
@pytest.mark.integration
async def test_store_sink_health_check(mock_batch_processor, sample_bars):
    """
    Test StoreSink health() method.
    
    This verifies that the sink provides health information
    for monitoring systems.
    """
    sink = StoreSink(
        batch_processor=mock_batch_processor,
        workers=1,
        queue_max=10
    )
    
    # Health before start
    health = await sink.health()
    assert health.connected is False
    
    # Start sink
    await sink.start()
    
    # Health after start
    health = await sink.health()
    assert health.connected is True
    assert health.queue_depth >= 0
    
    # Write some data
    await sink.write(sample_bars)
    
    health = await sink.health()
    assert health.queue_depth >= 0  # May be 0 or 1 depending on processing speed
    
    await sink.flush()
    await sink.close()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_store_sink_multiple_workers(mock_batch_processor, sample_bars):
    """
    Test StoreSink with multiple worker tasks.
    
    This verifies that the sink can process batches concurrently
    with multiple workers.
    """
    sink = StoreSink(
        batch_processor=mock_batch_processor,
        workers=3,  # Multiple workers
        queue_max=20
    )
    
    await sink.start()
    
    # Write multiple batches
    for _ in range(10):
        await sink.write(sample_bars)
    
    await sink.flush()
    await sink.close()
    
    # All batches should be processed
    assert len(mock_batch_processor.upsert_calls) == 10


@pytest.mark.asyncio
@pytest.mark.integration
async def test_store_sink_optional_fields(mock_batch_processor):
    """
    Test StoreSink handles optional Bar fields.
    
    This verifies that the sink properly handles optional fields
    like vwap, trade_count, and metadata.
    """
    now = datetime.now(timezone.utc)
    bars = [Bar(
        symbol="FULL",
        timestamp=now,
        open=Decimal("100.00"),
        high=Decimal("100.00"),
        low=Decimal("100.00"),
        close=Decimal("100.00"),
        volume=Decimal("100"),
        source="test",
        vwap=Decimal("100.25"),
        trade_count=42,
        metadata={"custom": "data"}
    )]
    
    sink = StoreSink(
        batch_processor=mock_batch_processor,
        workers=1,
        queue_max=10
    )
    
    await sink.start()
    await sink.write(bars)
    await sink.flush()
    await sink.close()
    
    # Verify optional fields in record
    record = mock_batch_processor.upsert_calls[0][0]
    assert record["vwap"] == 100.25
    assert record["trade_count"] == 42
    assert record["metadata"] == {"custom": "data"}


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

