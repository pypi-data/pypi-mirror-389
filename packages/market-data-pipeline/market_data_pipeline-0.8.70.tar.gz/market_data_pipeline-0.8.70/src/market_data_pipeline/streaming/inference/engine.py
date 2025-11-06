"""
Inference engine for signal generation.

Evaluates features and generates trading signals.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

from ..bus import SignalEvent
from .adapters.base import InferenceAdapter

logger = logging.getLogger(__name__)


class InferenceEngine:
    """Engine for evaluating features and generating signals."""
    
    def __init__(self, adapters: List[InferenceAdapter]):
        self.adapters = {adapter.name: adapter for adapter in adapters}
        self._running = False
    
    async def evaluate(self, symbol: str, features: Dict[str, Any]) -> List[SignalEvent]:
        """
        Evaluate features and generate signals.
        
        Args:
            symbol: Symbol name
            features: Feature dictionary
            
        Returns:
            List of generated signals
        """
        signals = []
        
        for adapter_name, adapter in self.adapters.items():
            try:
                # Evaluate with adapter
                adapter_signals = await adapter.evaluate(symbol, features)
                signals.extend(adapter_signals)
                
                logger.debug(f"Generated {len(adapter_signals)} signals from {adapter_name} for {symbol}")
                
            except Exception as e:
                logger.error(f"Error in adapter {adapter_name}: {e}")
                continue
        
        return signals
    
    async def start(self) -> None:
        """Start the inference engine."""
        self._running = True
        logger.info("Started inference engine")
        
        # Start all adapters
        for adapter in self.adapters.values():
            await adapter.start()
    
    async def stop(self) -> None:
        """Stop the inference engine."""
        self._running = False
        
        # Stop all adapters
        for adapter in self.adapters.values():
            await adapter.stop()
        
        logger.info("Stopped inference engine")
    
    def get_adapter_status(self) -> Dict[str, Any]:
        """Get status of all adapters."""
        status = {}
        for name, adapter in self.adapters.items():
            status[name] = {
                "enabled": adapter.enabled,
                "last_evaluation": getattr(adapter, "last_evaluation", None),
                "evaluation_count": getattr(adapter, "evaluation_count", 0)
            }
        return status
