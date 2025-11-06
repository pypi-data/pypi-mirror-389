"""
Phase 5 – SignalConsumer

Computes real-time signals from tick stream and persists to signals table.
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from prometheus_client import Counter, Histogram

from ..bus import Message, StreamBus

logger = logging.getLogger(__name__)

# Metrics
signals_written = Counter(
    "signals_written_total", "Total signals written", ["name"]
)
signals_write_failures = Counter(
    "signals_write_failures_total", "Signal write failures", ["name"]
)
signals_compute_duration = Histogram(
    "signals_compute_duration_seconds",
    "Time to compute signals",
    ["name"],
)


class SignalBuffer:
    """Buffer for computing signals on streaming ticks."""

    def __init__(self, max_age_seconds: int = 60):
        self.ticks = []  # Recent ticks for this symbol
        self.max_age = timedelta(seconds=max_age_seconds)

    def add_tick(self, tick: dict):
        """Add tick and prune old ones."""
        self.ticks.append(tick)

        # Prune old ticks
        if len(self.ticks) > 1000:  # Keep last 1000 ticks max
            self.ticks = self.ticks[-1000:]

    def get_recent_ticks(self, lookback_seconds: int = 60) -> List[dict]:
        """Get ticks from last N seconds."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=lookback_seconds)
        return [t for t in self.ticks if t["ts"] >= cutoff]


