#!/usr/bin/env bash
# Example usage of dual-table StoreSink

echo "=== StoreSink Dual-Table Example ==="

# Example 1: Write to bars_ohlcv (default)
echo "1. Writing to bars_ohlcv table:"
python -c "
import asyncio
from src.market_data_pipeline.sink.store import StoreSink
from src.market_data_pipeline.types import Bar
from datetime import datetime

async def test_bars_ohlcv():
    sink = StoreSink.from_env(table_name='bars_ohlcv')
    bar = Bar(
        source='synthetic',
        symbol='AAPL',
        timestamp=datetime.utcnow(),
        open=170.1,
        high=171.0,
        low=169.9,
        close=170.5,
        volume=10000
    )
    await sink.write([bar])
    print('✅ Written to bars_ohlcv')

asyncio.run(test_bars_ohlcv())
"

# Example 2: Write to legacy bars table
echo "2. Writing to legacy bars table:"
python -c "
import asyncio
from src.market_data_pipeline.sink.store import StoreSink
from src.market_data_pipeline.types import Bar
from datetime import datetime

async def test_bars():
    sink = StoreSink.from_env(table_name='bars')
    bar = Bar(
        source='synthetic',
        symbol='AAPL',
        timestamp=datetime.utcnow(),
        open=170.1,
        high=171.0,
        low=169.9,
        close=170.5,
        volume=10000
    )
    await sink.write([bar])
    print('✅ Written to bars')

asyncio.run(test_bars())
"

echo "=== Both tables supported! ==="
