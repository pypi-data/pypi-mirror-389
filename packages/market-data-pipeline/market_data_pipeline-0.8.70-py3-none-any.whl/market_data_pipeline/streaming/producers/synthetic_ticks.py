"""
Synthetic tick producer for testing and development.

Generates realistic market data events for testing stream processing.
"""

import asyncio
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import math

from .base import EventProducer

logger = logging.getLogger(__name__)


class SyntheticTickProducer(EventProducer):
    """Producer that generates synthetic tick data."""
    
    def __init__(
        self, 
        bus, 
        symbols: List[str] = None,
        tick_rate: float = 1.0,  # ticks per second per symbol
        price_volatility: float = 0.02,  # 2% volatility
        seed: int = 42,
        **kwargs
    ):
        super().__init__(bus, "synthetic", **kwargs)
        self.symbols = symbols or ["SPY", "AAPL", "MSFT", "GOOGL", "TSLA"]
        self.tick_rate = tick_rate
        self.price_volatility = price_volatility
        self.seed = seed
        
        # Initialize random state
        random.seed(seed)
        
        # Track state for each symbol
        self.symbol_states = {}
        for symbol in self.symbols:
            self.symbol_states[symbol] = {
                "price": 100.0 + random.uniform(-50, 50),  # Random starting price
                "volume": 1000,
                "seq": 0,
                "last_tick": datetime.utcnow()
            }
    
    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Generate synthetic tick data."""
        now = datetime.utcnow()
        
        # Select a random symbol
        symbol = random.choice(self.symbols)
        state = self.symbol_states[symbol]
        
        # Check if enough time has passed for this symbol
        time_since_last = (now - state["last_tick"]).total_seconds()
        if time_since_last < (1.0 / self.tick_rate):
            return None
        
        # Generate price movement
        price_change = random.gauss(0, self.price_volatility)
        new_price = state["price"] * (1 + price_change)
        
        # Ensure price stays positive
        new_price = max(new_price, 0.01)
        
        # Generate volume (log-normal distribution)
        volume = int(random.lognormvariate(math.log(1000), 0.5))
        
        # Update state
        state["price"] = new_price
        state["volume"] = volume
        state["seq"] += 1
        state["last_tick"] = now
        
        # Create tick data
        tick_data = {
            "symbol": symbol,
            "timestamp": now.isoformat() + "Z",
            "price": round(new_price, 2),
            "size": volume,
            "seq": state["seq"],
            "bid": round(new_price * 0.999, 2),
            "ask": round(new_price * 1.001, 2),
            "bid_size": volume // 2,
            "ask_size": volume // 2
        }
        
        return tick_data
    
    async def generate_bar_data(self, symbol: str, interval: str = "1m") -> Dict[str, Any]:
        """Generate synthetic bar data for backfill scenarios."""
        state = self.symbol_states[symbol]
        now = datetime.utcnow()
        
        # Generate OHLCV data
        base_price = state["price"]
        volatility = self.price_volatility
        
        # Generate open, high, low, close
        open_price = base_price
        close_price = base_price * (1 + random.gauss(0, volatility))
        
        # High and low should bracket the open/close
        high_price = max(open_price, close_price) * (1 + abs(random.gauss(0, volatility/2)))
        low_price = min(open_price, close_price) * (1 - abs(random.gauss(0, volatility/2)))
        
        # Generate volume
        volume = int(random.lognormvariate(math.log(10000), 0.5))
        
        # Update state
        state["price"] = close_price
        
        bar_data = {
            "symbol": symbol,
            "timestamp": now.isoformat() + "Z",
            "interval": interval,
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": volume,
            "seq": state["seq"]
        }
        
        return bar_data
