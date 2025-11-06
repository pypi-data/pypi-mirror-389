"""
Base inference adapter.

Defines the interface for inference adapters.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from datetime import datetime

from ...bus import SignalEvent


class InferenceAdapter(ABC):
    """Abstract base class for inference adapters."""
    
    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
        self.last_evaluation = None
        self.evaluation_count = 0
    
    @abstractmethod
    async def evaluate(self, symbol: str, features: Dict[str, Any]) -> List[SignalEvent]:
        """
        Evaluate features and generate signals.
        
        Args:
            symbol: Symbol name
            features: Feature dictionary
            
        Returns:
            List of generated signals
        """
        pass
    
    async def start(self) -> None:
        """Start the adapter."""
        pass
    
    async def stop(self) -> None:
        """Stop the adapter."""
        pass
    
    def _create_signal(
        self,
        symbol: str,
        name: str,
        value: float,
        score: float = None,
        metadata: Dict[str, Any] = None
    ) -> SignalEvent:
        """Create a signal event."""
        return SignalEvent(
            provider="inference",
            symbol=symbol,
            ts=datetime.utcnow(),
            name=name,
            value=value,
            score=score,
            metadata=metadata or {}
        )
