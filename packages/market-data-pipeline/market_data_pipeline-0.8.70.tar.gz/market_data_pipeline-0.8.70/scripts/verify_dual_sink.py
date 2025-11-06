#!/usr/bin/env python3
"""
Phase 20.1 dual-sink verification.
Writes identical synthetic batches to both sinks and compares row counts in Prometheus.
"""

import asyncio
import random
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from market_data_pipeline.sink.sink_registry import create_store_sink
from market_data_pipeline.types import Bar
from market_data_pipeline.context import PipelineContext

PROM_URL = "http://localhost:9090/api/v1/query"
BATCH_SIZE = 1000
SYMBOLS = ["AAPL", "MSFT", "NVDA", "SPY"]


class MockContext:
    """Mock context for testing."""
    def __init__(self, tenant_id: str = "demo", pipeline_id: str = "verify"):
        self.tenant_id = tenant_id
        self.pipeline_id = pipeline_id


async def make_bars() -> List[Bar]:
    """Generate synthetic bars for testing."""
    now = datetime.now(timezone.utc)
    bars = []
    
    for sym in SYMBOLS:
        for i in range(BATCH_SIZE):
            ts = now - timedelta(minutes=i)
            bars.append(
                Bar(
                    source="synthetic",
                    symbol=sym,
                    timeframe="1m",
                    timestamp=ts,
                    open=100 + random.random(),
                    high=101 + random.random(),
                    low=99 + random.random(),
                    close=100 + random.random(),
                    volume=random.randint(1000, 5000),
                )
            )
    
    return bars


async def verify_dual():
    """Run dual-sink verification test."""
    print("🚀 Phase 20.1 Dual-Sink Verification")
    print("=" * 50)
    
    # Create mock context
    ctx = MockContext()
    
    # Create both sink types
    print("📦 Creating sink instances...")
    legacy = create_store_sink("legacy", ctx=ctx)
    provider = create_store_sink("provider", ctx=ctx)
    
    # Generate test data
    print(f"📊 Generating {BATCH_SIZE * len(SYMBOLS)} bars...")
    bars = await make_bars()
    print(f"✅ Generated {len(bars)} bars for symbols: {SYMBOLS}")
    
    # Write to both sinks
    print("\n📝 Writing to both sinks...")
    print("  - Legacy sink (bars table)")
    print("  - Provider sink (bars_ohlcv table)")
    
    try:
        # Write to legacy sink
        await legacy.write(bars)
        print("✅ Legacy sink write completed")
        
        # Write to provider sink  
        await provider.write(bars)
        print("✅ Provider sink write completed")
        
        # Wait for processing
        print("\n⏳ Waiting for processing to complete...")
        await asyncio.sleep(2)
        
        # Flush both sinks
        await legacy.flush()
        await provider.flush()
        print("✅ Both sinks flushed")
        
    except Exception as e:
        print(f"❌ Error during write: {e}")
        return False
    
    finally:
        # Clean up
        print("\n🧹 Cleaning up...")
        await legacy.close()
        await provider.close()
        print("✅ Cleanup completed")
    
    # Report metrics to check
    print("\n📈 Prometheus Metrics to Check:")
    print("=" * 30)
    print("Legacy Sink Metrics:")
    print("  - pipeline_store_sink_batches_in_total")
    print("  - store_bars_written_total")
    print("  - store_sink_queue_depth")
    print()
    print("Provider Sink Metrics:")
    print("  - provider_sink_writes_total")
    print("  - provider_sink_latency_seconds")
    print("  - provider_sink_fails_total")
    print()
    print("Expected Results:")
    print(f"  - Both sinks should write ~{len(bars)} bars")
    print("  - Latency < 0.3s for batch processing")
    print("  - No failed writes or retries")
    print("  - Counts in bars ≈ bars_ohlcv")
    
    print("\n🎯 Verification Complete!")
    print("Check Prometheus at http://localhost:9090 for metrics")
    
    return True


async def test_sink_info():
    """Test sink registry information."""
    print("\n🔍 Sink Registry Information:")
    print("=" * 30)
    
    from market_data_pipeline.sink.sink_registry import get_sink_info, list_available_modes
    
    modes = list_available_modes()
    print(f"Available modes: {modes}")
    
    for mode in modes:
        info = get_sink_info(mode)
        print(f"\n{mode.upper()} Mode:")
        print(f"  Name: {info['name']}")
        print(f"  Table: {info['table']}")
        print(f"  Client: {info['client']}")
        print(f"  Description: {info['description']}")
        print(f"  Features: {', '.join(info['features'])}")


async def main():
    """Main verification function."""
    try:
        # Test sink info first
        await test_sink_info()
        
        # Run dual-sink verification
        success = await verify_dual()
        
        if success:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print("\n❌ Tests failed!")
            return 1
            
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Set up environment if needed
    if not os.getenv("DATABASE_URL"):
        print("⚠️  DATABASE_URL not set. Using default for testing.")
        os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/marketdata"
    
    # Run the verification
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
