"""
Sink Factory for Dynamic Store Sink Selection (Phase 20.1)
Supports both legacy AMDS-based and provider-based store sinks.
"""

from __future__ import annotations
from typing import Optional, Dict, Any

from ..context import PipelineContext
from .store import StoreSink as StoreSinkLegacy
from .store_sink_provider import StoreSink as StoreSinkProvider


def create_store_sink(mode: str = "legacy", **kwargs) -> StoreSinkLegacy | StoreSinkProvider:
    """
    Factory to create store sinks dynamically.
    
    Args:
        mode: Sink mode selection
            - 'legacy'   → tenant-based AMDS sink (writes to bars)
            - 'provider' → AsyncStoreClient sink (writes to bars_ohlcv)
        **kwargs: Additional arguments passed to sink constructor
    
    Returns:
        Configured store sink instance
        
    Raises:
        ValueError: If mode is not supported
    """
    if mode == "legacy":
        # Legacy sink supports all parameters
        return StoreSinkLegacy(**kwargs)
    elif mode == "provider":
        # Provider sink only supports specific parameters
        provider_kwargs = {
            k: v for k, v in kwargs.items() 
            if k in ["db_uri", "workers", "queue_max", "default_timeframe", "ctx"]
        }
        return StoreSinkProvider(**provider_kwargs)
    else:
        raise ValueError(f"Invalid sink mode: {mode}. Supported modes: 'legacy', 'provider'")


def create_store_sink_from_env(**kwargs) -> StoreSinkLegacy | StoreSinkProvider:
    """
    Create store sink from environment variables.
    
    Environment Variables:
        STORE_MODE: Sink mode ('legacy' or 'provider')
        DATABASE_URL: Database connection string
        STORE_WORKERS: Number of worker threads (default: 2)
        STORE_QUEUE_MAX: Maximum queue size (default: 100)
        STORE_TIMEFRAME: Default timeframe (default: '1m')
    
    Args:
        **kwargs: Override environment variables
    
    Returns:
        Configured store sink instance
    """
    import os
    
    mode = kwargs.get("mode", os.getenv("STORE_MODE", "legacy"))
    
    # Extract common parameters
    sink_kwargs = {
        "db_uri": kwargs.get("db_uri", os.getenv("DATABASE_URL")),
        "workers": int(kwargs.get("workers", os.getenv("STORE_WORKERS", "2"))),
        "queue_max": int(kwargs.get("queue_max", os.getenv("STORE_QUEUE_MAX", "100"))),
        "default_timeframe": kwargs.get("default_timeframe", os.getenv("STORE_TIMEFRAME", "1m")),
        "ctx": kwargs.get("ctx"),
    }
    
    # Remove None values
    sink_kwargs = {k: v for k, v in sink_kwargs.items() if v is not None}
    
    return create_store_sink(mode=mode, **sink_kwargs)


def get_sink_info(mode: str) -> Dict[str, Any]:
    """
    Get information about a sink mode.
    
    Args:
        mode: Sink mode ('legacy' or 'provider')
    
    Returns:
        Dictionary with sink information
    
    Raises:
        ValueError: If mode is not supported
    """
    info = {
        "legacy": {
            "name": "Legacy AMDS Sink",
            "table": "bars",
            "client": "mds_client.aclient.AMDS",
            "description": "Tenant-based sink using AMDS for bars table",
            "features": ["tenant_id", "retry_logic", "batch_splitting", "telemetry"]
        },
        "provider": {
            "name": "Provider Store Sink", 
            "table": "bars_ohlcv",
            "client": "market_data_store.store_client.AsyncStoreClient",
            "description": "Provider-based sink using AsyncStoreClient for bars_ohlcv table",
            "features": ["provider_mapping", "high_throughput", "prometheus_metrics"]
        }
    }
    
    if mode not in info:
        raise ValueError(f"Invalid sink mode: {mode}. Supported modes: {list(info.keys())}")
    
    return info[mode]


def list_available_modes() -> list[str]:
    """List all available sink modes."""
    return ["legacy", "provider"]
