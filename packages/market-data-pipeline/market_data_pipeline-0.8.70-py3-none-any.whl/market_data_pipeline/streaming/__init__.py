"""
Streaming module for market_data_pipeline.

Provides stream processing capabilities including:
- Event bus abstraction (Redis/Kafka)
- Micro-batch processing
- Feature computation
- Inference engine
"""

from .bus import StreamBus, Message
from .redis_bus import RedisStreamBus

__all__ = ["StreamBus", "Message", "RedisStreamBus"]
