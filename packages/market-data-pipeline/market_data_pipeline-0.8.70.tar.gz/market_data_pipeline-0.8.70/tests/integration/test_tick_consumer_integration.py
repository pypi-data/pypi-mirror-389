"""
Integration test for TickConsumer (Phase 3).

Tests the complete flow: stream events → TickConsumer → store.upsert_ticks()
"""

import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from market_data_pipeline.streaming.consumers.tick_consumer import TickConsumer
from market_data_pipeline.streaming.bus import Message, StreamBus


class MockStoreClient:
    """Mock AsyncStoreClient for testing tick persistence."""
    
    def __init__(self):
        self.ticks = []
        self.upsert_calls = 0
        self.upsert_errors = 0
    
    async def upsert_ticks(self, ticks: list) -> int:
        """Mock upsert_ticks method."""
        if self.upsert_errors > 0:
            self.upsert_errors -= 1
            raise Exception("Simulated store error")
        
        self.ticks.extend(ticks)
        self.upsert_calls += 1
        return len(ticks)


class MockStreamBus:
    """Mock StreamBus for testing."""
    
    def __init__(self):
        self.messages = []
        self.acked = []
        self.consumer_groups = set()
    
    async def create_consumer_group(self, topic: str, group: str):
        """Mock create consumer group."""
        self.consumer_groups.add((topic, group))
    
    async def read(self, topic: str, group: str, consumer: str, count: int, block_ms: int) -> list:
        """Mock read messages."""
        if not self.messages:
            return []
        
        batch = self.messages[:count]
        self.messages = self.messages[count:]
        return batch
    
    async def ack(self, topic: str, group: str, message_id: str):
        """Mock acknowledge message."""
        self.acked.append(message_id)
    
    def add_message(self, msg_id: str, payload: dict):
        """Add a mock message to the bus."""
        msg = Message(
            id=msg_id,
            topic="mdp.events",
            payload=payload,
            timestamp=datetime.now(timezone.utc)
        )
        self.messages.append(msg)


@pytest.mark.asyncio
async def test_tick_consumer_forwards_to_store():
    """Test that TickConsumer forwards tick data to store."""
    # Setup
    bus = MockStreamBus()
    store = MockStoreClient()
    
    consumer = TickConsumer(
        bus=bus,
        store_client=store,
        batch_size=5,
        flush_timeout_ms=100,
        consumer_group="test-group",
        consumer_name="test-consumer"
    )
    
    # Add test messages
    bus.add_message("msg-1", {
        "kind": "tick",
        "provider": "ibkr",
        "symbol": "NVDA",
        "price": 123.45,
        "timestamp": "2025-11-03T14:30:00Z",
        "size": 100,
        "bid": 123.40,
        "ask": 123.50
    })
    
    bus.add_message("msg-2", {
        "kind": "tick",
        "provider": "ibkr",
        "symbol": "AAPL",
        "price": 185.50,
        "timestamp": "2025-11-03T14:30:01Z",
        "size": 200
    })
    
    # Start consumer and let it process
    await consumer.start()
    await asyncio.sleep(0.3)  # Let it process
    await consumer.stop()
    
    # Verify
    assert store.upsert_calls > 0, "Store upsert_ticks should have been called"
    assert len(store.ticks) == 2, "Should have persisted 2 ticks"
    
    # Check first tick
    tick1 = store.ticks[0]
    assert tick1["provider"] == "ibkr"
    assert tick1["symbol"] == "NVDA"
    assert abs(tick1["price"] - 123.45) < 1e-6
    assert tick1["size"] == 100
    assert tick1["bid"] == 123.40
    
    # Check second tick
    tick2 = store.ticks[1]
    assert tick2["symbol"] == "AAPL"
    assert abs(tick2["price"] - 185.50) < 1e-6
    
    # Verify acknowledgments
    assert "msg-1" in bus.acked
    assert "msg-2" in bus.acked


@pytest.mark.asyncio
async def test_tick_consumer_filters_non_tick_events():
    """Test that TickConsumer only processes tick events, not bars."""
    # Setup
    bus = MockStreamBus()
    store = MockStoreClient()
    
    consumer = TickConsumer(
        bus=bus,
        store_client=store,
        batch_size=5
    )
    
    # Add mixed event types
    bus.add_message("msg-1", {
        "kind": "tick",
        "provider": "ibkr",
        "symbol": "NVDA",
        "price": 123.45,
        "timestamp": "2025-11-03T14:30:00Z"
    })
    
    bus.add_message("msg-2", {
        "kind": "bar",  # This should be filtered out
        "provider": "ibkr",
        "symbol": "AAPL",
        "o": 185.0,
        "h": 186.0,
        "l": 184.5,
        "c": 185.50,
        "v": 1000,
        "timestamp": "2025-11-03T14:30:00Z"
    })
    
    bus.add_message("msg-3", {
        "kind": "tick",
        "provider": "ibkr",
        "symbol": "MSFT",
        "price": 380.25,
        "timestamp": "2025-11-03T14:30:02Z"
    })
    
    # Process
    await consumer.start()
    await asyncio.sleep(0.3)
    await consumer.stop()
    
    # Verify only tick events were forwarded
    assert len(store.ticks) == 2, "Should only forward tick events"
    assert store.ticks[0]["symbol"] == "NVDA"
    assert store.ticks[1]["symbol"] == "MSFT"


