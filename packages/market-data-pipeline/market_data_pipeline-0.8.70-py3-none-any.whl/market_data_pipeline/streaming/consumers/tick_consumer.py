"""
Phase 3 – TickConsumer

Consumes tick messages from the stream bus and persists them to TimescaleDB.
No aggregation or windowing - direct forwarding for raw tick preservation.
"""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime

from prometheus_client import Counter

from ..bus import Message, StreamBus

logger = logging.getLogger(__name__)

# Prometheus metrics
tick_forward_total = Counter(
    "tick_forward_total",
    "Total ticks forwarded to store",
    ["provider"]
)
tick_forward_failures_total = Counter(
    "tick_forward_failures_total",
    "Tick forward failures",
    ["provider"]
)


class TickConsumer:
    """
    Consumer that forwards raw tick data to market_data_store.
    
    Architecture:
        Stream Bus → TickConsumer → AsyncStoreClient.upsert_ticks() → tick_data table
    
    Features:
    - No aggregation (preserves raw tick granularity)
    - Batch forwarding for efficiency
    - Prometheus metrics for observability
    - Consumer group support for horizontal scaling
    """
    
    def __init__(
        self,
        bus: StreamBus,
        store_client,
        batch_size: int = 100,
        flush_timeout_ms: int = 1000,
        consumer_group: str = "tick-consumer",
        consumer_name: str = "tick-1",
        topic: str = "mdp.events"
    ):
        """
        Initialize TickConsumer.
        
        Args:
            bus: StreamBus instance (Redis/Kafka)
            store_client: AsyncStoreClient instance with upsert_ticks() method
            batch_size: Number of ticks to batch before flushing
            flush_timeout_ms: Max time to wait before flushing partial batch
            consumer_group: Consumer group name for distributed processing
            consumer_name: Unique consumer name within group
            topic: Stream topic to consume from
        """
        self.bus = bus
        self.store_client = store_client
        self.batch_size = batch_size
        self.flush_timeout_ms = flush_timeout_ms
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self.topic = topic
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the consumer."""
        if self._running:
            logger.warning("[TickConsumer] Already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._consume_loop())
        logger.info(
            f"[TickConsumer] Started: group={self.consumer_group}, "
            f"name={self.consumer_name}, topic={self.topic}, batch_size={self.batch_size}"
        )
    
    async def stop(self) -> None:
        """Stop the consumer gracefully."""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("[TickConsumer] Stopped")
    
    async def _consume_loop(self) -> None:
        """Main consumer loop - reads from bus and forwards to store."""
        try:
            # Create consumer group if needed
            try:
                await self.bus.create_consumer_group(self.topic, self.consumer_group)
            except Exception as e:
                logger.debug(f"[TickConsumer] Consumer group may already exist: {e}")
            
            while self._running:
                try:
                    # Read messages from stream
                    messages = await self.bus.read(
                        topic=self.topic,
                        group=self.consumer_group,
                        consumer=self.consumer_name,
                        count=self.batch_size,
                        block_ms=self.flush_timeout_ms
                    )
                    
                    if not messages:
                        await asyncio.sleep(0.1)
                        continue
                    
                    # Process batch
                    await self._process_batch(messages)
                    
                    # Acknowledge messages
                    for msg in messages:
                        try:
                            await self.bus.ack(self.topic, self.consumer_group, msg.id)
                        except Exception as e:
                            logger.warning(f"[TickConsumer] Failed to ack {msg.id}: {e}")
                
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"[TickConsumer] Error in consume loop: {e}")
                    await asyncio.sleep(1)  # Backoff on error
        
        except Exception as e:
            logger.error(f"[TickConsumer] Fatal error: {e}")
    
    async def _process_batch(self, messages: List[Message]) -> None:
        """Process a batch of messages and forward to store."""
        if not messages:
            return
        
        try:
            # Convert messages to tick dicts
            ticks = []
            provider_counts = {}
            
            for msg in messages:
                try:
                    tick = self._message_to_tick(msg)
                    if tick:
                        ticks.append(tick)
                        provider = tick.get("provider", "unknown")
                        provider_counts[provider] = provider_counts.get(provider, 0) + 1
                except Exception as e:
                    logger.warning(f"[TickConsumer] Failed to parse message {msg.id}: {e}")
                    continue
            
            if not ticks:
                logger.debug("[TickConsumer] No valid ticks in batch")
                return
            
            # Forward to store
            count = await self.store_client.upsert_ticks(ticks)
            
            # Record metrics by provider
            for provider, pcount in provider_counts.items():
                tick_forward_total.labels(provider=provider).inc(pcount)
            
            logger.debug(f"[TickConsumer] Forwarded {count} ticks: {provider_counts}")
        
        except Exception as e:
            logger.error(f"[TickConsumer] Failed to process batch: {e}")
            # Record failure metrics
            for msg in messages:
                provider = msg.payload.get("provider", "unknown")
                tick_forward_failures_total.labels(provider=provider).inc()
    
    def _message_to_tick(self, msg: Message) -> Optional[dict]:
        """
        Convert stream message to tick dict for store.
        
        Args:
            msg: Message from stream bus
            
        Returns:
            Tick dict with keys: provider, symbol, price, ts, size, bid, ask
            Returns None if message is not a tick event
        """
        payload = msg.payload
        
        # Filter for tick events only (not bars)
        kind = payload.get("kind", "tick")
        if kind != "tick":
            return None
        
        # Extract required fields
        symbol = payload.get("symbol")
        price = payload.get("price") or payload.get("c")  # price or close
        
        if not symbol or price is None:
            logger.warning(f"[TickConsumer] Missing required fields in message {msg.id}")
            return None
        
        # Parse timestamp
        ts_str = payload.get("src_ts") or payload.get("timestamp")
        if not ts_str:
            ts = datetime.utcnow()
        elif isinstance(ts_str, datetime):
            ts = ts_str
        else:
            try:
                # Handle ISO format with 'Z' suffix
                ts_str_clean = ts_str.replace("Z", "+00:00")
                ts = datetime.fromisoformat(ts_str_clean)
            except Exception as e:
                logger.warning(f"[TickConsumer] Invalid timestamp {ts_str}: {e}")
                ts = datetime.utcnow()
        
        # Build tick dict
        tick = {
            "provider": payload.get("provider", "ibkr"),
            "symbol": symbol,
            "price": float(price),
            "ts": ts,
            "size": payload.get("size") or payload.get("v"),  # size or volume
            "bid": payload.get("bid"),
            "ask": payload.get("ask"),
        }
        
        return tick

