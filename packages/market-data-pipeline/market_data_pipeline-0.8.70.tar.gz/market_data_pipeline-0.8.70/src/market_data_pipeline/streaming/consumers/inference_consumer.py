"""
Inference consumer for processing signals.

Consumes features and generates signals using the inference engine.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..bus import StreamBus, SignalEvent
from ..features import RollingFeatures
from ..inference import InferenceEngine
from ..telemetry import (
    record_inference_eval_duration,
    record_signals_emitted
)

logger = logging.getLogger(__name__)


class InferenceConsumer:
    """Consumer that processes features and generates signals."""
    
    def __init__(
        self,
        bus: StreamBus,
        features: RollingFeatures,
        inference_engine: InferenceEngine,
        signals_store_client,
        consumer_group: str = "inference-consumer",
        consumer_name: str = "inference-1"
    ):
        self.bus = bus
        self.features = features
        self.inference_engine = inference_engine
        self.signals_store_client = signals_store_client
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self._running = False
    
    async def process_features(self, symbol: str, features: Dict[str, Any]) -> None:
        """Process features and generate signals."""
        try:
            # Generate signals using inference engine
            start_time = datetime.utcnow()
            signals = await self.inference_engine.evaluate(symbol, features)
            eval_duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Record metrics
            record_inference_eval_duration(eval_duration)
            record_signals_emitted(len(signals))
            
            if signals:
                # Publish signals to stream
                for signal in signals:
                    await self.bus.publish_signal(signal)
                
                # Store signals
                await self.signals_store_client.write_signals(signals)
                
                logger.debug(f"Generated {len(signals)} signals for {symbol}")
            
        except Exception as e:
            logger.error(f"Error processing features for {symbol}: {e}")
            raise
    
    async def run(self) -> None:
        """Run the inference consumer."""
        self._running = True
        logger.info("Started inference consumer")
        
        try:
            # Start inference engine
            await self.inference_engine.start()
            
            while self._running:
                try:
                    # Process features for all active symbols
                    for symbol in self.features.get_symbols():
                        # Get current features
                        current_features = self.features.get_current_features(symbol)
                        
                        if current_features:
                            # Process features
                            await self.process_features(symbol, current_features)
                    
                    # Brief pause to avoid busy waiting
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error in inference consumer loop: {e}")
                    await asyncio.sleep(1)
                    
        except asyncio.CancelledError:
            logger.info("Inference consumer cancelled")
        finally:
            # Stop inference engine
            await self.inference_engine.stop()
            self._running = False
            logger.info("Stopped inference consumer")
    
    async def stop(self) -> None:
        """Stop the inference consumer."""
        self._running = False
