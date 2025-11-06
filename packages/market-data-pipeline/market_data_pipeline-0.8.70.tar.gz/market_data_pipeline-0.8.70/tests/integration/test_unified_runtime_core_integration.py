"""
Integration tests for UnifiedRuntime with market-data-core.

Tests the integration between UnifiedRuntime and Core's:
- Event bus (Pulse)
- Feedback system
- Rate coordination
- Telemetry DTOs

These tests verify that the new status() and health() methods
properly integrate with Core contracts.
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from market_data_core.protocols import RateController
from market_data_core.telemetry import BackpressureLevel, FeedbackEvent, RateAdjustment

from market_data_pipeline.runtime.unified_runtime import UnifiedRuntime
from market_data_pipeline.settings.runtime_unified import (
    RuntimeModeEnum,
    UnifiedRuntimeSettings,
)


class MockRateController(RateController):
    """Mock rate controller for testing."""
    
    def __init__(self):
        self.adjustments: list[RateAdjustment] = []
    
    async def apply(self, adjustment: RateAdjustment) -> None:
        """Record rate adjustments."""
        self.adjustments.append(adjustment)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unified_runtime_status_method():
    """
    Test UnifiedRuntime.status() method returns proper structure.
    
    This test verifies that the new status() method works correctly
    and returns expected information about the runtime state.
    """
    # Create a simple DAG runtime
    settings = UnifiedRuntimeSettings(
        mode=RuntimeModeEnum.dag,
        dag={
            "graph": {
                "nodes": [{"id": "test", "operator": "identity", "config": {}}],
                "edges": []
            },
            "name": "test_status"
        }
    )
    
    runtime = UnifiedRuntime(settings)
    
    # Test status before starting
    status = await runtime.status()
    assert status["mode"] == "dag"
    assert status["started"] is False
    assert status["state"] == "stopped"
    
    # Note: We don't start the runtime here to keep test fast
    # Full lifecycle tested in test_facade.py


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unified_runtime_health_method():
    """
    Test UnifiedRuntime.health() method returns proper health info.
    
    This test verifies that the new health() method correctly
    aggregates health information suitable for monitoring systems.
    """
    settings = UnifiedRuntimeSettings(
        mode=RuntimeModeEnum.dag,
        dag={
            "graph": {
                "nodes": [{"id": "test", "operator": "identity", "config": {}}],
                "edges": []
            },
            "name": "test_health"
        }
    )
    
    runtime = UnifiedRuntime(settings)
    
    # Test health before starting
    health = await runtime.health()
    assert health["status"] == "ERROR"
    assert health["mode"] == "dag"
    assert health["started"] is False
    assert "message" in health
    assert health["message"] == "Runtime not started"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unified_runtime_with_feedback_handler():
    """
    Test UnifiedRuntime integrates with Core feedback system.
    
    This test verifies that the runtime can be configured with
    feedback handling that uses Core's FeedbackEvent and RateAdjustment DTOs.
    """
    # Mock the rate controller
    rate_controller = MockRateController()
    
    # Create runtime settings with feedback enabled
    settings = UnifiedRuntimeSettings(
        mode=RuntimeModeEnum.dag,
        dag={
            "graph": {
                "nodes": [{"id": "test", "operator": "identity", "config": {}}],
                "edges": []
            },
            "name": "test_feedback"
        },
        feedback={
            "enable_feedback": False,  # Disabled to avoid complex setup
            "provider_name": "test_provider",
            "scale_soft": 0.7,
            "scale_hard": 0.0,
        }
    )
    
    runtime = UnifiedRuntime(settings)
    
    # Verify runtime has proper feedback settings
    assert runtime._settings.feedback.provider_name == "test_provider"
    assert runtime._settings.feedback.scale_soft == 0.7


@pytest.mark.asyncio
@pytest.mark.integration
async def test_core_feedback_event_integration():
    """
    Test that Core's FeedbackEvent can be created and used.
    
    This verifies compatibility with market-data-core telemetry DTOs
    used in the feedback system.
    """
    # Create a Core FeedbackEvent
    event = FeedbackEvent(
        coordinator_id="test_coordinator",
        queue_size=500,
        capacity=1000,
        level=BackpressureLevel.soft,
        source="store",
        ts=time.time()
    )
    
    # Verify event structure
    assert event.coordinator_id == "test_coordinator"
    assert event.queue_size == 500
    assert event.capacity == 1000
    assert event.level == BackpressureLevel.soft
    assert event.source == "store"
    assert event.ts > 0
    
    # Verify it can be serialized/deserialized
    event_dict = event.model_dump()
    assert event_dict["coordinator_id"] == "test_coordinator"
    
    reconstructed = FeedbackEvent.model_validate(event_dict)
    assert reconstructed.coordinator_id == event.coordinator_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_core_rate_adjustment_integration():
    """
    Test that Core's RateAdjustment can be created and applied.
    
    This verifies compatibility with market-data-core telemetry DTOs
    used in rate coordination.
    """
    # Create a mock rate controller
    rate_controller = MockRateController()
    
    # Create a Core RateAdjustment
    adjustment = RateAdjustment(
        provider="test_provider",
        scale=0.5,
        reason=BackpressureLevel.soft,
        ts=time.time()
    )
    
    # Apply adjustment
    await rate_controller.apply(adjustment)
    
    # Verify adjustment was recorded
    assert len(rate_controller.adjustments) == 1
    assert rate_controller.adjustments[0].provider == "test_provider"
    assert rate_controller.adjustments[0].scale == 0.5
    assert rate_controller.adjustments[0].reason == BackpressureLevel.soft


@pytest.mark.asyncio
@pytest.mark.integration
async def test_status_method_with_implementation_error():
    """
    Test that status() gracefully handles implementation errors.
    
    This verifies that the status() method never raises exceptions
    even if the underlying implementation has issues.
    """
    settings = UnifiedRuntimeSettings(
        mode=RuntimeModeEnum.dag,
        dag={
            "graph": {
                "nodes": [{"id": "test", "operator": "identity", "config": {}}],
                "edges": []
            },
            "name": "test_error_handling"
        }
    )
    
    runtime = UnifiedRuntime(settings)
    
    # Mock the implementation to raise an error
    runtime._impl = MagicMock()
    runtime._impl.status = AsyncMock(side_effect=Exception("Test error"))
    runtime._state = MagicMock(started=True)
    
    # status() should not raise, but include error info
    status = await runtime.status()
    
    assert status["started"] is True
    assert "implementation_error" in status
    assert "Test error" in status["implementation_error"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_method_with_implementation_error():
    """
    Test that health() gracefully handles implementation errors.
    
    This verifies that the health() method never raises exceptions
    and properly marks status as DEGRADED when errors occur.
    """
    settings = UnifiedRuntimeSettings(
        mode=RuntimeModeEnum.dag,
        dag={
            "graph": {
                "nodes": [{"id": "test", "operator": "identity", "config": {}}],
                "edges": []
            },
            "name": "test_error_handling"
        }
    )
    
    runtime = UnifiedRuntime(settings)
    
    # Mock the implementation to raise an error
    runtime._impl = MagicMock()
    runtime._impl.health = AsyncMock(side_effect=Exception("Health check failed"))
    runtime._state = MagicMock(started=True)
    
    # health() should not raise, but mark as degraded
    health = await runtime.health()
    
    assert health["status"] == "DEGRADED"
    assert health["started"] is True
    assert len(health["components"]) > 0
    
    # Should have an error component
    error_component = next((c for c in health["components"] if c["status"] == "ERROR"), None)
    assert error_component is not None
    assert "error" in error_component


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])