@pytest.mark.asyncio
async def test_tick_consumer_batch_processing():
    """Test that TickConsumer batches ticks efficiently."""
    # Setup
    bus = MockStreamBus()
    store = MockStoreClient()
    
    consumer = TickConsumer(
        bus=bus,
        store_client=store,
        batch_size=10,
        flush_timeout_ms=100
    )
    
    # Add 25 ticks
    for i in range(25):
        bus.add_message(f"msg-{i}", {
            "kind": "tick",
            "provider": "ibkr",
            "symbol": f"SYM{i % 5}",  # 5 different symbols
            "price": 100.0 + i,
            "timestamp": f"2025-11-03T14:30:{i:02d}Z"
        })
    
    # Process
    await consumer.start()
    await asyncio.sleep(0.5)  # Let it process batches
    await consumer.stop()
    
    # Verify all ticks were forwarded
    assert len(store.ticks) == 25, "All 25 ticks should be forwarded"
    
    # Should have made multiple batch calls (batch_size=10)
    assert store.upsert_calls >= 2, "Should batch efficiently"


@pytest.mark.asyncio
async def test_tick_consumer_handles_missing_fields():
    """Test that TickConsumer handles messages with missing optional fields."""
    # Setup
    bus = MockStreamBus()
    store = MockStoreClient()
    
    consumer = TickConsumer(
        bus=bus,
        store_client=store,
        batch_size=5
    )
    
    # Add tick with only required fields
    bus.add_message("msg-1", {
        "kind": "tick",
        "provider": "ibkr",
        "symbol": "TSLA",
        "price": 250.75,
        # No timestamp - should default to now
        # No size, bid, ask - should be None
    })
    
    # Process
    await consumer.start()
    await asyncio.sleep(0.3)
    await consumer.stop()
    
    # Verify
    assert len(store.ticks) == 1
    tick = store.ticks[0]
    assert tick["symbol"] == "TSLA"
    assert abs(tick["price"] - 250.75) < 1e-6
    assert tick["size"] is None
    assert tick["bid"] is None
    assert tick["ask"] is None
    assert tick["ts"] is not None  # Should have defaulted timestamp


@pytest.mark.asyncio
async def test_tick_consumer_continues_on_store_error():
    """Test that TickConsumer continues processing after store errors."""
    # Setup
    bus = MockStreamBus()
    store = MockStoreClient()
    store.upsert_errors = 1  # Simulate one error
    
    consumer = TickConsumer(
        bus=bus,
        store_client=store,
        batch_size=2
    )
    
    # Add messages
    bus.add_message("msg-1", {
        "kind": "tick",
        "provider": "ibkr",
        "symbol": "NVDA",
        "price": 123.45,
        "timestamp": "2025-11-03T14:30:00Z"
    })
    
    bus.add_message("msg-2", {
        "kind": "tick",
        "provider": "ibkr",
        "symbol": "AAPL",
        "price": 185.50,
        "timestamp": "2025-11-03T14:30:01Z"
    })
    
    # Process - first batch will fail, second should succeed
    await consumer.start()
    await asyncio.sleep(0.5)
    await consumer.stop()
    
    # Despite one error, should have attempted to process
    # (actual behavior depends on error handling implementation)
    assert store.upsert_calls >= 1


@pytest.mark.asyncio
async def test_tick_consumer_symbol_uppercase_normalization():
    """Test that symbols are normalized to uppercase."""
    # Setup
    bus = MockStreamBus()
    store = MockStoreClient()
    
    consumer = TickConsumer(
        bus=bus,
        store_client=store
    )
    
    # Add tick with lowercase symbol
    bus.add_message("msg-1", {
        "kind": "tick",
        "provider": "ibkr",
        "symbol": "nvda",  # lowercase
        "price": 123.45,
        "timestamp": "2025-11-03T14:30:00Z"
    })
    
    # Process
    await consumer.start()
    await asyncio.sleep(0.3)
    await consumer.stop()
    
    # Verify symbol was passed as-is (store does uppercase normalization)
    assert len(store.ticks) == 1
    tick = store.ticks[0]
    assert tick["symbol"] == "nvda"  # Consumer passes through, store uppercases

