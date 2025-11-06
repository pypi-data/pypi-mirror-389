"""
Micro-batcher for windowing and aggregation.

Processes stream events in tumbling windows and aggregates them into bars.
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import statistics

from ..bus import StreamEvent, StreamBus
from ..telemetry import (
    record_microbatch_flush,
    record_microbatch_rows,
    record_microbatch_window_latency,
    record_store_write_duration
)
import time

logger = logging.getLogger(__name__)


class MicroBatcher:
    """Micro-batcher for processing stream events in windows."""
    
    def __init__(
        self,
        bus: StreamBus,
        store_client,
        window_seconds: int = 2,
        max_batch_size: int = 5000,
        allow_late_ms: int = 500,
        flush_timeout_ms: int = 1000,
        consumer_group: str = "micro-batcher",
        consumer_name: str = "batcher-1"
    ):
        self.bus = bus
        self.store_client = store_client
        self.window_seconds = window_seconds
        self.max_batch_size = max_batch_size
        self.allow_late_ms = allow_late_ms
        self.flush_timeout_ms = flush_timeout_ms
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        
        # Window state
        self.windows: Dict[Tuple[str, datetime], List[StreamEvent]] = defaultdict(list)
        self._running = False
        self._last_flush = datetime.utcnow()
    
    def _get_window_key(self, event: StreamEvent) -> Tuple[str, datetime]:
        """Get window key for an event."""
        # Parse timestamp - handle both string and datetime objects
        if isinstance(event.src_ts, str):
            # Remove any duplicate timezone info
            ts_str = event.src_ts.replace("Z", "").replace("+00:00", "")
            if "+00:00" in ts_str:
                ts_str = ts_str.replace("+00:00", "")
            ts = datetime.fromisoformat(ts_str)
        else:
            ts = event.src_ts
        
        # Round down to window boundary
        window_start = ts.replace(
            microsecond=0,
            second=(ts.second // self.window_seconds) * self.window_seconds
        )
        
        return (event.symbol, window_start)
    
    def _get_window_key_from_timestamp(self, ts: datetime) -> datetime:
        """Get window key from timestamp."""
        return ts.replace(
            microsecond=0,
            second=(ts.second // self.window_seconds) * self.window_seconds
        )
    
    def _is_window_expired(self, window_start: datetime) -> bool:
        """Check if a window has expired and should be flushed."""
        now = datetime.utcnow()
        window_end = window_start + timedelta(seconds=self.window_seconds)
        grace_period = timedelta(milliseconds=self.allow_late_ms)
        
        return now > window_end + grace_period
    
    def _aggregate_window(self, events: List[StreamEvent]) -> Dict[str, Any]:
        """Aggregate events in a window into OHLCV bar."""
        if not events:
            return None
        
        # Sort by timestamp to ensure proper ordering
        events.sort(key=lambda e: e.src_ts)
        
        symbol = events[0].symbol
        provider = events[0].provider
        window_start = self._get_window_key(events[0])[1]
        
        # Extract OHLCV data
        opens = []
        highs = []
        lows = []
        closes = []
        volumes = []
        
        for event in events:
            if event.kind == "tick":
                # For ticks, use close price for OHLC
                price = event.data.get("c", event.data.get("price", 0))
                volume = event.data.get("v", event.data.get("size", 0))
                opens.append(price)
                highs.append(price)
                lows.append(price)
                closes.append(price)
            else:
                # For bars, use actual OHLC
                open_price = event.data.get("o", 0)
                high_price = event.data.get("h", 0)
                low_price = event.data.get("l", 0)
                close_price = event.data.get("c", 0)
                volume = event.data.get("v", 0)
                
                opens.append(open_price)
                highs.append(high_price)
                lows.append(low_price)
                closes.append(close_price)
            
            volumes.append(volume)
        
        if not opens:
            return None
        
        # Calculate OHLCV
        open_price = opens[0]
        close_price = closes[-1]
        high_price = max(highs)
        low_price = min(lows)
        total_volume = sum(volumes)
        
        # Calculate VWAP
        if total_volume > 0:
            vwap = sum(c * v for c, v in zip(closes, volumes)) / total_volume
        else:
            vwap = close_price
        
        return {
            "provider": provider,
            "symbol": symbol,
            "interval": f"{self.window_seconds}s",
            "ts": window_start,
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": total_volume,
            "vwap": round(vwap, 2),
            "tick_count": len(events)
        }
    
    async def _flush_window(self, window_key: Tuple[str, datetime], events: List[StreamEvent]) -> None:
        """Flush a window to storage."""
        if not events:
            return
        
        try:
            # Aggregate events into bar
            bar_data = self._aggregate_window(events)
            if not bar_data:
                return
            
            # Write to store with timing
            start = time.monotonic()
            await self.store_client.write_bars([bar_data])
            duration = (time.monotonic() - start) * 1000  # Convert to milliseconds
            
            # Record metrics
            record_microbatch_flush(window_key[0], self.window_seconds * 1000)
            record_microbatch_rows(self.window_seconds * 1000, len(events))
            record_microbatch_window_latency(self.window_seconds * 1000, duration)
            record_store_write_duration("bars_ohlcv", duration / 1000)  # Convert back to seconds
            
            logger.debug(f"Flushed window {window_key} with {len(events)} events")
            
        except Exception as e:
            logger.error(f"Failed to flush window {window_key}: {e}")
            raise
    
    async def _flush_expired_windows(self) -> None:
        """Flush all expired windows."""
        expired_keys = []
        
        for window_key, events in self.windows.items():
            if self._is_window_expired(window_key[1]):
                expired_keys.append(window_key)
        
        for window_key in expired_keys:
            events = self.windows.pop(window_key)
            await self._flush_window(window_key, events)
    
    async def _process_event(self, event: StreamEvent) -> None:
        """Process a single event."""
        window_key = self._get_window_key(event)
        
        # Add event to window
        self.windows[window_key].append(event)
        
        # Check if window is full
        if len(self.windows[window_key]) >= self.max_batch_size:
            events = self.windows.pop(window_key)
            await self._flush_window(window_key, events)
    
    async def run(self) -> None:
        """Run the micro-batcher."""
        self._running = True
        logger.info(f"Started micro-batcher with {self.window_seconds}s windows")
        
        try:
            # Create consumer group
            await self.bus.create_consumer_group("mdp.events", self.consumer_group)
            
            while self._running:
                try:
                    # Read events from stream
                    events = await self.bus.read_events(
                        self.consumer_group,
                        self.consumer_name,
                        count=1000,
                        block_ms=self.flush_timeout_ms
                    )
                    
                    # Process events
                    for event in events:
                        await self._process_event(event)
                    
                    # Flush expired windows
                    await self._flush_expired_windows()
                    
                    # Check if we need to flush due to timeout
                    now = datetime.utcnow()
                    if (now - self._last_flush).total_seconds() * 1000 >= self.flush_timeout_ms:
                        await self._flush_expired_windows()
                        self._last_flush = now
                    
                except Exception as e:
                    logger.error(f"Error in micro-batcher loop: {e}")
                    await asyncio.sleep(1)
                    
        except asyncio.CancelledError:
            logger.info("Micro-batcher cancelled")
        finally:
            # Flush all remaining windows
            for window_key, events in self.windows.items():
                await self._flush_window(window_key, events)
            
            self._running = False
            logger.info("Stopped micro-batcher")
    
    async def stop(self) -> None:
        """Stop the micro-batcher."""
        self._running = False
