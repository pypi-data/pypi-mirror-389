"""
Phase 5 – TickReplayer

Re-streams historical ticks from tick_data back onto the bus at configurable speed.
"""

import asyncio
import asyncpg
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)

# Metrics
replay_ticks_emitted = Counter(
    "tick_replay_ticks_emitted_total",
    "Total ticks emitted during replay",
    ["provider", "symbol", "run_id"],
)
replay_lag_ms = Gauge(
    "tick_replay_lag_ms",
    "Current lag vs original timestamps during replay",
    ["run_id"],
)
replay_errors = Counter(
    "tick_replay_errors_total", "Replay errors", ["run_id"]
)


@dataclass
class TickReplayRequest:
    """Request to replay historical ticks."""

    provider: str
    symbols: Sequence[str]
    start: datetime
    end: datetime
    speed: float  # 1.0=real-time, N>1=faster, 0=burst (no sleep)
    run_id: int | None = None


class TickReplayer:
    """
    Replays historical ticks from tick_data table onto the stream bus.

    Architecture:
        tick_data (store) → TickReplayer → Stream Bus → Consumers
    
    Features:
        - Configurable replay speed (1x, 10x, burst)
        - Job tracking via job_runs table
        - Prometheus metrics for monitoring
        - Respects original timing (for real-time mode)
    """

    def __init__(self, db_dsn: str, bus, max_batch_size: int = 1000):
        """
        Initialize TickReplayer.

        Args:
            db_dsn: Database connection string for store
            bus: StreamBus instance for publishing
            max_batch_size: Max ticks to fetch per DB query
        """
        self._dsn = db_dsn
        self._bus = bus
        self._max_batch = max_batch_size
        self._pool = None
        self._active_replays = {}  # run_id -> task

    async def _ensure_pool(self):
        """Ensure database connection pool exists."""
        if not self._pool:
            self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=4)

    async def start_replay(self, req: TickReplayRequest) -> int:
        """
        Start a tick replay job.

        Args:
            req: Replay request parameters

        Returns:
            run_id: Job run ID for tracking

        Raises:
            Exception: If job creation fails
        """
        await self._ensure_pool()

        # Create job_runs entry
        run_id = await self._create_job_run(req)
        req.run_id = run_id

        # Start background replay task
        task = asyncio.create_task(self._run_replay(req, run_id))
        self._active_replays[run_id] = task

        logger.info(
            f"[TickReplayer] Started replay run_id={run_id}, "
            f"provider={req.provider}, symbols={req.symbols}, "
            f"start={req.start}, end={req.end}, speed={req.speed}x"
        )

        return run_id

    async def _create_job_run(self, req: TickReplayRequest) -> int:
        """Create job_runs entry in store."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO job_runs (
                    job_name, provider, mode, status, symbols,
                    min_ts, max_ts, metadata
                )
                VALUES (
                    'tick_replay', $1, 'backfill', 'running', $2,
                    $3, $4, $5
                )
                RETURNING id
                """,
                req.provider,
                list(req.symbols),
                req.start,
                req.end,
                {
                    "speed": req.speed,
                    "max_batch_size": self._max_batch,
                },
            )
            return row["id"]

    async def _run_replay(self, req: TickReplayRequest, run_id: int) -> None:
        """
        Core replay loop.

        1. Fetch batches of ticks from tick_data ordered by ts
        2. For each tick, compute send time based on speed factor
        3. Sleep if needed to respect timing
        4. Publish to bus
        5. Update job_runs progress
        """
        try:
            start_time = time.monotonic()
            first_tick_ts = None
            total_ticks = 0
            last_ts = req.start

            while last_ts < req.end:
                # Fetch next batch
                ticks = await self._fetch_tick_batch(
                    req.provider, req.symbols, last_ts, req.end
                )

                if not ticks:
                    break

                # Process batch
                for tick in ticks:
                    tick_ts = tick["ts"]

                    # First tick establishes time anchor
                    if first_tick_ts is None:
                        first_tick_ts = tick_ts

                    # Compute when this tick should be sent (for paced replay)
                    if req.speed > 0:
                        elapsed_real = (tick_ts - first_tick_ts).total_seconds()
                        target_elapsed = elapsed_real / req.speed
                        actual_elapsed = time.monotonic() - start_time

                        sleep_time = target_elapsed - actual_elapsed
                        if sleep_time > 0:
                            await asyncio.sleep(sleep_time)

                    # Publish to bus
                    await self._publish_tick(tick, run_id)

                    # Update metrics
                    replay_ticks_emitted.labels(
                        provider=tick["provider"],
                        symbol=tick["symbol"],
                        run_id=str(run_id),
                    ).inc()

                    total_ticks += 1
                    last_ts = tick_ts

                    # Compute lag
                    if req.speed > 0 and first_tick_ts:
                        expected_elapsed = (tick_ts - first_tick_ts).total_seconds() / req.speed
                        actual_elapsed = time.monotonic() - start_time
                        lag_ms = (actual_elapsed - expected_elapsed) * 1000
                        replay_lag_ms.labels(run_id=str(run_id)).set(lag_ms)

                # Update job progress every batch
                await self._update_job_progress(run_id, total_ticks, last_ts)

            # Mark complete
            await self._complete_job(run_id, total_ticks, "success")
            logger.info(
                f"[TickReplayer] Completed run_id={run_id}, emitted {total_ticks} ticks"
            )

        except Exception as e:
            logger.error(f"[TickReplayer] Replay run_id={run_id} failed: {e}")
            replay_errors.labels(run_id=str(run_id)).inc()
            await self._complete_job(run_id, total_ticks, "failure", str(e))
            raise

        finally:
            if run_id in self._active_replays:
                del self._active_replays[run_id]

    async def _fetch_tick_batch(
        self, provider: str, symbols: Sequence[str], start_ts: datetime, end_ts: datetime
    ) -> list:
        """Fetch next batch of ticks from tick_data."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT provider, symbol, price, ts, size, bid, ask
                FROM tick_data
                WHERE provider = $1
                  AND symbol = ANY($2)
                  AND ts >= $3
                  AND ts < $4
                ORDER BY ts ASC
                LIMIT $5
                """,
                provider,
                list(symbols),
                start_ts,
                end_ts,
                self._max_batch,
            )

            return [
                {
                    "provider": row["provider"],
                    "symbol": row["symbol"],
                    "price": float(row["price"]),
                    "ts": row["ts"],
                    "size": float(row["size"]) if row["size"] else None,
                    "bid": float(row["bid"]) if row["bid"] else None,
                    "ask": float(row["ask"]) if row["ask"] else None,
                }
                for row in rows
            ]

    async def _publish_tick(self, tick: dict, run_id: int) -> None:
        """Publish tick to stream bus with replay metadata."""
        # Convert to stream bus format
        payload = {
            "kind": "tick",
            "provider": tick["provider"],
            "symbol": tick["symbol"],
            "price": tick["price"],
            "timestamp": tick["ts"].isoformat(),
            "size": tick["size"],
            "bid": tick["bid"],
            "ask": tick["ask"],
            "origin": "replay",  # Metadata to identify replayed ticks
            "replay_run_id": run_id,
        }

        # Publish to bus
        topic = "mdp.events"  # Same topic as live ticks
        await self._bus.publish(topic, payload)

    async def _update_job_progress(self, run_id: int, rows_written: int, max_ts: datetime) -> None:
        """Update job_runs with current progress."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE job_runs
                SET rows_written = $1, max_ts = $2, updated_at = NOW()
                WHERE id = $3
                """,
                rows_written,
                max_ts,
                run_id,
            )

    async def _complete_job(
        self, run_id: int, rows_written: int, status: str, error_msg: str | None = None
    ) -> None:
        """Mark job as complete."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE job_runs
                SET status = $1, rows_written = $2, completed_at = NOW(),
                    error_message = $3, updated_at = NOW()
                WHERE id = $4
                """,
                status,
                rows_written,
                error_msg,
                run_id,
            )

    async def get_status(self, run_id: int) -> dict:
        """
        Get status of a replay job.

        Args:
            run_id: Job run ID

        Returns:
            Status dict with job details
        """
        await self._ensure_pool()

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, job_name, provider, mode, status, symbols,
                       rows_written, min_ts, max_ts, started_at, completed_at,
                       error_message, metadata
                FROM job_runs
                WHERE id = $1
                """,
                run_id,
            )

            if not row:
                raise ValueError(f"Job run_id={run_id} not found")

            return {
                "run_id": row["id"],
                "job_name": row["job_name"],
                "provider": row["provider"],
                "status": row["status"],
                "symbols": row["symbols"],
                "rows_written": row["rows_written"],
                "min_ts": row["min_ts"],
                "max_ts": row["max_ts"],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "error_message": row["error_message"],
                "metadata": row["metadata"],
            }

    async def close(self) -> None:
        """Clean shutdown - cancel active replays and close pool."""
        for run_id, task in list(self._active_replays.items()):
            logger.info(f"[TickReplayer] Cancelling replay run_id={run_id}")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        if self._pool:
            await self._pool.close()

