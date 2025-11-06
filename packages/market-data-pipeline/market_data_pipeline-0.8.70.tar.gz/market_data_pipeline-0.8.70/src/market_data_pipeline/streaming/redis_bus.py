"""
Redis Streams implementation of StreamBus.

Provides Redis Streams backend for stream processing.
"""

import asyncio
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import redis.asyncio as redis
from .bus import StreamBus, Message, StreamEvent, SignalEvent

logger = logging.getLogger(__name__)


class RedisStreamBus(StreamBus):
    """Redis Streams implementation of StreamBus."""
    
    def __init__(self, uri: str, events_stream: str = "mdp.events", signals_stream: str = "mdp.signals"):
        self.uri = uri
        self.events_stream = events_stream
        self.signals_stream = signals_stream
        self._redis: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self._redis = redis.from_url(self.uri, decode_responses=True)
            # Test connection
            await self._redis.ping()
            self._connected = True
            logger.info(f"Connected to Redis at {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._connected = False
            logger.info("Disconnected from Redis")
    
    async def publish(self, topic: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> str:
        """Publish a message to a Redis stream."""
        if not self._connected:
            raise RuntimeError("Not connected to Redis")
        
        try:
            # Serialize payload
            data = json.dumps(payload)
            stream_data = {"data": data}
            
            # Add headers if provided
            if headers:
                stream_data.update({f"header_{k}": v for k, v in headers.items()})
            
            # Publish to stream
            message_id = await self._redis.xadd(topic, stream_data)
            logger.debug(f"Published message {message_id} to stream {topic}")
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to publish to stream {topic}: {e}")
            raise
    
    async def read(
        self, 
        topic: str, 
        group: str, 
        consumer: str, 
        count: int = 100, 
        block_ms: int = 1000
    ) -> List[Message]:
        """Read messages from a Redis stream using consumer groups."""
        if not self._connected:
            raise RuntimeError("Not connected to Redis")
        
        try:
            # Read from stream using consumer group
            messages = await self._redis.xreadgroup(
                group, 
                consumer, 
                {topic: ">"}, 
                count=count, 
                block=block_ms
            )
            
            result = []
            for stream_name, entries in messages or []:
                for msg_id, fields in entries:
                    try:
                        # Parse message data
                        data = json.loads(fields["data"])
                        
                        # Extract headers
                        headers = {}
                        for key, value in fields.items():
                            if key.startswith("header_"):
                                headers[key[7:]] = value
                        
                        # Create message
                        message = Message(
                            id=msg_id,
                            topic=stream_name,
                            payload=data,
                            timestamp=datetime.utcnow(),
                            headers=headers if headers else None
                        )
                        result.append(message)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode message {msg_id}: {e}")
                        continue
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to read from stream {topic}: {e}")
            raise
    
    async def ack(self, topic: str, group: str, message_id: str) -> None:
        """Acknowledge a message."""
        if not self._connected:
            raise RuntimeError("Not connected to Redis")
        
        try:
            await self._redis.xack(topic, group, message_id)
            logger.debug(f"Acknowledged message {message_id} in group {group}")
        except Exception as e:
            logger.error(f"Failed to acknowledge message {message_id}: {e}")
            raise
    
    async def create_consumer_group(self, topic: str, group: str) -> None:
        """Create a consumer group for a topic."""
        if not self._connected:
            raise RuntimeError("Not connected to Redis")
        
        try:
            # Try to create consumer group, ignore if it already exists
            await self._redis.xgroup_create(topic, group, id="0", mkstream=True)
            logger.info(f"Created consumer group {group} for topic {topic}")
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group {group} already exists for topic {topic}")
            else:
                logger.error(f"Failed to create consumer group {group}: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to create consumer group {group}: {e}")
            raise
    
    async def publish_event(self, event: StreamEvent) -> str:
        """Publish a stream event."""
        return await self.publish(self.events_stream, event.to_dict())
    
    async def publish_signal(self, signal: SignalEvent) -> str:
        """Publish a signal event."""
        return await self.publish(self.signals_stream, signal.to_dict())
    
    async def read_events(
        self, 
        group: str, 
        consumer: str, 
        count: int = 100, 
        block_ms: int = 1000
    ) -> List[StreamEvent]:
        """Read stream events."""
        messages = await self.read(self.events_stream, group, consumer, count, block_ms)
        events = []
        
        for msg in messages:
            try:
                event = StreamEvent.from_dict(msg.payload)
                events.append(event)
            except Exception as e:
                logger.error(f"Failed to parse event from message {msg.id}: {e}")
                continue
        
        return events
    
    async def read_signals(
        self, 
        group: str, 
        consumer: str, 
        count: int = 100, 
        block_ms: int = 1000
    ) -> List[SignalEvent]:
        """Read signal events."""
        messages = await self.read(self.signals_stream, group, consumer, count, block_ms)
        signals = []
        
        for msg in messages:
            try:
                signal = SignalEvent.from_dict(msg.payload)
                signals.append(signal)
            except Exception as e:
                logger.error(f"Failed to parse signal from message {msg.id}: {e}")
                continue
        
        return signals
