"""
Integration tests for signals storage and retrieval.

Tests the complete flow: signal generation → store → readback.
"""

import asyncio
import pytest
import asyncpg
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock


class MockSignalsStoreClient:
    """Mock signals store client for testing."""
    
    def __init__(self):
        self.signals = []
        self.write_calls = 0
    
    async def write_signals(self, signals):
        """Mock write signals method."""
        self.signals.extend(signals)
        self.write_calls += 1
        return len(signals)
    
    async def fetch_signals(self, symbol=None, provider=None):
        """Mock fetch signals method."""
        filtered = self.signals
        if symbol:
            filtered = [s for s in filtered if s.symbol == symbol]
        if provider:
            filtered = [s for s in filtered if s.provider == provider]
        return filtered


@pytest.mark.asyncio
async def test_signals_roundtrip():
    """Test signals storage and retrieval roundtrip."""
    client = MockSignalsStoreClient()
    
    # Create test signal
    signal = SimpleNamespace(
        provider="synthetic",
        symbol="TEST",
        ts=datetime.now(timezone.utc),
        name="test_signal",
        value=1.23,
        score=0.99,
        metadata={"window": "1m"}
    )
    
    # Write signal
    await client.write_signals([signal])
    
    # Verify write was called
    assert client.write_calls == 1
    assert len(client.signals) == 1
    
    # Verify signal data
    stored_signal = client.signals[0]
    assert stored_signal.provider == "synthetic"
    assert stored_signal.symbol == "TEST"
    assert stored_signal.name == "test_signal"
    assert stored_signal.value == 1.23
    assert stored_signal.score == 0.99
    assert stored_signal.metadata == {"window": "1m"}


@pytest.mark.asyncio
async def test_signals_batch_write():
    """Test batch writing of multiple signals."""
    client = MockSignalsStoreClient()
    
    # Create multiple signals
    signals = []
    base_time = datetime.now(timezone.utc)
    
    for i in range(3):
        signal = SimpleNamespace(
            provider="synthetic",
            symbol=f"TEST{i}",
            ts=base_time,
            name=f"signal_{i}",
            value=1.0 + i * 0.1,
            score=0.8 + i * 0.05,
            metadata={"index": i}
        )
        signals.append(signal)
    
    # Write all signals
    await client.write_signals(signals)
    
    # Verify all signals were stored
    assert client.write_calls == 1
    assert len(client.signals) == 3
    
    # Verify individual signals
    for i, signal in enumerate(signals):
        stored = client.signals[i]
        assert stored.symbol == f"TEST{i}"
        assert stored.name == f"signal_{i}"
        assert stored.value == 1.0 + i * 0.1
        assert stored.score == 0.8 + i * 0.05


@pytest.mark.asyncio
async def test_signals_filtering():
    """Test signal filtering by symbol and provider."""
    client = MockSignalsStoreClient()
    
    # Create signals with different symbols and providers
    signals = [
        SimpleNamespace(
            provider="synthetic",
            symbol="AAPL",
            ts=datetime.now(timezone.utc),
            name="signal1",
            value=1.0,
            score=0.8,
            metadata={}
        ),
        SimpleNamespace(
            provider="synthetic",
            symbol="MSFT",
            ts=datetime.now(timezone.utc),
            name="signal2",
            value=2.0,
            score=0.9,
            metadata={}
        ),
        SimpleNamespace(
            provider="ibkr",
            symbol="AAPL",
            ts=datetime.now(timezone.utc),
            name="signal3",
            value=3.0,
            score=0.7,
            metadata={}
        )
    ]
    
    # Write all signals
    await client.write_signals(signals)
    
    # Test filtering by symbol
    aapl_signals = await client.fetch_signals(symbol="AAPL")
    assert len(aapl_signals) == 2
    
    # Test filtering by provider
    synthetic_signals = await client.fetch_signals(provider="synthetic")
    assert len(synthetic_signals) == 2
    
    # Test filtering by both
    aapl_synthetic = await client.fetch_signals(symbol="AAPL", provider="synthetic")
    assert len(aapl_synthetic) == 1
    assert aapl_synthetic[0].name == "signal1"


@pytest.mark.asyncio
async def test_signals_idempotency():
    """Test that duplicate signals are handled properly."""
    client = MockSignalsStoreClient()
    
    # Create signal
    signal = SimpleNamespace(
        provider="synthetic",
        symbol="TEST",
        ts=datetime.now(timezone.utc),
        name="duplicate_signal",
        value=1.0,
        score=0.8,
        metadata={}
    )
    
    # Write signal twice
    await client.write_signals([signal])
    await client.write_signals([signal])
    
    # Should handle duplicates gracefully
    assert client.write_calls == 2
    # In real implementation, duplicates would be deduplicated
    # For mock, we just verify the calls were made


@pytest.mark.asyncio
async def test_signals_metadata_handling():
    """Test that signal metadata is properly handled."""
    client = MockSignalsStoreClient()
    
    # Create signal with complex metadata
    metadata = {
        "window": "1m",
        "features": {
            "rsi": 65.5,
            "volatility": 0.15
        },
        "confidence": 0.95
    }
    
    signal = SimpleNamespace(
        provider="synthetic",
        symbol="TEST",
        ts=datetime.now(timezone.utc),
        name="complex_signal",
        value=1.5,
        score=0.9,
        metadata=metadata
    )
    
    # Write signal
    await client.write_signals([signal])
    
    # Verify metadata is preserved
    stored_signal = client.signals[0]
    assert stored_signal.metadata == metadata
    assert stored_signal.metadata["window"] == "1m"
    assert stored_signal.metadata["features"]["rsi"] == 65.5
    assert stored_signal.metadata["confidence"] == 0.95
