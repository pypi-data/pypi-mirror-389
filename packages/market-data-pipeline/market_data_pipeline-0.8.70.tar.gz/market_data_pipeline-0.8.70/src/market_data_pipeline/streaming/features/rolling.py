"""
Rolling window features for market data.

Computes VWAP, returns, volatility, and other rolling features.
"""

import logging
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, NamedTuple
import statistics
import math

logger = logging.getLogger(__name__)


class FeatureWindow(NamedTuple):
    """Represents a feature window configuration."""
    name: str
    horizon_seconds: int
    max_points: int = 1000


class RollingFeatures:
    """Computes rolling window features for market data."""
    
    def __init__(self, windows: List[FeatureWindow]):
        self.windows = {w.name: w for w in windows}
        self.symbol_data: Dict[str, Dict[str, deque]] = {}
        self.symbol_timestamps: Dict[str, deque] = {}
    
    def _get_symbol_data(self, symbol: str) -> Dict[str, deque]:
        """Get or create data structure for a symbol."""
        if symbol not in self.symbol_data:
            self.symbol_data[symbol] = {}
            self.symbol_timestamps[symbol] = deque(maxlen=1000)
        return self.symbol_data[symbol]
    
    def _cleanup_old_data(self, symbol: str, cutoff_time: datetime) -> None:
        """Remove data older than cutoff time."""
        timestamps = self.symbol_timestamps[symbol]
        
        # Remove old timestamps
        while timestamps and timestamps[0] < cutoff_time:
            timestamps.popleft()
        
        # Remove corresponding data points
        for feature_name, data in self.symbol_data[symbol].items():
            while len(data) > len(timestamps):
                data.popleft()
    
    def update(self, symbol: str, bar_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update features with new bar data.
        
        Args:
            symbol: Symbol name
            bar_data: Bar data with OHLCV
            
        Returns:
            Dictionary of computed features
        """
        ts = bar_data.get("ts", datetime.utcnow())
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        
        # Get symbol data
        data = self._get_symbol_data(symbol)
        
        # Add timestamp
        self.symbol_timestamps[symbol].append(ts)
        
        # Add price data
        if "prices" not in data:
            data["prices"] = deque(maxlen=1000)
        if "volumes" not in data:
            data["volumes"] = deque(maxlen=1000)
        if "returns" not in data:
            data["returns"] = deque(maxlen=1000)
        
        # Extract OHLCV
        open_price = bar_data.get("open", 0)
        high_price = bar_data.get("high", 0)
        low_price = bar_data.get("low", 0)
        close_price = bar_data.get("close", 0)
        volume = bar_data.get("volume", 0)
        
        # Use close price as primary price
        price = close_price
        data["prices"].append(price)
        data["volumes"].append(volume)
        
        # Calculate returns
        if len(data["prices"]) > 1:
            prev_price = data["prices"][-2]
            if prev_price > 0:
                returns = (price - prev_price) / prev_price
                data["returns"].append(returns)
        
        # Clean up old data
        cutoff_time = ts - timedelta(seconds=max(w.horizon_seconds for w in self.windows.values()))
        self._cleanup_old_data(symbol, cutoff_time)
        
        # Compute features
        features = {}
        for window_name, window in self.windows.items():
            features.update(self._compute_window_features(symbol, window_name, window, ts))
        
        return features
    
    def _compute_window_features(
        self, 
        symbol: str, 
        window_name: str, 
        window: FeatureWindow, 
        current_time: datetime
    ) -> Dict[str, Any]:
        """Compute features for a specific window."""
        data = self.symbol_data[symbol]
        timestamps = self.symbol_timestamps[symbol]
        
        # Get data within window
        cutoff_time = current_time - timedelta(seconds=window.horizon_seconds)
        window_data = []
        window_volumes = []
        window_returns = []
        
        for i, ts in enumerate(timestamps):
            if ts >= cutoff_time:
                if i < len(data["prices"]):
                    window_data.append(data["prices"][i])
                if i < len(data["volumes"]):
                    window_volumes.append(data["volumes"][i])
                if i < len(data["returns"]):
                    window_returns.append(data["returns"][i])
        
        if not window_data:
            return {}
        
        features = {}
        
        # Basic statistics
        features[f"{window_name}_price_mean"] = statistics.mean(window_data)
        features[f"{window_name}_price_std"] = statistics.stdev(window_data) if len(window_data) > 1 else 0
        features[f"{window_name}_price_min"] = min(window_data)
        features[f"{window_name}_price_max"] = max(window_data)
        
        # Volume statistics
        if window_volumes:
            features[f"{window_name}_volume_sum"] = sum(window_volumes)
            features[f"{window_name}_volume_mean"] = statistics.mean(window_volumes)
        
        # VWAP (Volume Weighted Average Price)
        if window_volumes and sum(window_volumes) > 0:
            vwap = sum(p * v for p, v in zip(window_data, window_volumes)) / sum(window_volumes)
            features[f"{window_name}_vwap"] = vwap
        
        # Returns statistics
        if window_returns:
            features[f"{window_name}_returns_mean"] = statistics.mean(window_returns)
            features[f"{window_name}_returns_std"] = statistics.stdev(window_returns) if len(window_returns) > 1 else 0
            features[f"{window_name}_returns_skew"] = self._skewness(window_returns)
            features[f"{window_name}_returns_kurtosis"] = self._kurtosis(window_returns)
        
        # Volatility (annualized)
        if len(window_returns) > 1:
            returns_std = statistics.stdev(window_returns)
            # Annualize assuming 252 trading days
            volatility = returns_std * math.sqrt(252)
            features[f"{window_name}_volatility"] = volatility
        
        # Price momentum
        if len(window_data) > 1:
            momentum = (window_data[-1] - window_data[0]) / window_data[0]
            features[f"{window_name}_momentum"] = momentum
        
        # RSI (simplified)
        if len(window_data) > 14:
            rsi = self._compute_rsi(window_data[-14:])
            features[f"{window_name}_rsi"] = rsi
        
        return features
    
    def _skewness(self, data: List[float]) -> float:
        """Compute skewness of data."""
        if len(data) < 3:
            return 0.0
        
        mean = statistics.mean(data)
        std = statistics.stdev(data)
        if std == 0:
            return 0.0
        
        n = len(data)
        skewness = (n / ((n - 1) * (n - 2))) * sum(((x - mean) / std) ** 3 for x in data)
        return skewness
    
    def _kurtosis(self, data: List[float]) -> float:
        """Compute kurtosis of data."""
        if len(data) < 4:
            return 0.0
        
        mean = statistics.mean(data)
        std = statistics.stdev(data)
        if std == 0:
            return 0.0
        
        n = len(data)
        kurtosis = (n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))) * sum(((x - mean) / std) ** 4 for x in data)
        kurtosis -= 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))
        return kurtosis
    
    def _compute_rsi(self, prices: List[float], period: int = 14) -> float:
        """Compute RSI (Relative Strength Index)."""
        if len(prices) < period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-change)
        
        if len(gains) < period:
            return 50.0
        
        avg_gain = statistics.mean(gains[-period:])
        avg_loss = statistics.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def get_current_features(self, symbol: str) -> Dict[str, Any]:
        """Get current feature values for a symbol."""
        if symbol not in self.symbol_data:
            return {}
        
        data = self.symbol_data[symbol]
        timestamps = self.symbol_timestamps[symbol]
        
        if not timestamps:
            return {}
        
        current_time = timestamps[-1]
        features = {}
        
        for window_name, window in self.windows.items():
            window_features = self._compute_window_features(symbol, window_name, window, current_time)
            features.update(window_features)
        
        return features
    
    def reset(self, symbol: str) -> None:
        """Reset features for a symbol."""
        if symbol in self.symbol_data:
            del self.symbol_data[symbol]
        if symbol in self.symbol_timestamps:
            del self.symbol_timestamps[symbol]
    
    def get_symbols(self) -> List[str]:
        """Get list of symbols with active features."""
        return list(self.symbol_data.keys())
