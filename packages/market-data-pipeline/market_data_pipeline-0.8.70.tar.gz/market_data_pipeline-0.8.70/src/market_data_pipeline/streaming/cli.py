"""
Streaming CLI for market_data_pipeline.

Provides commands for managing stream processing.
"""

import asyncio
import logging
import argparse
from typing import Dict, Any, List
from pathlib import Path
import yaml
import json

from .redis_bus import RedisStreamBus
from .producers import SyntheticTickProducer, IBKRTickProducer
from .consumers import MicroBatcher, InferenceConsumer
from .features import RollingFeatures, FeatureWindow
from .inference import InferenceEngine
from .inference.adapters import RulesAdapter, SklearnAdapter

logger = logging.getLogger(__name__)


class StreamingCLI:
    """CLI for streaming operations."""
    
    def __init__(self):
        self.bus = None
        self.producers = []
        self.consumers = []
        self.features = None
        self.inference_engine = None
    
    async def start_producer(self, config: Dict[str, Any], provider: str) -> None:
        """Start a producer."""
        if provider == "synthetic":
            producer = SyntheticTickProducer(
                bus=self.bus,
                symbols=config.get("symbols", ["SPY", "AAPL", "MSFT"]),
                tick_rate=config.get("tick_rate", 1.0),
                price_volatility=config.get("price_volatility", 0.02),
                seed=config.get("seed", 42)
            )
        elif provider == "ibkr":
            producer = IBKRTickProducer(
                bus=self.bus,
                symbols=config.get("symbols", ["SPY", "AAPL", "MSFT"]),
                host=config.get("host", "127.0.0.1"),
                port=config.get("port", 7497),
                client_id=config.get("client_id", 1)
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        self.producers.append(producer)
        await producer.start()
        logger.info(f"Started {provider} producer")
    
    async def start_micro_batcher(self, config: Dict[str, Any], store_client) -> None:
        """Start micro-batcher."""
        micro_batch_config = config.get("micro_batch", {})
        
        batcher = MicroBatcher(
            bus=self.bus,
            store_client=store_client,
            window_seconds=micro_batch_config.get("window_ms", 2000) // 1000,
            max_batch_size=micro_batch_config.get("max_batch_size", 5000),
            allow_late_ms=micro_batch_config.get("allow_late_ms", 500),
            flush_timeout_ms=micro_batch_config.get("flush_timeout_ms", 1000)
        )
        
        self.consumers.append(batcher)
        await batcher.run()
        logger.info("Started micro-batcher")
    
    async def start_inference(self, config: Dict[str, Any], store_client) -> None:
        """Start inference consumer."""
        # Create feature windows
        feature_config = config.get("features", {})
        windows = []
        for window_config in feature_config.get("windows", []):
            window = FeatureWindow(
                name=window_config["name"],
                horizon_seconds=self._parse_duration(window_config["horizon"])
            )
            windows.append(window)
        
        # Create rolling features
        self.features = RollingFeatures(windows)
        
        # Create inference adapters
        adapters = []
        inference_config = config.get("inference", {})
        
        # Rules adapter
        if inference_config.get("adapters", {}).get("rules", {}).get("enabled", True):
            rules_file = inference_config.get("adapters", {}).get("rules", {}).get("file")
            rules_adapter = RulesAdapter(rules_file=rules_file)
            adapters.append(rules_adapter)
        
        # Sklearn adapter
        sklearn_config = inference_config.get("adapters", {}).get("sklearn", {})
        if sklearn_config.get("enabled", False):
            model_path = sklearn_config.get("model_path")
            sklearn_adapter = SklearnAdapter(model_path=model_path)
            adapters.append(sklearn_adapter)
        
        # Create inference engine
        self.inference_engine = InferenceEngine(adapters)
        
        # Create inference consumer
        consumer = InferenceConsumer(
            bus=self.bus,
            features=self.features,
            inference_engine=self.inference_engine,
            signals_store_client=store_client
        )
        
        self.consumers.append(consumer)
        await consumer.run()
        logger.info("Started inference consumer")
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string to seconds."""
        if duration_str.endswith("s"):
            return int(duration_str[:-1])
        elif duration_str.endswith("m"):
            return int(duration_str[:-1]) * 60
        elif duration_str.endswith("h"):
            return int(duration_str[:-1]) * 3600
        else:
            return int(duration_str)
    
    async def tail_stream(self, topic: str, limit: int = 50) -> None:
        """Tail a stream."""
        try:
            count = 0
            while count < limit:
                messages = await self.bus.read(topic, "tail-consumer", "tail-1", count=10, block_ms=1000)
                
                for msg in messages:
                    print(f"[{msg.timestamp}] {msg.id}: {json.dumps(msg.payload, indent=2)}")
                    count += 1
                    
                    if count >= limit:
                        break
                        
        except KeyboardInterrupt:
            logger.info("Tail interrupted")
    
    async def replay_data(self, dataset: str, from_date: str, to_date: str) -> None:
        """Replay historical data into stream."""
        # This would integrate with the existing backfill system
        logger.info(f"Replaying {dataset} from {from_date} to {to_date}")
        # Implementation would depend on the specific dataset format
        pass
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        # Stop all producers
        for producer in self.producers:
            await producer.stop()
        
        # Stop all consumers
        for consumer in self.consumers:
            await consumer.stop()
        
        # Disconnect from bus
        if self.bus:
            await self.bus.disconnect()
        
        logger.info("Cleanup completed")


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Market Data Pipeline Streaming CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Produce command
    produce_parser = subparsers.add_parser("produce", help="Start a producer")
    produce_parser.add_argument("--config", required=True, help="Configuration file")
    produce_parser.add_argument("--provider", choices=["synthetic", "ibkr"], required=True, help="Provider to use")
    
    # Micro-batch command
    micro_batch_parser = subparsers.add_parser("micro-batch", help="Start micro-batcher")
    micro_batch_parser.add_argument("--config", required=True, help="Configuration file")
    
    # Inference command
    inference_parser = subparsers.add_parser("infer", help="Start inference")
    inference_parser.add_argument("--config", required=True, help="Configuration file")
    inference_parser.add_argument("--adapter", choices=["rules", "sklearn"], help="Adapter to use")
    
    # Tail command
    tail_parser = subparsers.add_parser("tail", help="Tail a stream")
    tail_parser.add_argument("--topic", default="mdp.events", help="Topic to tail")
    tail_parser.add_argument("--limit", type=int, default=50, help="Number of messages to show")
    
    # Replay command
    replay_parser = subparsers.add_parser("replay", help="Replay historical data")
    replay_parser.add_argument("--dataset", required=True, help="Dataset to replay")
    replay_parser.add_argument("--from", required=True, help="Start date")
    replay_parser.add_argument("--to", required=True, help="End date")
    
    args = parser.parse_args()
    
    # Load configuration
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    # Create CLI instance
    cli = StreamingCLI()
    
    try:
        # Connect to bus
        bus_config = config.get("bus", {})
        if bus_config.get("type") == "redis":
            redis_config = bus_config.get("redis", {})
            cli.bus = RedisStreamBus(
                uri=redis_config.get("uri", "redis://localhost:6379/0"),
                events_stream=redis_config.get("stream", "mdp.events"),
                signals_stream=redis_config.get("signals_stream", "mdp.signals")
            )
            await cli.bus.connect()
        
        # Execute command
        if args.command == "produce":
            await cli.start_producer(config, args.provider)
        elif args.command == "micro-batch":
            # This would need a store client
            logger.error("Store client not implemented in this example")
        elif args.command == "infer":
            # This would need a store client
            logger.error("Store client not implemented in this example")
        elif args.command == "tail":
            await cli.tail_stream(args.topic, args.limit)
        elif args.command == "replay":
            await cli.replay_data(args.dataset, getattr(args, 'from'), args.to)
        
        # Keep running for producers/consumers
        if args.command in ["produce", "micro-batch", "infer"]:
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutting down...")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        await cli.cleanup()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
