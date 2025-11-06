"""
Phase 4 – Tick Analytics Metrics

Exposes:
  - tick_agg_rows_total{view}
  - tick_rate_per_symbol{provider,symbol}
"""

import os
import logging
import asyncpg
from prometheus_client import Gauge

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgres://postgres:postgres@md_postgres:5432/market_data",
)

tick_agg_rows_total = Gauge(
    "tick_agg_rows_total",
    "Estimated number of rows in tick aggregate views",
    ["view"],
)

tick_rate_per_symbol = Gauge(
    "tick_rate_per_symbol",
    "Approximate ticks per minute over the last 5 minutes (from tick_rate_stats)",
    ["provider", "symbol"],
)


async def _get_pool():
    """Get or create connection pool (simple singleton pattern)."""
    if not hasattr(_get_pool, "_pool"):
        _get_pool._pool = await asyncpg.create_pool(
            DATABASE_URL, min_size=1, max_size=4
        )
    return _get_pool._pool


async def collect_tick_analytics_metrics() -> None:
    """
    Collect tick analytics metrics from the store database.
    
    Call this periodically from whatever metrics/housekeeping loop
    you already have in the pipeline process.
    
    Updates:
    - tick_agg_rows_total{view} - Row counts for each aggregate view
    - tick_rate_per_symbol{provider,symbol} - Recent tick rates
    """
    try:
        pool = await _get_pool()

        async with pool.acquire() as conn:
            # 1) View sizes for tick_agg_* materialized views
            rows = await conn.fetch(
                """
                SELECT relname AS view, n_live_tup
                FROM pg_stat_user_tables
                WHERE relname LIKE 'tick_agg_%'
                   OR relname LIKE 'tick_vwap_%'
                   OR relname LIKE 'tick_spread_%'
                   OR relname LIKE 'tick_rate_%'
                """
            )
            for r in rows:
                tick_agg_rows_total.labels(view=r["view"]).set(r["n_live_tup"])

            # 2) Tick rate per symbol from last 5 minutes
            rows = await conn.fetch(
                """
                SELECT provider, symbol, SUM(ticks_per_minute) AS rate
                FROM tick_rate_stats
                WHERE bucket > NOW() - INTERVAL '5 minutes'
                GROUP BY provider, symbol
                """
            )
            # Clear old values by resetting the metric first
            tick_rate_per_symbol.clear()
            for r in rows:
                tick_rate_per_symbol.labels(r["provider"], r["symbol"]).set(
                    r["rate"]
                )

        logger.debug("Collected tick analytics metrics successfully")

    except Exception as exc:
        logger.warning("Failed to collect tick analytics metrics: %s", exc)


async def close_pool() -> None:
    """Close the connection pool on shutdown."""
    if hasattr(_get_pool, "_pool"):
        await _get_pool._pool.close()
        delattr(_get_pool, "_pool")

