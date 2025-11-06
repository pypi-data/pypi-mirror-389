"""
Stream bus abstraction for market_data_pipeline.

Defines the interface for stream processing backends (Redis, Kafka).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import asyncio
import json
from datetime import datetime


@dataclass
class Message:
    """Represents a message from the stream bus."""
    id: str
    topic: str
    payload: Dict[str, Any]
    timestamp: datetime
    headers: Optional[Dict[str, str]] = None


class StreamBus(ABC):
    """Abstract base class for stream bus implementations."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to the stream bus."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the stream bus."""
        pass
    
    @abstractmethod
    async def publish(self, topic: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> str:
        """
        Publish a message to a topic.
        
        Args:
            topic: Topic/stream name
            payload: Message payload
            headers: Optional message headers
            
        Returns:
            Message ID
        """
        pass
    
    @abstractmethod
    async def read(
        self, 
        topic: str, 
        group: str, 
        consumer: str, 
        count: int = 100, 
        block_ms: int = 1000
    ) -> List[Message]:
        """
        Read messages from a topic using consumer groups.
        
        Args:
            topic: Topic/stream name
            group: Consumer group name
            consumer: Consumer name
            count: Maximum number of messages to read
            block_ms: Blocking timeout in milliseconds
            
        Returns:
            List of messages
        """
        pass
    
    @abstractmethod
    async def ack(self, topic: str, group: str, message_id: str) -> None:
        """
        Acknowledge a message.
        
        Args:
            topic: Topic/stream name
            group: Consumer group name
            message_id: Message ID to acknowledge
        """
        pass
    
    @abstractmethod
    async def create_consumer_group(self, topic: str, group: str) -> None:
        """
        Create a consumer group for a topic.
        
        Args:
            topic: Topic/stream name
            group: Consumer group name
        """
        pass


class StreamEvent:
    """Represents a market data event in the stream."""
    
    def __init__(
        self,
        provider: str,
        symbol: str,
        kind: str,  # tick | bar
        src_ts: datetime,
        ingest_ts: datetime,
        data: Dict[str, Any],
        interval: Optional[str] = None,
        seq: Optional[int] = None
    ):
        self.ver = 1
        self.provider = provider
        self.symbol = symbol
        self.kind = kind
        self.interval = interval
        self.src_ts = src_ts.isoformat() + "Z"
        self.ingest_ts = ingest_ts.isoformat() + "Z"
        self.seq = seq
        self.data = data
        
        # Generate deterministic event ID
        self.event_id = f"{provider}|{symbol}|{self.src_ts}|{seq or 0}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "ver": self.ver,
            "provider": self.provider,
            "symbol": self.symbol,
            "kind": self.kind,
            "src_ts": self.src_ts,
            "ingest_ts": self.ingest_ts,
            "event_id": self.event_id,
            **self.data
        }
        
        if self.interval:
            result["interval"] = self.interval
        if self.seq is not None:
            result["seq"] = self.seq
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamEvent":
        """Create from dictionary."""
        return cls(
            provider=data["provider"],
            symbol=data["symbol"],
            kind=data["kind"],
            src_ts=datetime.fromisoformat(data["src_ts"].replace("Z", "+00:00")),
            ingest_ts=datetime.fromisoformat(data["ingest_ts"].replace("Z", "+00:00")),
            data={k: v for k, v in data.items() if k not in [
                "ver", "provider", "symbol", "kind", "src_ts", "ingest_ts", 
                "event_id", "interval", "seq"
            ]},
            interval=data.get("interval"),
            seq=data.get("seq")
        )


class SignalEvent:
    """Represents a signal event in the stream."""
    
    def __init__(
        self,
        provider: str,
        symbol: str,
        ts: datetime,
        name: str,
        value: float,
        score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.ver = 1
        self.provider = provider
        self.symbol = symbol
        self.ts = ts.isoformat() + "Z"
        self.name = name
        self.value = value
        self.score = score
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "ver": self.ver,
            "provider": self.provider,
            "symbol": self.symbol,
            "ts": self.ts,
            "name": self.name,
            "value": self.value,
            "metadata": self.metadata
        }
        
        if self.score is not None:
            result["score"] = self.score
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SignalEvent":
        """Create from dictionary."""
        return cls(
            provider=data["provider"],
            symbol=data["symbol"],
            ts=datetime.fromisoformat(data["ts"].replace("Z", "+00:00")),
            name=data["name"],
            value=data["value"],
            score=data.get("score"),
            metadata=data.get("metadata", {})
        )
