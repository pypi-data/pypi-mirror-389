"""
Unit tests for Redis connection and basic functionality.

Tests Redis connectivity without requiring the full streaming pipeline.
"""

import pytest
import redis
from unittest.mock import patch, MagicMock


class TestRedisConnection:
    """Test Redis connection and basic operations."""
    
    def test_redis_connection_mock(self):
        """Test Redis connection with mock."""
        with patch('redis.Redis') as mock_redis:
            # Mock Redis connection
            mock_instance = MagicMock()
            mock_instance.ping.return_value = True
            mock_redis.return_value = mock_instance
            
            # Test connection
            r = redis.Redis(host='localhost', port=6379)
            assert r.ping() is True
            mock_redis.assert_called_once_with(host='localhost', port=6379)
    
    def test_redis_stream_operations_mock(self):
        """Test Redis stream operations with mock."""
        with patch('redis.Redis') as mock_redis:
            # Mock Redis instance
            mock_instance = MagicMock()
            mock_instance.xadd.return_value = "1234567890-0"
            mock_instance.xreadgroup.return_value = []
            mock_instance.xack.return_value = 1
            mock_redis.return_value = mock_instance
            
            # Test stream operations
            r = redis.Redis(host='localhost', port=6379)
            
            # Test xadd
            msg_id = r.xadd("test_stream", {"data": "test"})
            assert msg_id == "1234567890-0"
            
            # Test xreadgroup
            messages = r.xreadgroup("group", "consumer", {"test_stream": ">"})
            assert messages == []
            
            # Test xack
            ack_result = r.xack("test_stream", "group", "1234567890-0")
            assert ack_result == 1
    
    def test_redis_error_handling(self):
        """Test Redis error handling."""
        with patch('redis.Redis') as mock_redis:
            # Mock Redis connection error
            mock_instance = MagicMock()
            mock_instance.ping.side_effect = redis.ConnectionError("Connection failed")
            mock_redis.return_value = mock_instance
            
            # Test error handling
            r = redis.Redis(host='localhost', port=6379)
            
            with pytest.raises(redis.ConnectionError):
                r.ping()
    
    def test_redis_stream_bus_import(self):
        """Test that RedisStreamBus can be imported."""
        try:
            from market_data_pipeline.streaming.redis_bus import RedisStreamBus
            assert RedisStreamBus is not None
        except ImportError as e:
            pytest.fail(f"Failed to import RedisStreamBus: {e}")
    
    def test_stream_event_creation(self):
        """Test StreamEvent creation."""
        try:
            from market_data_pipeline.streaming.bus import StreamEvent
            from datetime import datetime, timezone
            
            event = StreamEvent(
                provider="test",
                symbol="TEST",
                kind="tick",
                src_ts=datetime.now(timezone.utc),
                ingest_ts=datetime.now(timezone.utc),
                data={"o": 100.0, "h": 100.0, "l": 100.0, "c": 100.0, "v": 1000}
            )
            
            assert event.provider == "test"
            assert event.symbol == "TEST"
            assert event.kind == "tick"
            assert event.data["o"] == 100.0
            assert event.data["v"] == 1000
            
        except ImportError as e:
            pytest.fail(f"Failed to import StreamEvent: {e}")
    
    def test_telemetry_import(self):
        """Test telemetry module import."""
        try:
            from market_data_pipeline.streaming.telemetry import start_metrics_server
            assert start_metrics_server is not None
        except ImportError as e:
            pytest.fail(f"Failed to import telemetry: {e}")
    
    def test_micro_batcher_import(self):
        """Test micro-batcher import."""
        try:
            from market_data_pipeline.streaming.consumers.micro_batcher import MicroBatcher
            assert MicroBatcher is not None
        except ImportError as e:
            pytest.fail(f"Failed to import MicroBatcher: {e}")