class SignalConsumer:
    """
    Consumes ticks and generates real-time signals.

    Signals computed:
        - vwap_deviation_bps: Deviation from daily VWAP
        - spread_bps: Bid-ask spread
        - tick_rate_zscore: Tick frequency anomaly (future)

    Architecture:
        Stream Bus → SignalConsumer → insert_signals() → signals table
    """

    def __init__(
        self,
        bus: StreamBus,
        store_client,
        batch_size: int = 200,
        flush_interval_seconds: int = 5,
        consumer_group: str = "signal-consumer",
        consumer_name: str = "signal-1",
        topic: str = "mdp.events",
    ):
        """
        Initialize SignalConsumer.

        Args:
            bus: StreamBus instance
            store_client: AsyncStoreClient with insert_signals() method
            batch_size: Signals to batch before writing
            flush_interval_seconds: Max time between flushes
            consumer_group: Consumer group name
            consumer_name: Unique consumer name
            topic: Stream topic to consume
        """
        self._bus = bus
        self._store = store_client
        self._batch_size = batch_size
        self._flush_interval = flush_interval_seconds
        self._consumer_group = consumer_group
        self._consumer_name = consumer_name
        self._topic = topic

        # Per-symbol buffers for tick history
        self._buffers: Dict[tuple, SignalBuffer] = defaultdict(SignalBuffer)

        # Pending signals to write
        self._pending_signals = []

        # Control
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._flush_task: Optional[asyncio.Task] = None

        # Cache for daily VWAP (fetch periodically)
        self._vwap_cache = {}  # (provider, symbol) -> (vwap, fetched_at)
        self._vwap_cache_ttl = timedelta(minutes=5)

    async def start(self) -> None:
        """Start the signal consumer."""
        if self._running:
            logger.warning("[SignalConsumer] Already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._consume_loop())
        self._flush_task = asyncio.create_task(self._flush_loop())

        logger.info(
            f"[SignalConsumer] Started: group={self._consumer_group}, "
            f"name={self._consumer_name}, batch={self._batch_size}"
        )

    async def stop(self) -> None:
        """Stop the signal consumer."""
        if not self._running:
            return

        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Final flush
        await self._flush_signals()

        logger.info("[SignalConsumer] Stopped")

    async def _consume_loop(self) -> None:
        """Main consume loop."""
        try:
            # Create consumer group
            try:
                await self._bus.create_consumer_group(self._topic, self._consumer_group)
            except Exception as e:
                logger.debug(f"[SignalConsumer] Consumer group may exist: {e}")

            while self._running:
                try:
                    # Read messages
                    messages = await self._bus.read(
                        topic=self._topic,
                        group=self._consumer_group,
                        consumer=self._consumer_name,
                        count=100,
                        block_ms=1000,
                    )

                    if not messages:
                        await asyncio.sleep(0.1)
                        continue

                    # Process batch
                    await self._process_messages(messages)

                    # Acknowledge
                    for msg in messages:
                        try:
                            await self._bus.ack(self._topic, self._consumer_group, msg.id)
                        except Exception as e:
                            logger.warning(f"[SignalConsumer] Failed to ack {msg.id}: {e}")

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"[SignalConsumer] Error in consume loop: {e}")
                    await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"[SignalConsumer] Fatal error: {e}")

    async def _flush_loop(self) -> None:
        """Periodic flush of pending signals."""
        while self._running:
            try:
                await asyncio.sleep(self._flush_interval)
                await self._flush_signals()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[SignalConsumer] Flush loop error: {e}")

    async def _process_messages(self, messages: List[Message]) -> None:
        """Process messages and generate signals."""
        for msg in messages:
            try:
                tick = self._parse_tick(msg)
                if tick:
                    await self._process_tick(tick)
            except Exception as e:
                logger.warning(f"[SignalConsumer] Failed to process message: {e}")

    def _parse_tick(self, msg: Message) -> Optional[dict]:
        """Parse message into tick dict."""
        payload = msg.payload

        # Filter for tick events
        if payload.get("kind") != "tick":
            return None

        symbol = payload.get("symbol")
        price = payload.get("price")

        if not symbol or price is None:
            return None

        # Parse timestamp
        ts_str = payload.get("timestamp") or payload.get("src_ts")
        if isinstance(ts_str, str):
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        elif isinstance(ts_str, datetime):
            ts = ts_str
        else:
            ts = datetime.now(timezone.utc)

        return {
            "provider": payload.get("provider", "ibkr"),
            "symbol": symbol,
            "price": float(price),
            "ts": ts,
            "size": payload.get("size"),
            "bid": payload.get("bid"),
            "ask": payload.get("ask"),
            "replay_run_id": payload.get("replay_run_id"),  # Track if from replay
        }

    async def _process_tick(self, tick: dict) -> None:
        """Process tick and generate signals."""
        provider = tick["provider"]
        symbol = tick["symbol"]
        key = (provider, symbol)

        # Add to buffer
        self._buffers[key].add_tick(tick)

        # Compute signals
        await self._compute_vwap_deviation(tick)
        await self._compute_spread_signal(tick)

        # Flush if batch is full
        if len(self._pending_signals) >= self._batch_size:
            await self._flush_signals()

    async def _compute_vwap_deviation(self, tick: dict) -> None:
        """Compute VWAP deviation signal."""
        try:
            with signals_compute_duration.labels(name="vwap_deviation_bps").time():
                provider = tick["provider"]
                symbol = tick["symbol"]
                price = tick["price"]
                ts = tick["ts"]

                # Get daily VWAP from cache or DB
                vwap = await self._get_daily_vwap(provider, symbol, ts)

                if vwap is None or vwap == 0:
                    return  # No VWAP available yet

                # Compute deviation in basis points
                deviation_bps = ((price - vwap) / vwap) * 10000

                signal = {
                    "provider": provider,
                    "symbol": symbol,
                    "ts": ts,
                    "name": "vwap_deviation_bps",
                    "value": deviation_bps,
                    "score": abs(deviation_bps) / 100,  # Normalize to ~0-1 range
                    "metadata": {
                        "vwap": vwap,
                        "price": price,
                        "replay_run_id": tick.get("replay_run_id"),
                    },
                }

                self._pending_signals.append(signal)

        except Exception as e:
            logger.warning(f"[SignalConsumer] VWAP deviation failed: {e}")

    async def _compute_spread_signal(self, tick: dict) -> None:
        """Compute bid-ask spread signal."""
        try:
            with signals_compute_duration.labels(name="spread_bps").time():
                bid = tick.get("bid")
                ask = tick.get("ask")

                if bid is None or ask is None or bid == 0:
                    return

                spread = ask - bid
                mid = (ask + bid) / 2
                spread_bps = (spread / mid) * 10000

                signal = {
                    "provider": tick["provider"],
                    "symbol": tick["symbol"],
                    "ts": tick["ts"],
                    "name": "spread_bps",
                    "value": spread_bps,
                    "score": spread_bps / 100,  # Normalize
                    "metadata": {
                        "bid": bid,
                        "ask": ask,
                        "spread": spread,
                        "replay_run_id": tick.get("replay_run_id"),
                    },
                }

                self._pending_signals.append(signal)

        except Exception as e:
            logger.warning(f"[SignalConsumer] Spread signal failed: {e}")

    async def _get_daily_vwap(
        self, provider: str, symbol: str, ts: datetime
    ) -> Optional[float]:
        """Get daily VWAP from cache or fetch from DB."""
        key = (provider, symbol)
        now = datetime.now(timezone.utc)

        # Check cache
        if key in self._vwap_cache:
            vwap, fetched_at = self._vwap_cache[key]
            if now - fetched_at < self._vwap_cache_ttl:
                return vwap

        # Fetch from DB (tick_vwap_daily view)
        try:
            # This requires a DB connection - simplified for now
            # In production, use self._store or separate connection
            # For now, return None (signals won't compute until VWAP available)
            # TODO: Add actual DB fetch
            return None

        except Exception as e:
            logger.warning(f"[SignalConsumer] Failed to fetch VWAP: {e}")
            return None

    async def _flush_signals(self) -> None:
        """Flush pending signals to store."""
        if not self._pending_signals:
            return

        signals = self._pending_signals[:]
        self._pending_signals.clear()

        try:
            count = await self._store.insert_signals(signals)

            # Update metrics per signal type
            signal_counts = {}
            for sig in signals:
                name = sig["name"]
                signal_counts[name] = signal_counts.get(name, 0) + 1

            for name, cnt in signal_counts.items():
                signals_written.labels(name=name).inc(cnt)

            logger.debug(f"[SignalConsumer] Flushed {count} signals: {signal_counts}")

        except Exception as e:
            logger.error(f"[SignalConsumer] Failed to flush signals: {e}")
            for sig in signals:
                signals_write_failures.labels(name=sig["name"]).inc()

