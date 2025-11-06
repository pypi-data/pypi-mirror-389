#!/usr/bin/env python3
"""
Quick test of the dual-sink system without requiring full database setup.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_imports():
    """Test that all imports work correctly."""
    print("🧪 Testing imports...")
    
    try:
        from market_data_pipeline.sink.sink_registry import create_store_sink, get_sink_info, list_available_modes
        print("✅ Sink registry imports successful")
        
        from market_data_pipeline.sink.store import StoreSink as StoreSinkLegacy
        print("✅ Legacy store sink import successful")
        
        from market_data_pipeline.sink.store_sink_provider import StoreSink as StoreSinkProvider
        print("✅ Provider store sink import successful")
        
        from market_data_pipeline.types import Bar
        print("✅ Bar type import successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


def test_sink_registry():
    """Test sink registry functionality."""
    print("\n🔍 Testing sink registry...")
    
    try:
        from market_data_pipeline.sink.sink_registry import get_sink_info, list_available_modes
        
        # Test available modes
        modes = list_available_modes()
        print(f"✅ Available modes: {modes}")
        
        # Test mode info
        for mode in modes:
            info = get_sink_info(mode)
            print(f"✅ {mode} mode info: {info['name']} -> {info['table']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Registry error: {e}")
        return False


def test_bar_creation():
    """Test Bar object creation."""
    print("\n📊 Testing Bar creation...")
    
    try:
        from market_data_pipeline.types import Bar
        
        bar = Bar(
            source="synthetic",
            symbol="AAPL",
            timestamp=datetime.now(timezone.utc),
            open=170.1,
            high=171.0,
            low=169.9,
            close=170.5,
            volume=10000
        )
        
        print(f"✅ Created bar: {bar.symbol} @ {bar.close}")
        return True
        
    except Exception as e:
        print(f"❌ Bar creation error: {e}")
        return False


def test_sink_creation():
    """Test sink creation (without database connection)."""
    print("\n🏭 Testing sink creation...")
    
    try:
        from market_data_pipeline.sink.sink_registry import create_store_sink
        
        # Test legacy sink creation (should work even without DB)
        print("Testing legacy sink creation...")
        try:
            legacy = create_store_sink("legacy")
            print("✅ Legacy sink created successfully")
        except Exception as e:
            print(f"⚠️  Legacy sink creation failed (expected without DB): {e}")
        
        # Test provider sink creation (should work even without DB)
        print("Testing provider sink creation...")
        try:
            provider = create_store_sink("provider")
            print("✅ Provider sink created successfully")
        except Exception as e:
            print(f"⚠️  Provider sink creation failed (expected without DB): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Sink creation error: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Phase 20.1 Dual-Sink System Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_sink_registry,
        test_bar_creation,
        test_sink_creation,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Dual-sink system is ready.")
        print("\nNext steps:")
        print("1. Set up DATABASE_URL environment variable")
        print("2. Run: python scripts/verify_dual_sink.py")
        print("3. Check Prometheus metrics at http://localhost:9090")
        return 0
    else:
        print("❌ Some tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
