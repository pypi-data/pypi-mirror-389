"""
End-to-end integration tests for backpressure flow.

Tests the complete backpressure loop:
1. Store → FeedbackEvent (via market-data-core)
2. Pulse/EventBus → FeedbackConsumer
3. FeedbackHandler → RateController
4. RateCoordinator → Pipeline throttling

This verifies the full integration between:
- market-data-core (events, protocols, telemetry)
- market-data-pipeline (feedback, coordination, runtime)
- market-data-store (batch processing, backpressure signals)
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from market_data_core.protocols import FeedbackPublisher, RateController
from market_data_core.telemetry import BackpressureLevel, FeedbackEvent, RateAdjustment

from market_data_pipeline.orchestration.coordinator import RateCoordinator
from market_data_pipeline.orchestration.feedback import (
    FeedbackBus,
    FeedbackHandler,
    RateCoordinatorAdapter,
)
from market_data_pipeline.settings.feedback import PipelineFeedbackSettings


@pytest.mark.asyncio
@pytest.mark.integration
async def test_backpressure_feedback_loop():
    """
    Test complete backpressure feedback loop.
    
    Simulates:
    1. Store emits FeedbackEvent (queue at 80% capacity)
    2. FeedbackBus publishes to subscribers
    3. FeedbackHandler processes event
    4. RateCoordinator applies throttling
    
    This is a critical integration test verifying the whole
    backpressure system works end-to-end.
    """
    # Setup rate coordinator
    coordinator = RateCoordinator()
    coordinator.register_provider("test_provider", capacity=100, refill_rate=60)
    
    # Wrap in Core protocol adapter
    rate_adapter = RateCoordinatorAdapter(coordinator)
    
    # Setup feedback handler
    settings = PipelineFeedbackSettings(
        provider_name="test_provider",
        scale_soft=0.7,
        scale_hard=0.0
    )
    handler = FeedbackHandler(
        rate=rate_adapter,
        provider="test_provider",
        policy=settings.get_policy()
    )
    
    # Setup feedback bus
    bus = FeedbackBus()
    bus.subscribe(handler.handle)
    
    # Simulate store backpressure event
    event = FeedbackEvent(
        coordinator_id="store_coordinator_01",
        queue_size=800,  # 80% of capacity
        capacity=1000,
        level=BackpressureLevel.soft,
        source="store",
        ts=time.time()
    )
    
    # Publish event
    await bus.publish(event)
    
    # Give handler time to process
    await asyncio.sleep(0.1)
    
    # Verify rate was throttled
    scale_factor = coordinator._scale_factors.get("test_provider")
    assert scale_factor == 0.7, f"Expected scale=0.7, got {scale_factor}"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_backpressure_escalation():
    """
    Test backpressure level escalation: OK → SOFT → HARD.
    
    This verifies that the system correctly handles
    escalating backpressure signals.
    """
    coordinator = RateCoordinator()
    coordinator.register_provider("escalation_test", capacity=100, refill_rate=60)
    rate_adapter = RateCoordinatorAdapter(coordinator)
    
    settings = PipelineFeedbackSettings(
        provider_name="escalation_test",
        scale_soft=0.7,
        scale_hard=0.0
    )
    handler = FeedbackHandler(
        rate=rate_adapter,
        provider="escalation_test",
        policy=settings.get_policy()
    )
    
    bus = FeedbackBus()
    bus.subscribe(handler.handle)
    
    # 1. OK level (normal operation)
    event_ok = FeedbackEvent(
        coordinator_id="test",
        queue_size=500,  # 50% capacity
        capacity=1000,
        level=BackpressureLevel.ok,
        source="store",
        ts=time.time()
    )
    await bus.publish(event_ok)
    await asyncio.sleep(0.05)
    
    scale = coordinator._scale_factors.get("escalation_test")
    assert scale == 1.0, "OK level should set scale=1.0"
    
    # 2. SOFT level (moderate pressure)
    event_soft = FeedbackEvent(
        coordinator_id="test",
        queue_size=800,  # 80% capacity
        capacity=1000,
        level=BackpressureLevel.soft,
        source="store",
        ts=time.time()
    )
    await bus.publish(event_soft)
    await asyncio.sleep(0.05)
    
    scale = coordinator._scale_factors.get("escalation_test")
    assert scale == 0.7, "SOFT level should set scale=0.7"
    
    # 3. HARD level (severe pressure)
    event_hard = FeedbackEvent(
        coordinator_id="test",
        queue_size=950,  # 95% capacity
        capacity=1000,
        level=BackpressureLevel.hard,
        source="store",
        ts=time.time()
    )
    await bus.publish(event_hard)
    await asyncio.sleep(0.05)
    
    scale = coordinator._scale_factors.get("escalation_test")
    assert scale == 0.0, "HARD level should set scale=0.0 (stop)"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_backpressure_multiple_subscribers():
    """
    Test feedback bus with multiple subscribers.
    
    This verifies that feedback events are delivered to
    all subscribers (fan-out pattern).
    """
    events_received_1 = []
    events_received_2 = []
    
    async def subscriber_1(event: FeedbackEvent) -> None:
        events_received_1.append(event)
    
    async def subscriber_2(event: FeedbackEvent) -> None:
        events_received_2.append(event)
    
    bus = FeedbackBus()
    bus.subscribe(subscriber_1)
    bus.subscribe(subscriber_2)
    
    # Publish event
    event = FeedbackEvent(
        coordinator_id="test",
        queue_size=500,
        capacity=1000,
        level=BackpressureLevel.ok,
        source="store",
        ts=time.time()
    )
    await bus.publish(event)
    
    # Give subscribers time to process
    await asyncio.sleep(0.1)
    
    # Both subscribers should receive the event
    assert len(events_received_1) == 1
    assert len(events_received_2) == 1
    assert events_received_1[0] is event
    assert events_received_2[0] is event


@pytest.mark.asyncio
@pytest.mark.integration
async def test_rate_coordinator_adapter_protocol_conformance():
    """
    Test RateCoordinatorAdapter conforms to Core's RateController protocol.
    
    This is a critical integration test verifying that Pipeline's
    rate coordination correctly implements Core's protocol contract.
    """
    coordinator = RateCoordinator()
    coordinator.register_provider("protocol_test", capacity=100, refill_rate=60)
    adapter = RateCoordinatorAdapter(coordinator)
    
    # Verify protocol conformance
    assert isinstance(adapter, RateController)
    
    # Test apply() method
    adjustment = RateAdjustment(
        provider="protocol_test",
        scale=0.5,
        reason=BackpressureLevel.soft,
        ts=time.time()
    )
    
    result = await adapter.apply(adjustment)
    assert result is None, "apply() should return None per protocol"
    
    # Verify adjustment was applied
    scale = coordinator._scale_factors.get("protocol_test")
    assert scale == 0.5


@pytest.mark.asyncio
@pytest.mark.integration
async def test_feedback_bus_protocol_conformance():
    """
    Test FeedbackBus conforms to Core's FeedbackPublisher protocol.
    
    This verifies that Pipeline's feedback bus correctly implements
    Core's protocol contract for event publishing.
    """
    bus = FeedbackBus()
    
    # Verify protocol conformance
    assert isinstance(bus, FeedbackPublisher)
    
    # Track published events
    published_events = []
    
    async def subscriber(event: FeedbackEvent) -> None:
        published_events.append(event)
    
    bus.subscribe(subscriber)
    
    # Test publish() method
    event = FeedbackEvent(
        coordinator_id="test",
        queue_size=500,
        capacity=1000,
        level=BackpressureLevel.ok,
        source="store",
        ts=time.time()
    )
    
    result = await bus.publish(event)
    assert result is None, "publish() should return None per protocol"
    
    await asyncio.sleep(0.05)
    
    # Verify event was delivered
    assert len(published_events) == 1
    assert published_events[0] is event


@pytest.mark.asyncio
@pytest.mark.integration
async def test_backpressure_with_custom_policy():
    """
    Test backpressure with custom scaling policy.
    
    This verifies that users can configure custom scale factors
    for different backpressure levels.
    """
    coordinator = RateCoordinator()
    coordinator.register_provider("custom_policy", capacity=100, refill_rate=60)
    rate_adapter = RateCoordinatorAdapter(coordinator)
    
    # Custom policy: be more aggressive
    settings = PipelineFeedbackSettings(
        provider_name="custom_policy",
        scale_soft=0.5,  # More aggressive than default 0.7
        scale_hard=0.1   # Don't stop completely
    )
    handler = FeedbackHandler(
        rate=rate_adapter,
        provider="custom_policy",
        policy=settings.get_policy()
    )
    
    bus = FeedbackBus()
    bus.subscribe(handler.handle)
    
    # Test SOFT with custom scale
    event_soft = FeedbackEvent(
        coordinator_id="test",
        queue_size=800,
        capacity=1000,
        level=BackpressureLevel.soft,
        source="store",
        ts=time.time()
    )
    await bus.publish(event_soft)
    await asyncio.sleep(0.05)
    
    scale = coordinator._scale_factors.get("custom_policy")
    assert scale == 0.5, "Should use custom scale_soft=0.5"
    
    # Test HARD with custom scale
    event_hard = FeedbackEvent(
        coordinator_id="test",
        queue_size=950,
        capacity=1000,
        level=BackpressureLevel.hard,
        source="store",
        ts=time.time()
    )
    await bus.publish(event_hard)
    await asyncio.sleep(0.05)
    
    scale = coordinator._scale_factors.get("custom_policy")
    assert scale == 0.1, "Should use custom scale_hard=0.1"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_backpressure_recovery():
    """
    Test backpressure recovery when pressure subsides.
    
    This verifies that the system recovers to normal operation
    when backpressure signals return to OK.
    """
    coordinator = RateCoordinator()
    coordinator.register_provider("recovery_test", capacity=100, refill_rate=60)
    rate_adapter = RateCoordinatorAdapter(coordinator)
    
    settings = PipelineFeedbackSettings(
        provider_name="recovery_test",
        scale_soft=0.7,
        scale_hard=0.0
    )
    handler = FeedbackHandler(
        rate=rate_adapter,
        provider="recovery_test",
        policy=settings.get_policy()
    )
    
    bus = FeedbackBus()
    bus.subscribe(handler.handle)
    
    # 1. Start with HIGH pressure
    event_hard = FeedbackEvent(
        coordinator_id="test",
        queue_size=950,
        capacity=1000,
        level=BackpressureLevel.hard,
        source="store",
        ts=time.time()
    )
    await bus.publish(event_hard)
    await asyncio.sleep(0.05)
    
    scale = coordinator._scale_factors.get("recovery_test")
    assert scale == 0.0, "Should be throttled"
    
    # 2. Recover to normal
    event_ok = FeedbackEvent(
        coordinator_id="test",
        queue_size=300,  # Back to low utilization
        capacity=1000,
        level=BackpressureLevel.ok,
        source="store",
        ts=time.time()
    )
    await bus.publish(event_ok)
    await asyncio.sleep(0.05)
    
    scale = coordinator._scale_factors.get("recovery_test")
    assert scale == 1.0, "Should recover to full speed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])


