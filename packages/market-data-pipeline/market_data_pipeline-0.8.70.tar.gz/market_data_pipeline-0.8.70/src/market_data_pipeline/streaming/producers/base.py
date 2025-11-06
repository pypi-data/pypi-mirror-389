"""
Base producer for stream events.

Defines the interface for converting provider data into stream events.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import logging
from datetime import datetime

from ..bus import StreamBus, StreamEvent

logger = logging.getLogger(__name__)


class EventProducer(ABC):
    """Abstract base class for event producers."""
    
    def __init__(self, bus: StreamBus, provider: str, batch_size: int = 100, linger_ms: int = 50):
        self.bus = bus
        self.provider = provider
        self.batch_size = batch_size
        self.linger_ms = linger_ms
        self._running = False
        self._batch = []
        self._last_flush = datetime.utcnow()
    
    @abstractmethod
    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """
        Fetch data from the provider.
        
        Returns:
            Data dictionary or None if no data available
        """
        pass
    
    def create_event(self, symbol: str, data: Dict[str, Any], kind: str = "tick") -> StreamEvent:
        """
        Create a stream event from provider data.
        
        Args:
            symbol: Symbol name
            data: Provider data
            kind: Event kind (tick or bar)
            
        Returns:
            Stream event
        """
        now = datetime.utcnow()
        
        # Extract common fields
        src_ts = data.get("timestamp", now)
        if isinstance(src_ts, str):
            src_ts = datetime.fromisoformat(src_ts.replace("Z", "+00:00"))
        
        # Create event data
        event_data = {
            "o": data.get("open", data.get("price", 0.0)),
            "h": data.get("high", data.get("price", 0.0)),
            "l": data.get("low", data.get("price", 0.0)),
            "c": data.get("close", data.get("price", 0.0)),
            "v": data.get("volume", data.get("size", 0))
        }
        
        # Add interval for bars
        interval = data.get("interval")
        
        # Add sequence number if available
        seq = data.get("seq")
        
        return StreamEvent(
            provider=self.provider,
            symbol=symbol,
            kind=kind,
            src_ts=src_ts,
            ingest_ts=now,
            data=event_data,
            interval=interval,
            seq=seq
        )
    
    async def add_to_batch(self, event: StreamEvent) -> None:
        """Add event to batch and flush if needed."""
        self._batch.append(event)
        
        # Flush if batch is full or linger time exceeded
        now = datetime.utcnow()
        if (len(self._batch) >= self.batch_size or 
            (now - self._last_flush).total_seconds() * 1000 >= self.linger_ms):
            await self.flush_batch()
    
    async def flush_batch(self) -> None:
        """Flush the current batch to the stream."""
        if not self._batch:
            return
        
        try:
            # Publish all events in batch
            for event in self._batch:
                await self.bus.publish_event(event)
            
            logger.debug(f"Flushed batch of {len(self._batch)} events")
            self._batch.clear()
            self._last_flush = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Failed to flush batch: {e}")
            raise
    
    async def start(self) -> None:
        """Start the producer."""
        self._running = True
        logger.info(f"Started {self.__class__.__name__} for provider {self.provider}")
        
        try:
            while self._running:
                try:
                    # Fetch data from provider
                    data = await self.fetch_data()
                    
                    if data:
                        # Create and add event to batch
                        symbol = data.get("symbol", "UNKNOWN")
                        kind = "bar" if "interval" in data else "tick"
                        event = self.create_event(symbol, data, kind)
                        await self.add_to_batch(event)
                    else:
                        # No data available, sleep briefly
                        await asyncio.sleep(0.01)
                        
                except Exception as e:
                    logger.error(f"Error in producer loop: {e}")
                    await asyncio.sleep(1)  # Brief pause before retry
                    
        except asyncio.CancelledError:
            logger.info(f"Producer {self.__class__.__name__} cancelled")
        finally:
            # Flush any remaining events
            await self.flush_batch()
            self._running = False
            logger.info(f"Stopped {self.__class__.__name__}")
    
    async def stop(self) -> None:
        """Stop the producer."""
        self._running = False
