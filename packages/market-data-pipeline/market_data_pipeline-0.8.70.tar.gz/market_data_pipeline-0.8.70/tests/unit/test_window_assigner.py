"""
Unit tests for window assignment logic in micro-batcher.
"""

import pytest
from datetime import datetime, timezone, timedelta
from market_data_pipeline.streaming.consumers.micro_batcher import MicroBatcher


class TestWindowAssigner:
    """Test window assignment and bucket key logic."""
    
    def test_bucket_key_alignment(self):
        """Test that bucket keys align properly for window boundaries."""
        mb = MicroBatcher(bus=None, store_client=None, window_seconds=2)
        
        # Test 2-second window alignment
        t1 = datetime(2025, 10, 24, 12, 0, 1, tzinfo=timezone.utc)
        t2 = datetime(2025, 10, 24, 12, 0, 3, tzinfo=timezone.utc)
        t3 = datetime(2025, 10, 24, 12, 0, 5, tzinfo=timezone.utc)
        
        # Test window assignment logic
        key1 = mb._get_window_key_from_timestamp(t1)
        key2 = mb._get_window_key_from_timestamp(t2)
        key3 = mb._get_window_key_from_timestamp(t3)
        
        # With 2-second windows:
        # Second 1: (1 // 2) * 2 = 0 * 2 = 0
        # Second 3: (3 // 2) * 2 = 1 * 2 = 2
        # Second 5: (5 // 2) * 2 = 2 * 2 = 4
        expected_key1 = datetime(2025, 10, 24, 12, 0, 0, tzinfo=timezone.utc)
        expected_key2 = datetime(2025, 10, 24, 12, 0, 2, tzinfo=timezone.utc)
        expected_key3 = datetime(2025, 10, 24, 12, 0, 4, tzinfo=timezone.utc)
        
        assert key1 == expected_key1
        assert key2 == expected_key2
        assert key3 == expected_key3
    
    def test_different_window_sizes(self):
        """Test bucket keys for different window sizes."""
        # Test 1-second windows
        mb1 = MicroBatcher(bus=None, store_client=None, window_seconds=1)
        t = datetime(2025, 10, 24, 12, 0, 1, 500000, tzinfo=timezone.utc)
        key1 = mb1._get_window_key_from_timestamp(t)
        assert key1.microsecond == 0
        
        # Test 5-second windows
        mb5 = MicroBatcher(bus=None, store_client=None, window_seconds=5)
        key5 = mb5._get_window_key_from_timestamp(t)
        assert key5.second % 5 == 0
    
    def test_window_expiration(self):
        """Test window expiration logic."""
        mb = MicroBatcher(bus=None, store_client=None, window_seconds=2, allow_late_ms=500)
        
        now = datetime.utcnow()
        
        # Test with a recent window (should not be expired)
        recent_window = now - timedelta(seconds=1)  # 1 second ago
        assert not mb._is_window_expired(recent_window)
        
        # Test with an old window (should be expired)
        old_window = now - timedelta(seconds=10)  # 10 seconds ago
        assert mb._is_window_expired(old_window)
    
    def test_aggregate_window_empty(self):
        """Test aggregation with empty window."""
        mb = MicroBatcher(bus=None, store_client=None)
        result = mb._aggregate_window([])
        assert result is None
    
    def test_aggregate_window_single_event(self):
        """Test aggregation with single event."""
        mb = MicroBatcher(bus=None, store_client=None)
        
        from market_data_pipeline.streaming.bus import StreamEvent
        event = StreamEvent(
            provider="test",
            symbol="TEST",
            kind="tick",
            src_ts=datetime.utcnow(),
            ingest_ts=datetime.utcnow(),
            data={"o": 100.0, "h": 100.0, "l": 100.0, "c": 100.0, "v": 1000}
        )
        
        result = mb._aggregate_window([event])
        assert result is not None
        assert result["symbol"] == "TEST"
        assert result["open"] == 100.0
        assert result["close"] == 100.0
        assert result["volume"] == 1000
    
    def test_aggregate_window_multiple_events(self):
        """Test aggregation with multiple events."""
        mb = MicroBatcher(bus=None, store_client=None)
        
        from market_data_pipeline.streaming.bus import StreamEvent
        events = [
            StreamEvent(
                provider="test",
                symbol="TEST",
                kind="bar",
                src_ts=datetime.utcnow(),
                ingest_ts=datetime.utcnow(),
                data={"o": 100.0, "h": 100.0, "l": 100.0, "c": 100.0, "v": 1000}
            ),
            StreamEvent(
                provider="test",
                symbol="TEST",
                kind="bar",
                src_ts=datetime.utcnow(),
                ingest_ts=datetime.utcnow(),
                data={"o": 100.0, "h": 102.0, "l": 99.0, "c": 101.0, "v": 500}
            )
        ]
        
        result = mb._aggregate_window(events)
        assert result is not None
        assert result["symbol"] == "TEST"
        assert result["open"] == 100.0  # First event open
        assert result["close"] == 101.0  # Last event close
        assert result["high"] == 102.0   # Max high (from second event)
        assert result["low"] == 99.0    # Min low
        assert result["volume"] == 1500  # Sum of volumes
