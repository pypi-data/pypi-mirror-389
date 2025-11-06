"""Example demonstrating UnifiedRuntime status() and health() methods.

This example shows how to check the status and health of a UnifiedRuntime instance.
These methods were added to fix Issue #15 where calling runtime.status() would fail.

Usage:
    python examples/runtime_status_example.py
"""

import asyncio
import json

from market_data_pipeline.runtime.unified_runtime import UnifiedRuntime
from market_data_pipeline.settings.runtime_unified import (
    RuntimeModeEnum,
    UnifiedRuntimeSettings,
)


async def main():
    """Demonstrate status and health methods."""
    print("=" * 60)
    print("UnifiedRuntime Status and Health Example")
    print("=" * 60)
    
    # Create a simple DAG runtime configuration with a basic node
    settings = UnifiedRuntimeSettings(
        mode=RuntimeModeEnum.dag,
        dag={
            "graph": {
                "nodes": [
                    {
                        "id": "demo_node",
                        "operator": "identity",
                        "config": {}
                    }
                ],
                "edges": []
            },
            "name": "status-demo"
        }
    )
    
    runtime = UnifiedRuntime(settings)
    
    # Check status before starting
    print("\n1. Status BEFORE starting runtime:")
    print("-" * 60)
    status = await runtime.status()
    print(json.dumps(status, indent=2))
    
    # Check health before starting
    print("\n2. Health BEFORE starting runtime:")
    print("-" * 60)
    health = await runtime.health()
    print(json.dumps(health, indent=2))
    
    # The status() and health() methods work even without starting
    # They return appropriate information based on the current state
    print("\n✓ status() and health() methods work correctly!")
    print("  - status() shows: mode, started flag, and state")
    print("  - health() shows: overall health status with components")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print("\nNote: This example demonstrates the new status() and health()")
    print("      methods that were added to fix Issue #15.")


if __name__ == "__main__":
    asyncio.run(main())

